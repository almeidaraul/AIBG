import pandas as pd
import pytest
from io import BytesIO, StringIO
from datetime import datetime, timedelta
from random import randint, randrange
from typing import BinaryIO, TextIO

from glikoz import dataframe_handler


@pytest.fixture(scope="function")
def random_dataframe_handler():
    """DataFrameHandler initialized with a random valid DataFrame"""
    number_of_samples = 4000
    datetime_strf = "%d/%m/%Y %H:%M"
    datetime_range = (datetime.strptime("01/01/2020 00:00", datetime_strf),
                      datetime.strptime("20/05/2023 23:59", datetime_strf))
    delta = datetime_range[1] - datetime_range[0]
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds

    dates, glucose, bolus, correction, basal, activity = [], [], [], [], [], []
    hba1c, meal, tags, comments, carbs = [], [], [], [], []
    possible_tags = [["a", "b"], ["a"], ["b"], []]
    for _ in range(number_of_samples):
        random_date = datetime_range[0] + timedelta(
            seconds=randrange(int_delta))
        dates.append(random_date)
        glucose.append(None if randint(0, 4) < 3 else randint(40, 320))
        bolus.append(randint(0, 10))
        correction.append(randint(0, 10))
        basal.append(randint(0, 30))
        activity.append(randint(0, 100))
        hba1c.append(randint(4, 8) + 0.1*randint(0, 10))
        meal.append({"carbs": randint(0, 100)})
        carbs.append(float(meal[-1]["carbs"]))
        tags.append(possible_tags[randint(0, len(possible_tags)-1)])
        comments.append("comment" if randint(0, 100) > 90 else "")

    df = pd.DataFrame({
            "date": dates,
            "glucose": glucose,
            "bolus_insulin": bolus,
            "correction_insulin": correction,
            "basal_insulin": basal,
            "activity": activity,
            "hba1c": hba1c,
            "meal": meal,
            "tags": tags,
            "comments": comments,
            "carbs": carbs
        })
    df["fast_insulin"] = df["bolus_insulin"] + df["correction_insulin"]
    df["total_insulin"] = df["fast_insulin"] + df["basal_insulin"]
    handler = dataframe_handler.DataFrameHandler(df)

    return handler


@pytest.fixture(scope="function")
def empty_dataframe_handler() -> dataframe_handler.DataFrameHandler:
    df = pd.DataFrame(columns=[
        "date", "glucose", "bolus_insulin", "correction_insulin",
        "basal_insulin", "activity", "hba1c", "meal", "tags", "comments",
        "carbs", "fast_insulin", "total_insulin"
    ])
    handler = dataframe_handler.DataFrameHandler(df)

    return handler


@pytest.fixture(scope="function")
def binaryIO_buffer() -> BinaryIO:
    return BytesIO()


@pytest.fixture(scope="function")
def textIO_buffer() -> TextIO:
    return StringIO()


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    return start + timedelta(seconds=randrange(int_delta))


def random_entries(number_of_entries: int) -> list:
    entries = []
    base = []
    base.append('"meta";"23"')
    tags = ["tag1", "tag2", "tag3"]
    for tag in tags:
        base.append(f'"tag";"{tag}"')
    foods = {"food1": 5, "food2": 10, "food3": 0, "food5": 100}
    for food, glycemic_idx in foods.items():
        base.append(f'"food";"{food}";;"{food}";"{glycemic_idx}"')
    entries.append(base)
    datetime_strf = "%Y-%m-%d %H:%M:%S"
    datetime_range = (datetime.strptime("2020-01-01 00:00:00", datetime_strf),
                      datetime.strptime("2023-05-20 23:59:59", datetime_strf))
    for _ in range(number_of_entries):
        current_entry = []
        date = random_date(datetime_range[0], datetime_range[1])
        date_formatted = date.strftime(datetime_strf)
        current_entry.append(f'"entry";"{date_formatted}";""')
        nothing_written: bool = True
        glucose = randint(30, 330)
        if randint(1, 100) < 70:
            current_entry.append(f'"measurement";"bloodsugar";"{glucose:.1f}"')
            nothing_written = False
        ins = [randint(0, 10), randint(0, 10), randint(0, 30)]
        for i in range(3):
            ins[i] = f"{ins[i]:.1f}"
        if randint(1, 100) < 80:
            current_entry.append(('"measurement";"insulin";'
                                  + f'"{ins[0]}";"{ins[1]}";"{ins[2]}"'))
            nothing_written = False
        hba1c = randint(4, 16)/2
        if randint(1, 100) < 2:
            current_entry.append(f'"measurement";"hba1c";"{hba1c:.1f}"')
            nothing_written = False
        meal = float(randint(0, 100))
        if randint(1, 100) < 50:
            current_entry.append(f'"measurement";"meal";"{meal:.1f}"')
            nothing_written = False
        for food, glycemic_idx in foods.items():
            if randint(1, 100) < 40:
                weight = randint(10, 100)
                current_entry.append(f'"foodEaten";"{food}";"{weight:.1f}"')
                nothing_written = False
        for tag in tags:
            if randint(1, 100) < 10:
                current_entry.append(f'"entryTag";"{tag}"')
                nothing_written = False
        activity = randint(0, 100)
        if nothing_written or randint(1, 100) < 10:
            current_entry.append(f'"measurement";"activity";"{activity:.1f}"')
        entries.append(current_entry)
    return entries


def StringIO_from_list_of_entries(entries: list) -> StringIO:
    target = StringIO()
    for entry in entries:
        for line in entry:
            target.write(line + '\n')
    target.seek(0)
    return target


@pytest.fixture(scope="function")
def valid_random_diaguard_csv_backup() -> TextIO:
    return StringIO_from_list_of_entries(random_entries(40))


@pytest.fixture(scope="function")
def diaguard_csv_backup_without_entries() -> TextIO:
    entries = random_entries(40)
    entries = entries[0]
    return StringIO_from_list_of_entries(entries)


@pytest.fixture(scope="function")
def diaguard_csv_backup_without_header() -> TextIO:
    entries = random_entries(40)
    entries = entries[1:]
    return StringIO_from_list_of_entries(entries)


@pytest.fixture(scope="function")
def diaguard_csv_backup_without_entry_start_on_first_entry() -> TextIO:
    entries = random_entries(40)
    entries[1] = entries[1][1:]
    return StringIO_from_list_of_entries(entries)


@pytest.fixture(scope="function")
def diaguard_csv_backup_with_invalid_date_field_on_last_entry() -> TextIO:
    entries = random_entries(40)
    entries.append(['"entry";"date_formatted";'])
    return StringIO_from_list_of_entries(entries)


@pytest.fixture(scope="function")
def empty_csv() -> TextIO:
    return StringIO()
