import sqlite3
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.optimizer.preprocessing import (
    build_historical_parameters,
)

from app.optimizer.engine import (
    solve_schedule,
)


router = APIRouter(
    prefix="/api",
    tags=["optimizer"],
)


# =========================================================
# DATABASE
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "dummy_data.db"
)


def load_historical_records():
    """
    Loads historical ticket-sale records from SQLite.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    try:
        cursor = connection.execute(
            """
            SELECT
                id,
                title_tag,
                venue_tag,
                play_day,
                curtain_time,
                account_tag,
                passes_bought
            FROM records
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()


# =========================================================
# REQUEST MODELS
# =========================================================

class RepertoireEntry(BaseModel):
    title: str

    required_blocks: int = Field(
        ge=1,
        le=2,
    )


class OptimizationRequest(BaseModel):
    repertoire: list[RepertoireEntry]

    room_amount: int = Field(
        ge=1,
        le=8,
    )

    day_weights: dict[str, float]

    time_weights: dict[str, float]


# =========================================================
# OPTIMIZATION ENDPOINT
# =========================================================

@router.post("/optimize")
def optimize_schedule(
    request: OptimizationRequest
):
    """
    Complete optimization pipeline:

        UI data
            ↓
        historical DB data
            ↓
        preprocessing
            ↓
        CP-SAT
            ↓
        schedule
    """

    historical_records = (
        load_historical_records()
    )

    repertoire = [
        movie.model_dump()
        for movie in request.repertoire
    ]

    historical_parameters = (
        build_historical_parameters(
            records=historical_records,
            time_weights=request.time_weights,
            day_weights=request.day_weights,
        )
    )

    result = solve_schedule(
        repertoire=repertoire,
        room_amount=request.room_amount,
        day_weights=request.day_weights,
        time_weights=request.time_weights,
        historical_parameters=historical_parameters,
    )

    return result