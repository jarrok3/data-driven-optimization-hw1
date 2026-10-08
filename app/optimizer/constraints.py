from ortools.sat.python import cp_model

from app.optimizer.constants import (
    MIN_ROOM_AMOUNT,
    MAX_ROOM_AMOUNT,
)


# =========================================================
# INPUT VALIDATION
# =========================================================

def validate_repertoire(repertoire):
    """
    Validates repertoire input before the solver is started.

    Every repertoire entry must contain:
        title: non-empty string
        required_blocks: 1 or 2
    """

    if not repertoire:
        raise ValueError(
            "Repertoire cannot be empty."
        )

    for movie in repertoire:

        title = movie.get("title")
        required_blocks = movie.get("required_blocks")

        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                "Every repertoire entry must contain "
                "a non-empty title."
            )

        if required_blocks not in (1, 2):
            raise ValueError(
                f"Movie '{title}' has invalid "
                f"required_blocks={required_blocks}. "
                "Allowed values are 1 or 2."
            )


def validate_room_amount(room_amount):
    """
    Validates number of available screening rooms.
    """

    if not (
        MIN_ROOM_AMOUNT
        <= room_amount
        <= MAX_ROOM_AMOUNT
    ):
        raise ValueError(
            f"room_amount must be between "
            f"{MIN_ROOM_AMOUNT} and {MAX_ROOM_AMOUNT}."
        )


def validate_optimizer_input(
    repertoire,
    room_amount,
):
    """
    Main input validation entry point.
    """

    validate_repertoire(repertoire)
    validate_room_amount(room_amount)


# =========================================================
# SOLVER CONSTRAINTS
# =========================================================

def add_valid_start_constraints(
    model,
    x,
    repertoire,
    days,
    time_slots,
    room_amount,
):
    """
    Prevents a movie from starting in a slot from which
    all required blocks would not fit.

    x[(movie_index, day, slot_index, room)] == 1
    means that the movie STARTS in that slot.

    Example for required_blocks = 2:

        start at 20:00:
            occupies 20:00 and 22:00 -> allowed

        start at 22:00:
            would require another slot -> forbidden
    """

    slot_count = len(time_slots)

    for movie_index, movie in enumerate(repertoire):

        required_blocks = movie["required_blocks"]

        for day in days:
            for slot_index in range(slot_count):
                for room in range(room_amount):

                    if slot_index + required_blocks > slot_count:

                        model.Add(
                            x[
                                movie_index,
                                day,
                                slot_index,
                                room
                            ] == 0
                        )


def add_repertoire_rule(
    model,
    x,
    repertoire,
    days,
    time_slots,
    room_amount,
):
    """
    Hard constraint:

        every repertoire entry must be scheduled
        at least once during the week.

    Formally:

        sum(x[m,d,t,r]) >= 1
    """

    for movie_index, _movie in enumerate(repertoire):

        starts = []

        for day in days:
            for slot_index in range(len(time_slots)):
                for room in range(room_amount):

                    starts.append(
                        x[
                            movie_index,
                            day,
                            slot_index,
                            room
                        ]
                    )

        model.Add(
            sum(starts) >= 1
        )


def add_room_occupancy_constraints(
    model,
    x,
    repertoire,
    days,
    time_slots,
    room_amount,
):
    """
    Hard constraint:

        a room may be occupied by at most one movie
        during any time block.

    Important:
        x describes STARTS, not occupancy.

    Therefore a 2-block movie that starts at 16:00
    occupies both:

        16:00
        18:00

    Example:

        TITLE_A, required_blocks=2, starts at 16:00

    then another movie cannot start in the same room
    at 18:00.
    """

    slot_count = len(time_slots)

    for day in days:

        for occupied_slot in range(slot_count):

            for room in range(room_amount):

                occupying_variables = []

                for movie_index, movie in enumerate(
                    repertoire
                ):

                    required_blocks = (
                        movie["required_blocks"]
                    )

                    for start_slot in range(slot_count):

                        # Check whether a movie starting
                        # at start_slot occupies
                        # occupied_slot.
                        occupies_this_slot = (
                            start_slot
                            <= occupied_slot
                            < start_slot + required_blocks
                        )

                        # Ignore starts that would extend
                        # beyond the timetable.
                        valid_start = (
                            start_slot + required_blocks
                            <= slot_count
                        )

                        if (
                            occupies_this_slot
                            and valid_start
                        ):
                            occupying_variables.append(
                                x[
                                    movie_index,
                                    day,
                                    start_slot,
                                    room
                                ]
                            )

                model.Add(
                    sum(occupying_variables) <= 1
                )


def add_all_constraints(
    model,
    x,
    repertoire,
    days,
    time_slots,
    room_amount,
):
    """
    Convenience function used by model.py.

    Adds all hard scheduling constraints.
    """

    add_valid_start_constraints(
        model=model,
        x=x,
        repertoire=repertoire,
        days=days,
        time_slots=time_slots,
        room_amount=room_amount,
    )

    add_repertoire_rule(
        model=model,
        x=x,
        repertoire=repertoire,
        days=days,
        time_slots=time_slots,
        room_amount=room_amount,
    )

    add_room_occupancy_constraints(
        model=model,
        x=x,
        repertoire=repertoire,
        days=days,
        time_slots=time_slots,
        room_amount=room_amount,
    )