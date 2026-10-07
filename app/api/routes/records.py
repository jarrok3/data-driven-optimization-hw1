import sqlite3
from pathlib import Path

from fastapi import APIRouter


router = APIRouter(
    prefix="/api/records",
    tags=["records"]
)


DATABASE_PATH = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
    .parent
    / "data"
    / "dummy_data.db"
)


@router.get("")
def get_records(
    offset: int = 0,
    limit: int = 50
):
    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    cursor = connection.execute("""
        SELECT
            id,
            title_tag,
            venue_tag,
            play_day,
            curtain_time,
            account_tag,
            passes_bought
        FROM records
        ORDER BY id
        LIMIT ?
        OFFSET ?
    """, (
        limit,
        offset
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]