import os
import uuid

from app.models.schemas import PitchReviewResponse

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reviews")


def save_review(review: PitchReviewResponse) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{uuid.uuid4()}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(review.model_dump_json(indent=2))


def list_recent(n: int = 10) -> list[PitchReviewResponse]:
    if not os.path.isdir(DATA_DIR):
        return []
    files = sorted(
        (os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".json")),
        key=os.path.getmtime,
        reverse=True,
    )[:n]
    reviews = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            reviews.append(PitchReviewResponse.model_validate_json(f.read()))
    return reviews
