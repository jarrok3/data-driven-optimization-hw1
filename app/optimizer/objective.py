from collections import defaultdict

from app.optimizer.constants import ROOM_CAPACITY


def calculate_expected_demand(
    base_attendance,
    time_weight,
    day_weight,
    overtime_popularity
):
    return (
        base_attendance
        * time_weight
        * day_weight
        * overtime_popularity
    )


def calculate_realized_attendance(
    expected_demand,
    room_count
):
    capacity = ROOM_CAPACITY * room_count

    return min(
        expected_demand,
        capacity
    )


def evaluate_schedule(
    schedule,
    base_attendance,
    overtime_popularity,
    day_weights,
    time_weights,
):
    """
    Calculates total expected attendance for
    an already generated schedule.

    Parallel screenings of the same title at the same
    day/time share the same demand.

    Returns:
        {
            "objective_value": float,
            "attendance": [...]
        }
    """

    parallel_screenings = defaultdict(int)

    for screening in schedule:

        key = (
            screening["title"],
            screening["day"],
            screening["start_time"],
        )

        parallel_screenings[key] += 1


    total_attendance = 0
    attendance_details = []


    for (
        title,
        day,
        start_time
    ), room_count in parallel_screenings.items():

        movie_op = overtime_popularity.get(
            title,
            1.0
        )

        expected_demand = (
            calculate_expected_demand(
                base_attendance=base_attendance,
                time_weight=time_weights[start_time],
                day_weight=day_weights[day],
                overtime_popularity=movie_op,
            )
        )

        expected_demand = max(
            0,
            int(round(expected_demand))
        )

        realized_attendance = (
            calculate_realized_attendance(
                expected_demand=expected_demand,
                room_count=room_count,
            )
        )

        total_attendance += (
            realized_attendance
        )

        attendance_details.append({
            "title": title,
            "day": day,
            "time": start_time,
            "rooms": room_count,
            "expected_demand":
                expected_demand,
            "expected_attendance":
                realized_attendance,
        })


    return {
        "objective_value":
            total_attendance,

        "attendance":
            attendance_details,
    }