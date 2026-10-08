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