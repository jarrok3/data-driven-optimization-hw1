from collections import defaultdict

from ortools.sat.python import cp_model

from app.optimizer.constants import (
    ROOM_CAPACITY,
    TIME_SLOTS,
    DAYS_OF_WEEK,
)

from app.optimizer.constraints import (
    validate_optimizer_input,
    add_all_constraints,
)

from app.optimizer.objective import (
    calculate_expected_demand,
)


def build_model(
    repertoire,
    room_amount,
    day_weights,
    time_weights,
    historical_parameters,
):
    """
    Builds the complete CP-SAT optimization model.

    Parameters
    ----------
    repertoire:
        List of repertoire entries, for example:

        [
            {
                "title": "TITLE_A",
                "required_blocks": 1
            },
            {
                "title": "TITLE_B",
                "required_blocks": 2
            }
        ]

    room_amount:
        Number of available cinema rooms.

    day_weights:
        Dictionary containing DoW multipliers.

        Example:
        {
            "Monday": 1.0,
            "Tuesday": 1.0,
            ...
        }

    time_weights:
        Dictionary containing ToD multipliers.

        Example:
        {
            "10:00": 0.3,
            "12:00": 0.4,
            ...
        }

    historical_parameters:
        Output from preprocessing:

        {
            "base_attendance": float,

            "overtime_popularity": {
                "TITLE_A": float,
                ...
            }
        }

    Returns
    -------
    dict
        Complete model package containing:
        - CP-SAT model
        - decision variables
        - auxiliary variables
        - expected demand
        - scheduling metadata
    """

    # =====================================================
    # 1. INPUT VALIDATION
    # =====================================================

    validate_optimizer_input(
        repertoire=repertoire,
        room_amount=room_amount,
    )

    model = cp_model.CpModel()


    # =====================================================
    # 2. HISTORICAL PARAMETERS
    # =====================================================

    base_attendance = historical_parameters[
        "base_attendance"
    ]

    overtime_popularity = historical_parameters[
        "overtime_popularity"
    ]


    # =====================================================
    # 3. GROUP REPERTOIRE ENTRIES BY TITLE
    #
    # Repertoire rows remain separate scheduling entities
    # because two rows may have the same title but different
    # required_blocks.
    #
    # Demand, however, belongs to the movie title.
    # =====================================================

    title_to_movie_indices = defaultdict(list)

    for movie_index, movie in enumerate(repertoire):

        title = movie["title"]

        title_to_movie_indices[
            title
        ].append(movie_index)


    # =====================================================
    # 4. DECISION VARIABLES
    #
    # x[m, d, t, r] = 1
    #
    # means:
    # repertoire entry m STARTS
    # on day d
    # in time slot t
    # in room r
    #
    # x represents a START, not room occupancy.
    # =====================================================

    x = {}

    for movie_index, movie in enumerate(repertoire):

        for day in DAYS_OF_WEEK:

            for slot_index, time_slot in enumerate(
                TIME_SLOTS
            ):

                for room in range(room_amount):

                    variable_name = (
                        f"x_"
                        f"{movie_index}_"
                        f"{day}_"
                        f"{time_slot}_"
                        f"room_{room}"
                    )

                    x[
                        movie_index,
                        day,
                        slot_index,
                        room
                    ] = model.NewBoolVar(
                        variable_name
                    )


    # =====================================================
    # 5. HARD CONSTRAINTS
    # =====================================================

    add_all_constraints(
        model=model,
        x=x,
        repertoire=repertoire,
        days=DAYS_OF_WEEK,
        time_slots=TIME_SLOTS,
        room_amount=room_amount,
    )


    # =====================================================
    # 6. EXPECTED DEMAND
    #
    # D[m,d,t] =
    #
    # B * ToD[t] * DoW[d] * OP[m]
    #
    # This value is fully determined before optimization,
    # therefore it does not need to be a CP-SAT variable.
    #
    # CP-SAT requires integer values, so the result is
    # rounded to an integer number of viewers.
    # =====================================================

    expected_demand = {}

    for title in title_to_movie_indices:

        movie_op = overtime_popularity.get(
            title,
            1.0
        )

        for day in DAYS_OF_WEEK:

            day_weight = day_weights[day]

            for slot_index, time_slot in enumerate(
                TIME_SLOTS
            ):

                time_weight = time_weights[
                    time_slot
                ]

                demand = calculate_expected_demand(
                    base_attendance=base_attendance,
                    time_weight=time_weight,
                    day_weight=day_weight,
                    overtime_popularity=movie_op,
                )

                demand = max(
                    0,
                    int(round(demand))
                )

                expected_demand[
                    title,
                    day,
                    slot_index
                ] = demand


    # =====================================================
    # 7. ROOM COUNT VARIABLES
    #
    # room_count[title, day, slot]
    #
    # Number of rooms in which the same movie title
    # starts simultaneously.
    #
    # If the repertoire contains multiple rows with
    # the same title, they are aggregated here.
    # =====================================================

    room_count = {}

    for title, movie_indices in (
        title_to_movie_indices.items()
    ):

        for day in DAYS_OF_WEEK:

            for slot_index in range(
                len(TIME_SLOTS)
            ):

                room_count_var = model.NewIntVar(
                    0,
                    room_amount,
                    (
                        f"room_count_"
                        f"{title}_"
                        f"{day}_"
                        f"{slot_index}"
                    )
                )

                start_variables = []

                for movie_index in movie_indices:

                    for room in range(room_amount):

                        start_variables.append(
                            x[
                                movie_index,
                                day,
                                slot_index,
                                room
                            ]
                        )

                model.Add(
                    room_count_var
                    == sum(start_variables)
                )

                room_count[
                    title,
                    day,
                    slot_index
                ] = room_count_var


    # =====================================================
    # 8. REALIZED ATTENDANCE
    #
    # attendance[title, day, slot] =
    #
    # min(
    #     expected_demand,
    #     ROOM_CAPACITY * room_count
    # )
    #
    # Example:
    #
    # demand = 130
    #
    # 0 rooms -> 0 viewers
    # 1 room  -> 100 viewers
    # 2 rooms -> 130 viewers
    # 3 rooms -> still 130 viewers
    #
    # This prevents parallel rooms from creating
    # artificial additional demand.
    # =====================================================

    attendance = {}

    for title in title_to_movie_indices:

        for day in DAYS_OF_WEEK:

            for slot_index in range(
                len(TIME_SLOTS)
            ):

                demand = expected_demand[
                    title,
                    day,
                    slot_index
                ]

                maximum_attendance = min(
                    demand,
                    ROOM_CAPACITY * room_amount
                )

                attendance_var = model.NewIntVar(
                    0,
                    maximum_attendance,
                    (
                        f"attendance_"
                        f"{title}_"
                        f"{day}_"
                        f"{slot_index}"
                    )
                )

                total_capacity = (
                    ROOM_CAPACITY
                    * room_count[
                        title,
                        day,
                        slot_index
                    ]
                )

                model.AddMinEquality(
                    attendance_var,
                    [
                        demand,
                        total_capacity,
                    ]
                )

                attendance[
                    title,
                    day,
                    slot_index
                ] = attendance_var


    # =====================================================
    # 9. OBJECTIVE FUNCTION
    #
    # Maximize:
    #
    # Σ attendance[m,d,t]
    #
    # across all titles, days and time slots.
    # =====================================================

    model.Maximize(
        sum(attendance.values())
    )


    # =====================================================
    # 10. RETURN MODEL PACKAGE
    #
    # engine.py will later use this dictionary to:
    #
    # - run CpSolver
    # - read x variables
    # - reconstruct the final schedule
    # - read objective value
    # =====================================================

    return {
        "model": model,

        "x": x,

        "room_count": room_count,

        "attendance": attendance,

        "expected_demand": expected_demand,

        "title_to_movie_indices":
            dict(title_to_movie_indices),

        "repertoire": repertoire,

        "room_amount": room_amount,

        "days": DAYS_OF_WEEK,

        "time_slots": TIME_SLOTS,
    }