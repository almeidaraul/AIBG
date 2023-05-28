class TestDiaguardCSVParser:
    def test_empty_csv(self):
        pass

    def test_csv_without_entries(self):
        pass

    def test_valid_csv_glucose_entry_count(self):
        """
        Number of DataFrame rows with glucose values and CSV lines with
        bloodsugar field should be equal
        """
        pass

    def test_invalid_csv(self):
        pass


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
