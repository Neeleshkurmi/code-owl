from app.core.config import settings

from app.services.review_job_service import ReviewJobService
from app.services.vercel_review_job_service import (
    VercelReviewJobService,
)


def get_review_job_service():

    if settings.review_queue_backend == "vercel":
        return VercelReviewJobService()

    return ReviewJobService()