from fastapi import APIRouter

router = APIRouter(
    prefix="/api/records",
    tags=["records"]
)

@router.get("")
def get_records(
    offset: int = 0,
    limit: int = 50
):
    return []