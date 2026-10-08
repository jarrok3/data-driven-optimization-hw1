from collections import defaultdict
from datetime import date, timedelta
from app.optimizer.constants import HISTORY_WEEKS

def get_weekday_name(play_day):
    """
    Converts YYYY-MM-DD into weekday name.

    Example:
        "2026-01-03" -> "Saturday"
    """

    if isinstance(play_day, str):
        play_day = date.fromisoformat(play_day)

    return play_day.strftime("%A")


def filter_records(
    records,
    ref_weeks=HISTORY_WEEKS,
    reference_date=None,
    offset_weeks=0
):
    """
    Filters records to a specific historical window.

    Parameters
    ----------
    records:
        Historical purchase records.

    ref_weeks:
        Width of the requested window in weeks.

    reference_date:
        Upper reference point.
        Defaults to today's date.

    offset_weeks:
        How many weeks backwards the window should be shifted.

    Examples
    --------
    Last 4 weeks:
        filter_records(records, ref_weeks=4)

    Last week (t-1):
        filter_records(
            records,
            ref_weeks=1,
            offset_weeks=0
        )

    Week before last (t-2):
        filter_records(
            records,
            ref_weeks=1,
            offset_weeks=1
        )
    """

    if reference_date is None:
        reference_date = date.today()

    window_end = (
        reference_date
        - timedelta(weeks=offset_weeks)
    )

    window_start = (
        window_end
        - timedelta(weeks=ref_weeks)
    )

    return [
        record
        for record in records
        if (
            window_start
            <= date.fromisoformat(record["play_day"])
            < window_end
        )
    ]


def aggregate_screenings(records):
    """
    Aggregates purchase records into individual screenings.

    A screening is identified by:
        title
        venue
        day
        curtain time
    """

    screenings = defaultdict(int)

    for record in records:

        key = (
            record["title_tag"],
            record["venue_tag"],
            record["play_day"],
            record["curtain_time"]
        )

        screenings[key] += record["passes_bought"]

    return screenings


def normalize_screenings(
    screenings,
    time_weights,
    day_weights
):
    """
    Removes ToD and DoW influence from observed attendance.

    neutral_attendance =
        attendance / (ToD * DoW)

    This prevents a movie shown mainly in weak slots from
    looking artificially unpopular.
    """

    normalized = []

    for (
        title,
        venue,
        play_day,
        curtain_time
    ), tickets in screenings.items():

        weekday = get_weekday_name(play_day)

        if curtain_time not in time_weights:
            raise ValueError(
                f"Missing time weight for {curtain_time}"
            )

        if weekday not in day_weights:
            raise ValueError(
                f"Missing day weight for {weekday}"
            )

        time_weight = time_weights[curtain_time]
        day_weight = day_weights[weekday]

        if time_weight <= 0:
            raise ValueError(
                f"Time weight for {curtain_time} "
                "must be greater than 0."
            )

        if day_weight <= 0:
            raise ValueError(
                f"Day weight for {weekday} "
                "must be greater than 0."
            )

        neutral_attendance = (
            tickets
            / (time_weight * day_weight)
        )

        normalized.append({
            "title": title,
            "venue": venue,
            "play_day": play_day,
            "curtain_time": curtain_time,
            "attendance": tickets,
            "neutral_attendance": neutral_attendance
        })

    return normalized


def calculate_base_attendance(
    normalized_screenings
) -> float:
    """
    Calculates baseline B.

    B is the mean neutralized attendance per screening
    across the baseline historical period.
    """

    if not normalized_screenings:
        return 1.0

    return sum(
        screening["neutral_attendance"]
        for screening in normalized_screenings
    ) / len(normalized_screenings)


def calculate_average_by_movie(
    normalized_screenings
):
    """
    Calculates mean neutralized attendance per screening
    for every movie.

    Returns:
        {
            "TITLE_A": 52.4,
            "TITLE_B": 37.8,
            ...
        }
    """

    movie_values = defaultdict(list)

    for screening in normalized_screenings:

        movie_values[
            screening["title"]
        ].append(
            screening["neutral_attendance"]
        )

    return {
        title: sum(values) / len(values)
        for title, values in movie_values.items()
        if values
    }


def calculate_global_average(
    normalized_screenings
):
    """
    Calculates V_global for a given period:
    average neutralized attendance across all screenings.
    """

    if not normalized_screenings:
        return 1.0

    return sum(
        screening["neutral_attendance"]
        for screening in normalized_screenings
    ) / len(normalized_screenings)


def calculate_overtime_popularity(
    last_week_screenings,
    previous_week_screenings
) -> dict:
    """
    Calculates OP_m.

    Definition:

        If movie has history in t-1 and t-2:

            OP_m = V_m,t-1 / V_m,t-2

        If movie exists in t-1 but not t-2:

            OP_m = V_m,t-1 / V_global,t-1

        If movie has no t-1 history:

            OP_m = 1.0

    V values are based on neutralized attendance so that
    ToD and DoW effects are not counted twice.
    """

    last_week_averages = calculate_average_by_movie(
        last_week_screenings
    )

    previous_week_averages = calculate_average_by_movie(
        previous_week_screenings
    )

    global_last_week_average = calculate_global_average(
        last_week_screenings
    )

    all_titles = (
        set(last_week_averages)
        | set(previous_week_averages)
    )

    popularity = {}

    for title in all_titles:

        has_last_week = (
            title in last_week_averages
        )

        has_previous_week = (
            title in previous_week_averages
        )

        # No data in the most recent week:
        # neutral retention.
        if not has_last_week:
            popularity[title] = 1.0
            continue

        v_last = last_week_averages[title]

        # Two weeks of history.
        if has_previous_week:

            v_previous = previous_week_averages[
                title
            ]

            if v_previous <= 0:
                popularity[title] = 1.0
            else:
                popularity[title] = (
                    v_last / v_previous
                )

            continue

        # Only one week of history.
        if global_last_week_average <= 0:
            popularity[title] = 1.0
        else:
            popularity[title] = (
                v_last / global_last_week_average
            )

    return popularity


def build_historical_parameters(
    records,
    time_weights,
    day_weights,
    reference_date=None
):
    """
    Main preprocessing entry point. Returns a dictionary where the values for keys are dictionaries

    Baseline:
        previous 4 weeks

    Overtime popularity:
        t-1 = previous week
        t-2 = week before previous week
    """

    # --------------------------------------------------
    # BASELINE B
    # --------------------------------------------------

    baseline_records = filter_records(
        records,
        ref_weeks=HISTORY_WEEKS,
        reference_date=reference_date
    )

    baseline_screenings = aggregate_screenings(
        baseline_records
    )

    normalized_baseline = normalize_screenings(
        baseline_screenings,
        time_weights,
        day_weights
    )

    base_attendance = calculate_base_attendance(
        normalized_baseline
    )


    # --------------------------------------------------
    # LAST WEEK: t-1
    # --------------------------------------------------

    last_week_records = filter_records(
        records,
        ref_weeks=1,
        reference_date=reference_date,
        offset_weeks=0
    )

    last_week_screenings = aggregate_screenings(
        last_week_records
    )

    normalized_last_week = normalize_screenings(
        last_week_screenings,
        time_weights,
        day_weights
    )


    # --------------------------------------------------
    # PREVIOUS WEEK: t-2
    # --------------------------------------------------

    previous_week_records = filter_records(
        records,
        ref_weeks=1,
        reference_date=reference_date,
        offset_weeks=1
    )

    previous_week_screenings = aggregate_screenings(
        previous_week_records
    )

    normalized_previous_week = normalize_screenings(
        previous_week_screenings,
        time_weights,
        day_weights
    )


    # --------------------------------------------------
    # OP_m
    # --------------------------------------------------

    overtime_popularity = (
        calculate_overtime_popularity(
            normalized_last_week,
            normalized_previous_week
        )
    )


    return {
        "base_attendance": base_attendance,
        "overtime_popularity": overtime_popularity
    }