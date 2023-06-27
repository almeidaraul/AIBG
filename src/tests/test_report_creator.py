import numpy as np
import pandas as pd
from glikoz.report_creator import (ReportCreator, PDFReportCreator,
                                   JSONReportCreator)


class TestReportCreator:
    def test_hba1c_for_empty_glucose_series_is_none(self,
                                                    random_dataframe_handler):
        random_dataframe_handler.df["glucose"] = None
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_hba1c()
        assert report_creator.retrieve("hba1c") is None

    def test_save_hba1c_where_glucose_is_not_empty(self,
                                                   random_dataframe_handler):
        random_dataframe_handler.df["glucose"] = 160
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_hba1c()
        assert report_creator.retrieve("hba1c") == (160+46.7)/28.7

    def test_save_tir(self, random_dataframe_handler):
        sequence_size = len(random_dataframe_handler.df["glucose"])
        new_sequence = ([200]
                        + [100, 110]
                        + [40, 50, 60]
                        + [None]*(sequence_size-6))
        random_dataframe_handler.df["glucose"] = pd.Series(new_sequence)
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir(lower_bound=70, upper_bound=180)
        time_in_range = report_creator.retrieve("time_in_range")
        time_above_range = report_creator.retrieve("time_above_range")
        time_below_range = report_creator.retrieve("time_below_range")
        assert time_in_range == 2
        assert time_above_range == 1
        assert time_below_range == 3

    def test_save_tir_with_no_glucose_entries_gives_0(
            self, random_dataframe_handler):
        random_dataframe_handler.df["glucose"] = None
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir()
        time_in_range = report_creator.retrieve("time_in_range")
        time_above_range = report_creator.retrieve("time_above_range")
        time_below_range = report_creator.retrieve("time_below_range")
        assert time_in_range == 0
        assert time_above_range == 0
        assert time_below_range == 0

    def test_total_entry_count_is_numeric(self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_entry_count()
        entry_count = report_creator.retrieve("entry_count")
        assert isinstance(entry_count, int)

    def test_mean_daily_entry_count_is_numeric(self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_entry_count()
        mean_daily_entry_count = report_creator.retrieve(
            "mean_daily_entry_count")
        assert isinstance(mean_daily_entry_count, float)

    def test_entry_count_without_entries_is_zero(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_entry_count()
        entry_count = report_creator.retrieve("entry_count")
        mean_daily_entry_count = report_creator.retrieve(
            "mean_daily_entry_count")
        assert entry_count == 0
        assert mean_daily_entry_count == 0

    def test_mean_daily_fast_insulin_is_numeric(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_fast_insulin_use()
        mean_daily_fast_insulin = report_creator.retrieve(
            "mean_daily_fast_insulin")
        assert isinstance(mean_daily_fast_insulin, float)

    def test_std_daily_fast_insulin_is_numeric(self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_fast_insulin_use()
        std_daily_fast_insulin = report_creator.retrieve(
            "std_daily_fast_insulin")
        assert isinstance(std_daily_fast_insulin, float)

    def test_daily_fast_insulin_use_with_no_entries(self,
                                                    empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_fast_insulin_use()
        mean_daily_fast_insulin = report_creator.retrieve(
            "mean_daily_fast_insulin")
        std_daily_fast_insulin = report_creator.retrieve(
            "std_daily_fast_insulin")
        assert mean_daily_fast_insulin == 0
        assert std_daily_fast_insulin == 0

    def test_save_mean_glucose_by_hour_all_series_have_same_length(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_mean_glucose_by_hour()
        series_dict = report_creator.retrieve("glucose_by_hour_series")
        unique_sizes = set([len(s) for s in series_dict.values()])
        assert len(unique_sizes) == 1

    def test_save_mean_glucose_by_hour_all_series_are_instances_of_ndarray(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_mean_glucose_by_hour()
        series_dict = report_creator.retrieve("glucose_by_hour_series")
        for series in series_dict.values():
            assert isinstance(series, np.ndarray)

    def test_save_mean_glucose_by_hour_all_series_are_numeric(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_mean_glucose_by_hour()
        series_dict = report_creator.retrieve("glucose_by_hour_series")
        for series in series_dict.values():
            assert np.issubdtype(series.dtype, np.number)

    def test_mean_glucose_by_hour_series_are_empty_on_empty_dataframe_handler(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_mean_glucose_by_hour()
        series_dict = report_creator.retrieve("glucose_by_hour_series")
        for series in series_dict.values():
            assert len(series) == 0

    def test_fill_report_succeeds_on_random_dataframe_handler(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.fill_report()

    def test_fill_report_on_empty_dataframe_handler(self,
                                                    empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.fill_report()

    def test_tir_by_hour_on_empty_dataframe_handler_does_not_raise_error(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_tir_by_hour()

    def test_tir_by_hour_on_empty_dataframe_handler_outputs_key_on_report(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_tir_by_hour()
        time_above_range_by_hour = report_creator.retrieve(
            "time_above_range_by_hour")
        time_below_range_by_hour = report_creator.retrieve(
            "time_below_range_by_hour")
        time_in_range_by_hour = report_creator.retrieve(
            "time_in_range_by_hour")
        assert time_above_range_by_hour is not None
        assert time_below_range_by_hour is not None
        assert time_in_range_by_hour is not None

    def test_tir_by_hour_on_empty_dataframe_handler_outputs_int_np_arrays(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_tir_by_hour()
        time_above_range_by_hour = report_creator.retrieve(
            "time_above_range_by_hour")
        time_below_range_by_hour = report_creator.retrieve(
            "time_below_range_by_hour")
        time_in_range_by_hour = report_creator.retrieve(
            "time_in_range_by_hour")
        assert np.issubdtype(time_above_range_by_hour.dtype, np.integer)
        assert np.issubdtype(time_below_range_by_hour.dtype, np.integer)
        assert np.issubdtype(time_in_range_by_hour.dtype, np.integer)

    def test_tir_by_hour_on_empty_dataframe_handler_arrays_sum_to_0(
            self, empty_dataframe_handler):
        report_creator = ReportCreator(empty_dataframe_handler)
        report_creator.save_tir_by_hour()
        time_above_range_by_hour = report_creator.retrieve(
            "time_above_range_by_hour")
        time_below_range_by_hour = report_creator.retrieve(
            "time_below_range_by_hour")
        time_in_range_by_hour = report_creator.retrieve(
            "time_in_range_by_hour")
        sum_by_hour = (time_above_range_by_hour
                       + time_below_range_by_hour
                       + time_in_range_by_hour)
        assert set(sum_by_hour) == {0}

    def test_tir_by_hour_values_check(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        df = random_dataframe_handler.df
        df["glucose"] = None

        df.iloc[0, (df.columns.get_loc("glucose"))] = 100
        report_creator.save_tir_by_hour()
        time_in_range_by_hour = report_creator.retrieve(
            "time_in_range_by_hour")
        time_above_range_by_hour = report_creator.retrieve(
            "time_above_range_by_hour")
        time_below_range_by_hour = report_creator.retrieve(
            "time_below_range_by_hour")
        assert time_in_range_by_hour.sum() == 1
        assert time_above_range_by_hour.sum() == 0
        assert time_below_range_by_hour.sum() == 0


    def test_tir_by_hour_on_random_dataframe_handler_does_not_raise_error(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir_by_hour()

    def test_tir_by_hour_on_random_dataframe_handler_outputs_key_on_report(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir_by_hour()
        for variant in ["in", "above", "below"]:
            retrieved = report_creator.retrieve(
                f"time_{variant}_range_by_hour")
            assert retrieved is not None

    def test_tir_by_hour_on_random_dataframe_handler_outputs_numeric_np_arrays(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir_by_hour()
        for variant in ["in", "above", "below"]:
            retrieved = report_creator.retrieve(
                f"time_{variant}_range_by_hour")
            assert isinstance(retrieved, np.ndarray)
            assert np.issubdtype(retrieved.dtype, np.number)

    def test_tir_by_hour_on_random_dataframe_handler_has_24_hours(
            self, random_dataframe_handler):
        report_creator = ReportCreator(random_dataframe_handler)
        report_creator.save_tir_by_hour()
        for variant in ["in", "above", "below"]:
            retrieved = report_creator.retrieve(
                f"time_{variant}_range_by_hour")
            assert len(retrieved) == 24


class TestJSONReportCreator:
    def test_create_report_with_random_dataframe_handler(
            self, random_dataframe_handler, textIO_buffer):
        report_creator = JSONReportCreator(random_dataframe_handler)
        report_creator.fill_report()
        report_creator.create_report(target=textIO_buffer)
        assert len(textIO_buffer.getvalue()) > 0

    def test_create_report_with_empty_dataframe_handler(
            self, empty_dataframe_handler, textIO_buffer):
        report_creator = JSONReportCreator(empty_dataframe_handler)
        report_creator.fill_report()
        report_creator.create_report(target=textIO_buffer)
        assert len(textIO_buffer.getvalue()) > 0


class TestPDFReportCreator:
    def test_create_report_with_random_dataframe_handler(
            self, random_dataframe_handler, binaryIO_buffer):
        report_creator = PDFReportCreator(random_dataframe_handler)
        report_creator.fill_report()
        report_creator.create_report(target=binaryIO_buffer)
        assert len(binaryIO_buffer.getbuffer()) > 0

    def test_create_report_with_empty_dataframe_handler(
            self, empty_dataframe_handler, binaryIO_buffer):
        report_creator = PDFReportCreator(empty_dataframe_handler)
        report_creator.fill_report()
        report_creator.create_report(target=binaryIO_buffer)
        assert len(binaryIO_buffer.getbuffer()) > 0
