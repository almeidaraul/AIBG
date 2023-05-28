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


@pytest.fixture(scope="function")
def valid_random_diaguard_csv_backup() -> TextIO:
    pass


@pytest.fixture(scope="function")
def invalid_random_diaguard_csv_backup() -> TextIO:
    pass


@pytest.fixture(scope="function")
def empty_csv() -> TextIO:
    pass
