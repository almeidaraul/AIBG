import pandas as pd
from .analyser import Analyser


class Reporter():
    """Base reporter class

    This class' methods can be split into three categories:
    1. Utility functions for manipulating the explorer and analyser objects
       and computing values to be reported
    2. The get_values function which uses all utility functions to produce
       the final report dictionary
    3. The report function, which produces the final report in the desired
       format
    """

    def __init__(self, explorer):
        self.explorer = explorer
        self.analyser = Analyser(self.explorer.df)
        self.report_dict = {}
        self.get_values()

    def reset_df(self, day_count):
        """Reset df to last x days"""
        self.explorer.reset_df().last_x_days(day_count)
        self.analyser = Analyser(self.explorer.df)

    def update_hba1c(self):
        """Compute HbA1c for last 90 days"""
        self.explorer.last_x_days(90)
        self.report_dict["hba1c"] = float(self.analyser.hba1c())

    def update_tir(self):
        """Compute time below, in and above range"""
        in_range, below_range, above_range = self.analyser.tir(70, 180)
        self.report_dict["in_range"] = float(in_range)
        self.report_dict["below_range"] = float(below_range)
        self.report_dict["above_range"] = float(above_range)

    def update_entry_count(self):
        """Compute total and average (per day) number of entries"""
        # total
        total_entries = self.analyser.count()
        self.report_dict["total_entries"] = int(total_entries)
        # per day
        entries_per_day = self.groupby_day["date"].count().mean()
        self.report_dict["entries_per_day"] = float(entries_per_day)

    def update_insulin_use(self):
        """Compute fast insulin use per day (mean and std dev)"""
        fast_per_day = self.groupby_day["fast_insulin"].sum()
        mean_fast_per_day = fast_per_day.mean()
        std_fast_per_day = fast_per_day.std()
        self.report_dict["mean_fast_per_day"] = float(mean_fast_per_day)
        self.report_dict["std_fast_per_day"] = float(std_fast_per_day)

    def update_glucose(self):
        """Compute mean (and std dev) glucose per hour"""
        groupby_hour = self.analyser.groupby_hour()
        glucose_per_hour = {
            "mean": groupby_hour["glucose"].mean(),
            "std": groupby_hour["glucose"].std(),
        }
        self.report_dict["mean_glucose_per_hour"] = {
                "mean_glucose": [
                    float(x) for x in glucose_per_hour["mean"].tolist()
                ],
                "hour": list(groupby_hour.groups.keys()),
                "std_error": [
                    float(x) for x in glucose_per_hour["std"].tolist()
                ],
                }

    def update_table(self):
        """Update table of all entries"""
        def meal_to_str(meal): return '; '.join(
                [f"{x}, {meal[x]:.1f}g" for x in meal.keys()])
        def epoch_to_datetime(e): return e.strftime('%d/%m/%y %H:%M')
        show_columns = {
            'date': 'Date',
            'glucose': 'Glucose',
            'bolus_insulin': 'Bolus',
            'correction_insulin': 'Correction',
            'basal_insulin': 'Basal',
            'meal': 'Meal',
            'carbs': 'Carbohydrates',
        }
        table = self.analyser.df[list(show_columns.keys())].copy()
        table["meal"] = table["meal"].apply(meal_to_str)
        numeric_columns = ["glucose", "carbs", "bolus_insulin",
                           "correction_insulin", "basal_insulin"]
        for col in numeric_columns:
            table[col] = table[col].fillna(0).apply(lambda x: int(x))
            table[col] = table[col].astype(str).replace(['0'], '')
        table["date"] = table["date"].apply(epoch_to_datetime)
        # reverse order (recent entries first)
        table = table.rename(columns=show_columns)[::-1].reset_index(drop=True)
        self.report_dict["table"] = table

    def get_values(self):
        """Compute all necessary information"""
        self.update_hba1c()
        self.reset_df(15)
        self.update_tir()
        self.reset_df(5)
        self.groupby_day = self.analyser.groupby_day()
        self.update_entry_count()
        self.update_insulin_use()
        self.update_glucose()
        self.update_table()
        return self.report_dict

    def report(self):
        """Should be overwritten by child classes"""
        pass
