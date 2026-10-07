import os
import random
import sqlite3
from datetime import date, timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


SCRIPT_DIR = Path(__file__).resolve().parent
DATABASE_FILENAME = os.getenv(
    "DATABASE_PATH",
    "dummy_data.db"
)
DATABASE_PATH = SCRIPT_DIR / DATABASE_FILENAME

NUMBER_OF_RECORDS = int(
    os.getenv("NUMBER_OF_RECORDS", "10000")
)

# STATIC seed load if was specified
RANDOM_SEED = int(
    os.getenv("RANDOM_SEED", "42")
)

NOISE_MIN = float(
    os.getenv("NOISE_MIN", "0.85")
)

NOISE_MAX = float(
    os.getenv("NOISE_MAX", "1.15")
)
random.seed(RANDOM_SEED)


TITLES = [
    "TITLE_A",
    "TITLE_B",
    "TITLE_C",
    "TITLE_D",
    "TITLE_E",
    "TITLE_F",
]


VENUES = [
    "VENUE_01",
    "VENUE_02",
    "VENUE_03",
]


CURTAIN_TIMES = [
    "10:00",
    "12:00",
    "14:00",
    "16:00",
    "18:00",
    "20:00",
    "22:00",
]


ACCOUNTS = [
    f"ACCOUNT_{i:03d}"
    for i in range(1, 201)
]


# Additional popularity parameters (just for data generation)
TITLE_POPULARITY = {
    "TITLE_A": 1.80,
    "TITLE_B": 1.45,
    "TITLE_C": 1.15,
    "TITLE_D": 0.95,
    "TITLE_E": 0.70,
    "TITLE_F": 0.45,
}


# Time of day impact
TIME_POPULARITY = {
    "10:00": 0.3,
    "12:00": 0.4,
    "14:00": 0.6,
    "16:00": 1.00,
    "18:00": 1.50,
    "20:00": 1.80,
    "22:00": 1.1,
}


# weekday():
#
# Monday    = 0
# Tuesday   = 1
# Wednesday = 2
# Thursday  = 3
# Friday    = 4
# Saturday  = 5
# Sunday    = 6
DAY_POPULARITY = {
    0: 1.00,
    1: 1.00,
    2: 1.00,
    3: 1.00,
    4: 1.30,
    5: 1.50,
    6: 1.35,
}

def create_table(connection):
    connection.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title_tag TEXT NOT NULL,
            venue_tag TEXT NOT NULL,

            play_day TEXT NOT NULL,
            curtain_time TEXT NOT NULL,

            account_tag TEXT NOT NULL,

            passes_bought INTEGER NOT NULL
                CHECK (passes_bought > 0)
        )
    """)


def generate_screenings():
    screenings = []

    start_date = date(2026, 1, 1)

    for day_offset in range(35):

        play_day = start_date + timedelta(days=day_offset)

        for venue in VENUES:

            daily_titles = random.sample(
                TITLES,
                k=random.randint(3, 6)
            )

            for title in daily_titles:

                curtain_time = random.choice(
                    CURTAIN_TIMES
                )

                screenings.append({
                    "title_tag": title,
                    "venue_tag": venue,
                    "play_day": play_day,
                    "curtain_time": curtain_time,
                })

    return screenings

def calculate_screening_popularity(screening):
    """
    calc subjective popularity of a single screening
    """

    title_factor = TITLE_POPULARITY[
        screening["title_tag"]
    ]

    time_factor = TIME_POPULARITY[
        screening["curtain_time"]
    ]

    day_factor = DAY_POPULARITY[
        screening["play_day"].weekday()
    ]

    base_popularity = (
        title_factor
        * time_factor
        * day_factor
    )

    noise = random.uniform(
        NOISE_MIN,
        NOISE_MAX
    )

    return base_popularity * noise


def generate_record(screening):

    passes_bought = random.choices(
        population=[1, 2, 3, 4, 5, 6],
        weights=[35, 35, 15, 8, 5, 2],
        k=1
    )[0]

    return (
        screening["title_tag"],
        screening["venue_tag"],
        screening["play_day"].isoformat(),
        screening["curtain_time"],
        random.choice(ACCOUNTS),
        passes_bought
    )


def seed_database():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    create_table(connection)

    # Clean data after reseeding
    connection.execute(
        "DELETE FROM records"
    )

    screenings = generate_screenings()

    # Calc weight for each seanse
    screening_weights = [
        calculate_screening_popularity(screening)
        for screening in screenings
    ]

    records = []

    for _ in range(NUMBER_OF_RECORDS):
        screening = random.choices(
            population=screenings,
            weights=screening_weights,
            k=1
        )[0]

        records.append(
            generate_record(screening)
        )

    connection.executemany("""
        INSERT INTO records (
            title_tag,
            venue_tag,
            play_day,
            curtain_time,
            account_tag,
            passes_bought
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, records)

    connection.commit()

    print_summary(connection)

    connection.close()

    print(
        f"\nInserted {NUMBER_OF_RECORDS} records "
        f"into {DATABASE_PATH}"
    )


def print_summary(connection):

    print("\n--- Purchases by title ---")

    rows = connection.execute("""
        SELECT
            title_tag,
            COUNT(*) AS purchases,
            SUM(passes_bought) AS tickets
        FROM records
        GROUP BY title_tag
        ORDER BY tickets DESC
    """).fetchall()

    for row in rows:
        print(row)


    print("\n--- Tickets by curtain time ---")

    rows = connection.execute("""
        SELECT
            curtain_time,
            SUM(passes_bought) AS tickets
        FROM records
        GROUP BY curtain_time
        ORDER BY curtain_time
    """).fetchall()

    for row in rows:
        print(row)


    print("\n--- Tickets by venue ---")

    rows = connection.execute("""
        SELECT
            venue_tag,
            SUM(passes_bought) AS tickets
        FROM records
        GROUP BY venue_tag
        ORDER BY tickets DESC
    """).fetchall()

    for row in rows:
        print(row)


if __name__ == "__main__":
    seed_database()