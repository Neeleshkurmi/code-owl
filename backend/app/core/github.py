import hashlib
import hmac

from app.core.config import settings


def verify_github_signature(
        payload : bytes, 
        signature : str | None,
) -> bool :

    if signature is None :
        return False

    expected_signature = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )