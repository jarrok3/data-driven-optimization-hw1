from ortools.sat.python import cp_model

from app.optimizer.model import build_model


def solve_schedule(
    repertoire,
    room_amount,
    day_weights,
    time_weights,
    historical_parameters,
    max_time_seconds=10.0,
):
    """
    Builds and solves the CP-SAT movie scheduling model.

    Parameters
    ----------
    repertoire:
        Weekly repertoire.

    room_amount:
        Number of available cinema rooms.

    day_weights:
        Day-of-week multipliers.

    time_weights:
        Time-of-day multipliers.

    historical_parameters:
        Dictionary produced by preprocessing:

        {
            "base_attendance": float,
            "overtime_popularity": {
                "TITLE_A": float,
                ...
            }
        }

    max_time_seconds:
        Maximum time allowed for the CP-SAT solver.

    Returns
    -------
    dict
        JSON-friendly optimization result.
    """

    # =====================================================
    # 1. BUILD MODEL
    # =====================================================

    model_data = build_model(
        repertoire=repertoire,
        room_amount=room_amount,
        day_weights=day_weights,
        time_weights=time_weights,
        historical_parameters=historical_parameters,
    )

    model = model_data["model"]
    x = model_data["x"]

    days = model_data["days"]
    time_slots = model_data["time_slots"]


    # =====================================================
    # 2. CREATE SOLVER
    # =====================================================

    solver = cp_model.CpSolver()

    solver.parameters.max_time_in_seconds = (
        max_time_seconds
    )


    # =====================================================
    # 3. SOLVE
    # =====================================================

    status = solver.Solve(model)


    # =====================================================
    # 4. HANDLE STATUS
    # =====================================================

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        return {
            "status": get_status_name(status),
            "objective_value": None,
            "schedule": [],
            "message": (
                "No feasible schedule was found."
            ),
        }


    # =====================================================
    # 5. EXTRACT SCHEDULE
    # =====================================================

    schedule = extract_schedule(
        solver=solver,
        x=x,
        repertoire=repertoire,
        room_amount=room_amount,
        days=days,
        time_slots=time_slots,
    )


    # =====================================================
    # 6. ATTENDANCE DETAILS
    # =====================================================

    attendance_details = (
        extract_attendance_details(
            solver=solver,
            model_data=model_data,
        )
    )


    # =====================================================
    # 7. RETURN RESULT
    # =====================================================

    return {
        "status": get_status_name(status),

        "objective_value": solver.ObjectiveValue(),

        "best_objective_bound":
            solver.BestObjectiveBound(),

        "schedule": schedule,

        "attendance": attendance_details,

        "message": (
            "Optimization completed successfully."
        ),
    }


def extract_schedule(
    solver,
    x,
    repertoire,
    room_amount,
    days,
    time_slots,
):
    """
    Converts selected CP-SAT x variables into
    a readable weekly schedule.

    Each returned entry represents a movie START.
    """

    schedule = []

    for movie_index, movie in enumerate(repertoire):

        required_blocks = movie[
            "required_blocks"
        ]

        title = movie["title"]

        for day in days:

            for slot_index, time_slot in enumerate(
                time_slots
            ):

                for room in range(room_amount):

                    variable = x[
                        movie_index,
                        day,
                        slot_index,
                        room
                    ]

                    if solver.Value(variable) == 1:

                        occupied_slots = (
                            get_occupied_slots(
                                slot_index=slot_index,
                                required_blocks=required_blocks,
                                time_slots=time_slots,
                            )
                        )

                        schedule.append({
                            "movie_index":
                                movie_index,

                            "title":
                                title,

                            "required_blocks":
                                required_blocks,

                            "day":
                                day,

                            "start_time":
                                time_slot,

                            "room":
                                room + 1,

                            "occupied_slots":
                                occupied_slots,
                        })

    return sort_schedule(
        schedule=schedule,
        days=days,
        time_slots=time_slots,
    )


def get_occupied_slots(
    slot_index,
    required_blocks,
    time_slots,
):
    """
    Returns all timetable slots occupied by
    a screening.

    Example:

        slot_index = 3
        required_blocks = 2

    may return:

        ["16:00", "18:00"]
    """

    end_index = (
        slot_index + required_blocks
    )

    return time_slots[
        slot_index:end_index
    ]


def extract_attendance_details(
    solver,
    model_data,
):
    """
    Extracts expected demand, room count and
    realized attendance for scheduled title/day/slot
    combinations.
    """

    attendance_result = []

    room_count = model_data[
        "room_count"
    ]

    attendance = model_data[
        "attendance"
    ]

    expected_demand = model_data[
        "expected_demand"
    ]

    days = model_data["days"]
    time_slots = model_data[
        "time_slots"
    ]

    title_to_movie_indices = model_data[
        "title_to_movie_indices"
    ]

    for title in title_to_movie_indices:

        for day in days:

            for slot_index, time_slot in enumerate(
                time_slots
            ):

                rooms = solver.Value(
                    room_count[
                        title,
                        day,
                        slot_index
                    ]
                )

                if rooms == 0:
                    continue

                realized = solver.Value(
                    attendance[
                        title,
                        day,
                        slot_index
                    ]
                )

                demand = expected_demand[
                    title,
                    day,
                    slot_index
                ]

                attendance_result.append({
                    "title":
                        title,

                    "day":
                        day,

                    "time":
                        time_slot,

                    "rooms":
                        rooms,

                    "expected_demand":
                        demand,

                    "expected_attendance":
                        realized,
                })

    return attendance_result


def sort_schedule(
    schedule,
    days,
    time_slots,
):
    """
    Sorts the resulting schedule by:

        day
        time
        room
    """

    day_order = {
        day: index
        for index, day in enumerate(days)
    }

    time_order = {
        time_slot: index
        for index, time_slot in enumerate(
            time_slots
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


def get_status_name(status):
    """
    Converts CP-SAT status code into readable text.
    """

    status_names = {
        cp_model.OPTIMAL:
            "OPTIMAL",

        cp_model.FEASIBLE:
            "FEASIBLE",

        cp_model.INFEASIBLE:
            "INFEASIBLE",

        cp_model.MODEL_INVALID:
            "MODEL_INVALID",

        cp_model.UNKNOWN:
            "UNKNOWN",
    }

    return status_names.get(
        status,
        "UNKNOWN"
    )