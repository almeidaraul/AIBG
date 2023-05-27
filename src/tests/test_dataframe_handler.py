import pandas as pd
import pytest
from datetime import datetime, timedelta
from random import randint, randrange

from glikoz import dataframe_handler


@pytest.fixture(scope="function")
def random_handler():
    """Generate a DataFrameHandler from a random valid DataFrame"""
    number_of_samples = 40
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


class TestDataFrameHandler:
    def test_dataframe_versions_are_equal_in_unchanged_handler(self,
                                                               random_handler):
        """
        The df and original_df dataframes should be equal upon instantiation
        """
        assert random_handler.original_df.equals(random_handler.df)

    def test_dataframe_versions_are_different_objects(self, random_handler):
        """
        The df and original_df dataframes should be different objects
        """
        assert random_handler.original_df is not random_handler.df

    def test_reset_df(self, random_handler):
        """df should be reset to equal original_df"""
        random_handler.df = None
        random_handler.reset_df()
        assert random_handler.original_df.equals(random_handler.df)

    def test_col_lims_with_empty_result(self, random_handler):
        """When no rows fit the filter, the resulting df should be empty"""
        column = "glucose"
        max_value_in_column = random_handler.df[column].max()
        random_handler.col_lims(
            column=column, lower_bound=max_value_in_column+1,
            upper_bound=max_value_in_column+2)
        assert random_handler.df.empty

    def test_col_lims_with_bound_interval_empty(self, random_handler):
        """
        When the filter interval is empty, the resulting df should be empty
        """
        column = "glucose"
        random_handler.col_lims(column=column, lower_bound=10, upper_bound=1)
        assert random_handler.df.empty

    def test_last_x_days_with_negative_x(self, random_handler):
        """
        A negative value of x is interpreted as "more than 5 days in the
        future", so the resulting df should be empty
        """
        x = -5
        random_handler.last_x_days(x)
        assert random_handler.df.empty

    def test_last_x_days_with_x_equal_to_zero(self, random_handler):
        """A value of 0 corresponds to an empty query interval"""
        x = 0
        random_handler.last_x_days(x)
        assert random_handler.df.empty

    def test_last_x_days_with_x_greater_than_zero(self, random_handler):
        """Difference between extreme dates should not exceed x"""
        x = 5
        random_handler.last_x_days(x)
        date_series = random_handler.df["date"]
        date_delta = date_series.max() - date_series.min()
        assert date_delta.days <= x

# TODO test DiaguardCSVParser
