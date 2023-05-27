# from glikoz import report_creator


class TestReportCreator:
    def test_save_hba1c_where_glucose_is_empty():
        # TODO what value to store when there are no glucose entries?
        pass

    def test_save_hba1c_where_glucose_is_not_empty():
        pass

    def test_save_tir_where_bound_interval_is_empty():
        pass

    def test_save_tir_where_bound_interval_is_not_empty():
        pass

    def test_save_tir_where_glucose_is_empty():
        pass

    def test_save_entry_count_is_numeric():
        pass

    def test_save_entry_mean_by_day_where_there_are_entries():
        pass

    def test_save_entry_mean_by_day_where_there_are_no_entries():
        pass

    def test_save_mean_fast_insulin_by_day_is_numeric():
        pass

    def test_save_std_fast_insulin_by_day_is_numeric():
        pass

    def test_save_fast_insulin_by_day_where_are_no_entries():
        pass

    def test_save_mean_glucose_by_hour_all_series_have_same_length():
        pass

    def test_save_mean_glucose_by_hour_all_series_are_numeric():
        pass
