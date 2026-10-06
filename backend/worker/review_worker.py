import asyncio
import json

import redis.exceptions

from app.db.database import AsyncSessionLocal
from app.services.review_job_service import ReviewJobService

from worker.review_processor import process_review_run


review_job_service = ReviewJobService()


async def worker():

    print("Development review worker started")

    while True:

        try:

            raw_job = await review_job_service.claim()

            if raw_job is None:
                continue

            job = json.loads(raw_job)

            review_run_id = job["review_run_id"]

            print(
                f"Processing ReviewRun {review_run_id}"
            )

            try:

                async with AsyncSessionLocal() as db:

                    await process_review_run(
                        db=db,
                        review_run_id=review_run_id,
                    )

            except Exception as error:

                print(
                    f"ReviewRun {review_run_id} failed: "
                    f"{error}"
                )

                # Do NOT acknowledge a failed job.
                # The job remains unacknowledged.
                continue

            await review_job_service.acknowledge(
                raw_job,
            )

            print(
                f"ReviewRun {review_run_id} acknowledged"
            )

        except redis.exceptions.RedisError as error:

            print(
                f"Redis error: {error}"
            )

            await asyncio.sleep(2)

        except Exception as error:

            print(
                f"Unexpected worker error: {error}"
            )

            await asyncio.sleep(2)


async def main():

    await worker()


if __name__ == "__main__":
    asyncio.run(main())