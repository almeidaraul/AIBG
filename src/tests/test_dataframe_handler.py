import pandas as pd

from glikoz.dataframe_handler import DiaguardCSVParser


class TestDiaguardCSVParser:
    expected_columns = {
        "date", "glucose", "bolus_insulin", "correction_insulin",
        "basal_insulin", "activity", "hba1c", "meal", "tags",
        "comments", "carbs", "fast_insulin", "total_insulin"
    }

    def test_empty_csv(self, empty_csv):
        parser = DiaguardCSVParser()
        df = parser.parse_csv(empty_csv)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert set(df.columns) == self.expected_columns

    def test_csv_without_entries(self, diaguard_csv_backup_without_entries):
        parser = DiaguardCSVParser()
        df = parser.parse_csv(diaguard_csv_backup_without_entries)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert set(df.columns) == self.expected_columns

    def test_csv_without_header(self, diaguard_csv_backup_without_header):
        parser = DiaguardCSVParser()
        df = parser.parse_csv(diaguard_csv_backup_without_header)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == self.expected_columns
        assert not df.empty

    def test_csv_without_entry_start_on_first_entry(
            self, diaguard_csv_backup_without_entry_start_on_first_entry):
        parser = DiaguardCSVParser()
        df = parser.parse_csv(
            diaguard_csv_backup_without_entry_start_on_first_entry)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == self.expected_columns
        assert not df.empty

    def test_csv_with_invalid_date(
            self, diaguard_csv_backup_with_invalid_date_field_on_last_entry):
        parser = DiaguardCSVParser()
        df = parser.parse_csv(
            diaguard_csv_backup_with_invalid_date_field_on_last_entry)
        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == self.expected_columns
        assert not df.empty

    def test_valid_csv_glucose_entry_count(self,
                                           valid_random_diaguard_csv_backup):
        """
        Number of DataFrame rows with glucose values and CSV lines with
        bloodsugar field should be equal
        """
        parser = DiaguardCSVParser()
        df = parser.parse_csv(valid_random_diaguard_csv_backup)
        buffer_value = valid_random_diaguard_csv_backup.getvalue()
        bloodsugar_lines = buffer_value.count("bloodsugar")
        assert bloodsugar_lines == df["glucose"].count()


class TestDataFrameHandler:
    def test_dataframe_versions_are_equal_in_unchanged_handler(
            self, random_dataframe_handler):
        """
        The df and original_df dataframes should be equal upon instantiation
        """
        original_df = random_dataframe_handler.original_df
        current_df = random_dataframe_handler.df
        assert original_df.equals(current_df)

    def test_dataframe_versions_are_different_objects(
            self, random_dataframe_handler):
        """
        The df and original_df dataframes should be different objects
        """
        original_df = random_dataframe_handler.original_df
        current_df = random_dataframe_handler.df
        assert original_df is not current_df

    def test_reset_df(self, random_dataframe_handler):
        """df should be reset to equal original_df"""
        random_dataframe_handler.df = None
        random_dataframe_handler.reset_df()
        assert random_dataframe_handler.original_df.equals(
            random_dataframe_handler.df)

    def test_col_lims_with_empty_result(self, random_dataframe_handler):
        """When no rows fit the filter, the resulting df should be empty"""
        column = "glucose"
        max_value_in_column = random_dataframe_handler.df[column].max()
        random_dataframe_handler.col_lims(
            column=column, lower_bound=max_value_in_column+1,
            upper_bound=max_value_in_column+2)
        assert random_dataframe_handler.df.empty

    def test_col_lims_with_bound_interval_empty(self,
                                                random_dataframe_handler):
        """
        When the filter interval is empty, the resulting df should be empty
        """
        column = "glucose"
        random_dataframe_handler.col_lims(column=column, lower_bound=10,
                                          upper_bound=1)
        assert random_dataframe_handler.df.empty

    def test_last_x_days_with_negative_x(self, random_dataframe_handler):
        """
        A negative value of x is interpreted as "more than 5 days in the
        future", so the resulting df should be empty
        """
        x = -5
        random_dataframe_handler.last_x_days(x)
        assert random_dataframe_handler.df.empty

    def test_last_x_days_with_x_equal_to_zero(self, random_dataframe_handler):
        """A value of 0 corresponds to an empty query interval"""
        x = 0
        random_dataframe_handler.last_x_days(x)
        assert random_dataframe_handler.df.empty

    def test_last_x_days_with_x_greater_than_zero(self,
                                                  random_dataframe_handler):
        """Difference between extreme dates should not exceed x"""
        x = 5
        random_dataframe_handler.last_x_days(x)
        date_series = random_dataframe_handler.df["date"]
        date_delta = date_series.max() - date_series.min()
        assert date_delta.days <= x
