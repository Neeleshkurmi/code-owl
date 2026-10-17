import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.models.github_installation import GitHubInstallation
from app.models.oauth_login_code import OAuthLoginCode
from app.models.user import User

import logging


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

bearer_scheme = HTTPBearer(auto_error=False)

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "code-owl"
JWT_AUDIENCE = "code-owl-dashboard"
ACCESS_TOKEN_MINUTES = 30
LOGIN_CODE_SECONDS = 120


class ExchangeCodeRequest(BaseModel):
    code: str


def _frontend_url() -> str:
    if settings.debug:
        return settings.frontend_dev_url.rstrip("/")
    return settings.frontend_prod_url.rstrip("/")


def _make_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


@router.get("/github/login")
async def github_login():
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.github_oauth_app_client_id,
        "redirect_uri": settings.github_oauth_redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }

    response = RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{urlencode(params)}",
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        key="github_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/api/v1/auth/github",
    )
    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    response: Response,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    frontend_url = _frontend_url()

    if error:
        return RedirectResponse(
            f"{frontend_url}/auth/callback?error=github_authorization_denied",
            status_code=status.HTTP_302_FOUND,
        )

    expected_state = request.cookies.get("github_oauth_state")
    if not state or not expected_state or not secrets.compare_digest(
        state, expected_state
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state. Restart GitHub login.",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code.",
        )

    if not settings.github_oauth_app_client_id or not settings.github_oauth_app_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth is not configured.",
        )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": settings.github_oauth_app_client_id,
                    "client_secret": settings.github_oauth_app_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_oauth_redirect_uri,
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()

            github_access_token = token_data.get("access_token")
            if not github_access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="GitHub did not return an access token.",
                )

            github_headers = {
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            profile_response = await client.get(
                "https://api.github.com/user",
                headers=github_headers,
            )
            profile_response.raise_for_status()
            profile = profile_response.json()

            email = profile.get("email")
            if not email:
                emails_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers=github_headers,
                )
                if emails_response.is_success:
                    emails = emails_response.json()
                    email = next(
                        (
                            item["email"]
                            for item in emails
                            if item.get("primary") and item.get("verified")
                        ),
                        None,
                    )

                installations = []

                installations_response = await client.get(
                    f"{settings.github_api_url}/user/installations?per_page=100",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )

                if installations_response.is_success:
                    installations = installations_response.json().get("installations", [])
                else:
                    logger.warning(
                        "Could not fetch GitHub App installations: status=%s response=%s",
                        installations_response.status_code,
                        installations_response.text,
                    )


    except HTTPException:
        raise
    except httpx.HTTPError:
        logger.exception("GitHub OAuth callback failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to complete GitHub authorization.",
        ) from None

    github_user_id = profile.get("id")
    github_login = profile.get("login")

    if not isinstance(github_user_id, int) or not github_login:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned an invalid user profile.",
        )

    result = await db.execute(
        select(User).where(User.github_user_id == github_user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            github_user_id=github_user_id,
            github_login=github_login,
            name=profile.get("name"),
            email=email,
            avatar_url=profile.get("avatar_url"),
        )
        db.add(user)
        await db.flush()
    else:
        user.github_login = github_login
        user.name = profile.get("name")
        user.email = email
        user.avatar_url = profile.get("avatar_url")

    # Associate only installations GitHub confirms this user can access.
    allowed_installation_ids = {
        item.get("id")
        for item in installation_items
        if isinstance(item.get("id"), int)
    }

    if allowed_installation_ids:
        result = await db.execute(
            select(GitHubInstallation).where(
                GitHubInstallation.github_installation_id.in_(
                    allowed_installation_ids
                ),
                GitHubInstallation.is_active.is_(True),
            )
        )
        known_installations = result.scalars().all()
        existing_ids = {item.id for item in user.installations}
        for installation in known_installations:
            if installation.id not in existing_ids:
                user.installations.append(installation)

    raw_login_code = secrets.token_urlsafe(32)
    login_code = OAuthLoginCode(
        code_hash=_hash_code(raw_login_code),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(seconds=LOGIN_CODE_SECONDS),
    )
    db.add(login_code)
    await db.commit()

    redirect = RedirectResponse(
        url=f"{frontend_url}/auth/callback?{urlencode({'code': raw_login_code})}",
        status_code=status.HTTP_302_FOUND,
    )
    redirect.delete_cookie(
        key="github_oauth_state",
        path="/api/v1/auth/github",
    )
    return redirect


@router.post("/token")
async def exchange_login_code(
    payload: ExchangeCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    code_hash = _hash_code(payload.code)

    result = await db.execute(
        select(OAuthLoginCode)
        .where(
            OAuthLoginCode.code_hash == code_hash,
            OAuthLoginCode.used_at.is_(None),
            OAuthLoginCode.expires_at > datetime.utcnow(),
        )
        .with_for_update()
    )
    login_code = result.scalar_one_or_none()

    if login_code is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or already used login code.",
        )

    result = await db.execute(
        select(User).where(User.id == login_code.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    login_code.used_at = datetime.utcnow()
    await db.commit()

    return {
        "access_token": _make_access_token(user),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_MINUTES * 60,
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError("Wrong token type")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    return user


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "github_user_id": current_user.github_user_id,
        "github_login": current_user.github_login,
        "name": current_user.name,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
    }
