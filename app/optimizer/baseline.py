import random

from app.optimizer.constants import (
    DAYS_OF_WEEK,
    TIME_SLOTS,
)

from app.optimizer.constraints import (
    validate_optimizer_input,
)


def generate_baseline_schedule(
    repertoire,
    room_amount,
    random_seed=42,
    max_attempts=100,
):
    """
    Generates a simple baseline weekly movie schedule.

    Algorithm:
    1. Schedule every repertoire entry at least once.
    2. Fill the remaining available timetable positions
       with randomly selected repertoire entries.
    3. Respect required_blocks and room occupancy.

    This baseline does NOT use:
        - historical attendance,
        - baseline B,
        - overtime popularity OP_m,
        - ToD weights,
        - DoW weights,
        - optimization objective.

    It exists as a simple reference schedule against which
    the optimized CP-SAT schedule can be compared.
    """

    validate_optimizer_input(
        repertoire=repertoire,
        room_amount=room_amount,
    )

    if not repertoire:
        raise ValueError(
            "Cannot generate baseline for empty repertoire."
        )

    total_capacity = (
        len(DAYS_OF_WEEK)
        * len(TIME_SLOTS)
        * room_amount
    )

    required_capacity = sum(
        movie["required_blocks"]
        for movie in repertoire
    )

    if required_capacity > total_capacity:
        raise ValueError(
            "The repertoire cannot fit into the available "
            "weekly schedule."
        )

    rng = random.Random(random_seed)

    # A randomized greedy placement can theoretically create
    # fragmentation, therefore retry from scratch if necessary.
    for _ in range(max_attempts):

        result = _try_generate_baseline(
            repertoire=repertoire,
            room_amount=room_amount,
            rng=rng,
        )

        if result is not None:
            return result

    raise ValueError(
        "Could not generate a valid baseline schedule "
        f"after {max_attempts} attempts."
    )


def _try_generate_baseline(
    repertoire,
    room_amount,
    rng,
):
    """
    Performs one attempt at building the baseline schedule.
    """

    occupancy = create_empty_occupancy(
        room_amount=room_amount
    )

    schedule = []


    # =====================================================
    # 1. MINIMUM REPERTOIRE CONSTRAINT
    #
    # Every repertoire entry must appear at least once.
    #
    # 2-block entries are placed first because they are
    # harder to fit than 1-block entries.
    # =====================================================

    movie_indices = list(
        range(len(repertoire))
    )

    rng.shuffle(movie_indices)

    movie_indices.sort(
        key=lambda index:
            repertoire[index]["required_blocks"],
        reverse=True,
    )

    for movie_index in movie_indices:

        movie = repertoire[movie_index]

        valid_placements = get_valid_placements(
            movie=movie,
            occupancy=occupancy,
            room_amount=room_amount,
        )

        if not valid_placements:
            # This random construction attempt failed.
            return None

        day, slot_index, room = rng.choice(
            valid_placements
        )

        add_screening(
            schedule=schedule,
            occupancy=occupancy,
            movie=movie,
            movie_index=movie_index,
            day=day,
            slot_index=slot_index,
            room=room,
        )


    # =====================================================
    # 2. RANDOMLY FILL REMAINING SCHEDULE
    # =====================================================

    fill_remaining_slots(
        schedule=schedule,
        occupancy=occupancy,
        repertoire=repertoire,
        room_amount=room_amount,
        rng=rng,
    )


    # =====================================================
    # 3. SORT RESULT
    # =====================================================

    return sort_schedule(
        schedule=schedule
    )


def create_empty_occupancy(
    room_amount,
):
    """
    Creates room occupancy map.

    Key:
        (day, slot_index, room)

    Value:
        False -> free
        True  -> occupied
    """

    occupancy = {}

    for day in DAYS_OF_WEEK:

        for slot_index in range(
            len(TIME_SLOTS)
        ):

            for room in range(
                room_amount
            ):

                occupancy[
                    day,
                    slot_index,
                    room
                ] = False

    return occupancy


def get_valid_placements(
    movie,
    occupancy,
    room_amount,
):
    """
    Returns every currently valid start position
    for the given movie.

    A 1-block movie requires one free slot.

    A 2-block movie requires two consecutive free
    slots in the same room.
    """

    valid_placements = []

    required_blocks = movie[
        "required_blocks"
    ]

    slot_count = len(
        TIME_SLOTS
    )

    for day in DAYS_OF_WEEK:

        for slot_index in range(
            slot_count
        ):

            # Movie would extend beyond timetable.
            if (
                slot_index
                + required_blocks
                > slot_count
            ):
                continue

            for room in range(
                room_amount
            ):

                if can_place_movie(
                    occupancy=occupancy,
                    day=day,
                    slot_index=slot_index,
                    room=room,
                    required_blocks=required_blocks,
                ):
                    valid_placements.append(
                        (
                            day,
                            slot_index,
                            room,
                        )
                    )

    return valid_placements


def can_place_movie(
    occupancy,
    day,
    slot_index,
    room,
    required_blocks,
):
    """
    Checks whether all blocks required by the movie
    are free in the selected room.
    """

    if (
        slot_index
        + required_blocks
        > len(TIME_SLOTS)
    ):
        return False

    for offset in range(
        required_blocks
    ):

        occupied = occupancy[
            day,
            slot_index + offset,
            room
        ]

        if occupied:
            return False

    return True


def add_screening(
    schedule,
    occupancy,
    movie,
    movie_index,
    day,
    slot_index,
    room,
):
    """
    Adds screening to schedule and marks all
    required timetable blocks as occupied.
    """

    required_blocks = movie[
        "required_blocks"
    ]

    occupied_slots = TIME_SLOTS[
        slot_index:
        slot_index + required_blocks
    ]

    for offset in range(
        required_blocks
    ):

        occupancy[
            day,
            slot_index + offset,
            room
        ] = True

    schedule.append({
        "movie_index":
            movie_index,

        "title":
            movie["title"],

        "required_blocks":
            required_blocks,

        "day":
            day,

        "start_time":
            TIME_SLOTS[slot_index],

        "room":
            room + 1,

        "occupied_slots":
            list(occupied_slots),
    })


def fill_remaining_slots(
    schedule,
    occupancy,
    repertoire,
    room_amount,
    rng,
):
    """
    Traverses the timetable and fills every position
    for which at least one repertoire entry can
    legally start.

    Selection between valid movies is random.
    """

    for day in DAYS_OF_WEEK:

        for slot_index in range(
            len(TIME_SLOTS)
        ):

            for room in range(
                room_amount
            ):

                # Current block already belongs to
                # another screening.
                if occupancy[
                    day,
                    slot_index,
                    room
                ]:
                    continue

                candidates = []

                for movie_index, movie in enumerate(
                    repertoire
                ):

                    if can_place_movie(
                        occupancy=occupancy,
                        day=day,
                        slot_index=slot_index,
                        room=room,
                        required_blocks=movie[
                            "required_blocks"
                        ],
                    ):
                        candidates.append(
                            movie_index
                        )

                # For example, the final slot may remain
                # empty if every movie requires 2 blocks.
                if not candidates:
                    continue

                movie_index = rng.choice(
                    candidates
                )

                movie = repertoire[
                    movie_index
                ]

                add_screening(
                    schedule=schedule,
                    occupancy=occupancy,
                    movie=movie,
                    movie_index=movie_index,
                    day=day,
                    slot_index=slot_index,
                    room=room,
                )


def sort_schedule(
    schedule,
):
    """
    Sorts schedule by:
        day -> time -> room
    """

    day_order = {
        day: index
        for index, day in enumerate(
            DAYS_OF_WEEK
        )
    }

    time_order = {
        time_slot: index
        for index, time_slot in enumerate(
            TIME_SLOTS
        )
    }

    return sorted(
        schedule,
        key=lambda screening: (
            day_order[
                screening["day"]
            ],
            time_order[
                screening["start_time"]
            ],
            screening["room"],
        )
    )