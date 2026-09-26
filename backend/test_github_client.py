import asyncio

from app.core.github_client import GitHubClient


async def main() :
    client = GitHubClient()

    diff = await client.get_pull_request_diff(
        owner = "neeleshkurmi",
        repo="Leet-Code-grind",
        pull_request_number=1,
    )

    print(diff)


if __name__ == "__main__" : 
    asyncio.run(main())