import json

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends import backend_pdf
from typing import BinaryIO, TextIO, Final

from .dataframe_handler import DataFrameHandler


class ReportCreator:
    """Base report creator class

    This class' methods can be split into three categories:
    1.  Utility functions for manipulating the DataFrameHandler object and
        computing/storing values to be reported
    2.  The fill_report function which uses all utility functions to store
        all data in the final report
    3.  The create_report function which produces the final report in a
        specific format (overwritten by child classes)
    """

    def __init__(self, dataframe_handler: DataFrameHandler):
        self.df_handler = dataframe_handler
        self.report_as_dict = {}

    def reset_df(self, day_count: int = None):
        """Remove filters from the DataFrame

        Arguments:
        - day_count: if provided, the DataFrame is filtered with the
        DataFrameHandler's last_x_days function (with x = day_count)
        """
        self.df_handler.reset_df().last_x_days(day_count)

    def store(self, key: str, value: any):
        """Store value in report, indexed by key"""
        self.report_as_dict[key] = value

    def retrieve(self, key: str, default_value: any = None):
        """Retrieve value from report, or default_value if key missing"""
        return self.report_as_dict.get(key, default_value)

    def save_hba1c(self):
        """
        Compute and store HbA1c value based on glucose readings of most recent
        90 days

        This function filters the DataFrame to the most recent 90 days, but it
        is the user's responsibility to undo this filter if necessary.

        The HbA1c estimative depends on the estimated average glucose (mg/dL)
        from the last three months, as described in the paper "Translating the
        A1C assay into estimated average glucose values" by Nathan DM,
        Kuenen J, Borg R, Zheng H, Schoenfeld D, and Heine RJ (2008) (Diabetes
        Care. 31 (8): 1473-78).
        """
        self.df_handler.last_x_days(90)
        glucose = self.df_handler.df["glucose"].dropna()
        if glucose.empty:
            hba1c = None
        else:
            hba1c = (glucose.mean()+46.7)/28.7
        self.store("hba1c", hba1c)

    def save_tir(self, lower_bound: int = 70, upper_bound: int = 180):
        """Compute and store time in/below/above range

        The time in range is the number of entries in the intervals [lo, up),
        (, lo) and [up,) (i.e., in range, below range, and above range)
        """
        glucose = self.df_handler.df["glucose"]
        in_range = glucose[(glucose >= lower_bound)
                           & (glucose < upper_bound)].count()
        below_range = glucose[glucose < lower_bound].count()
        above_range = glucose[glucose >= upper_bound].count()
        self.store("time_in_range", in_range)
        self.store("time_below_range", below_range)
        self.store("time_above_range", above_range)

    def save_entry_count(self):
        """Compute and store total and mean daily number of entries"""
        if self.df_handler.df.empty:
            entry_count = 0
            mean_daily_entry_count = 0.
        else:
            entry_count = self.df_handler.count()
            dates_grouped_by_day = self.df_handler.groupby_day()["date"]
            mean_daily_entry_count = dates_grouped_by_day.count().mean()
        self.store("entry_count", entry_count)
        self.store("mean_daily_entry_count", mean_daily_entry_count)

    def save_fast_insulin_use(self):
        """Compute and store daily fast insulin use (mean and std dev)"""
        if self.df_handler.df.empty:
            mean_daily_fast_insulin = 0.
            std_daily_fast_insulin = 0.
        else:
            groupby = self.df_handler.groupby_day()
            fast_insulin_sum = groupby["fast_insulin"].sum()
            mean_daily_fast_insulin = fast_insulin_sum.mean()
            std_daily_fast_insulin = fast_insulin_sum.std()
        self.store("mean_daily_fast_insulin", mean_daily_fast_insulin)
        self.store("std_daily_fast_insulin", std_daily_fast_insulin)

    def save_mean_glucose_by_hour(self):
        """Compute and store mean and std dev of glucose by hour"""
        df = self.df_handler.df[["date", "glucose"]].dropna()
        if df.empty:
            glucose_by_hour_series = {
                "mean_glucose": np.array([]),
                "hour": np.array([]),
                "std_error": np.array([])
            }
        else:
            glucose_by_hour = df.groupby(df["date"].dt.hour)
            mean_glucose = glucose_by_hour.mean().fillna(0)["glucose"]
            hour = list(glucose_by_hour.groups.keys())
            std_error = glucose_by_hour.std().fillna(0)["glucose"]
            glucose_by_hour_series = {
                "mean_glucose": mean_glucose.values,
                "hour": np.array(hour),
                "std_error": std_error.values,
            }
        self.store("glucose_by_hour_series", glucose_by_hour_series)

    def save_tir_by_hour(self, lower_bound: int = 70, upper_bound: int = 180):
        """Compute and store the time in range for each hour of the day"""
        time_above_range_by_hour = np.array([0]*24)
        time_below_range_by_hour = np.array([0]*24)
        time_in_range_by_hour = np.array([0]*24)
        if not self.df_handler.df.empty:
            # return self.df.groupby(self.df["date"].dt.hour)
            glucose = self.df_handler.df["glucose"].dropna()
            groupby_param = self.df_handler.df["date"].dt.hour
            time_above_range_by_hour_count = glucose[glucose >= upper_bound
                ].groupby(groupby_param).count()
            for hour, count in time_above_range_by_hour_count.iteritems():
                time_above_range_by_hour[hour] = count
            time_below_range_by_hour_count = glucose[glucose < lower_bound
                ].groupby(groupby_param).count()
            for hour, count in time_below_range_by_hour_count.iteritems():
                time_below_range_by_hour[hour] = count
            time_in_range_by_hour_count = glucose[
                (glucose >= lower_bound) & (glucose < upper_bound)
                ].groupby(groupby_param).count()
            for hour, count in time_in_range_by_hour_count.iteritems():
                time_in_range_by_hour[hour] = count
        self.store("time_above_range_by_hour", time_above_range_by_hour)
        self.store("time_below_range_by_hour", time_below_range_by_hour)
        self.store("time_in_range_by_hour", time_in_range_by_hour)

    def save_entries_df(self):
        """Compute and store DataFrame of all entries"""
        def meal_to_str(meal): return "; ".join(
                [f"{x}, {meal[x]:.1f}g" for x in meal.keys()])

        def epoch_to_datetime(e): return e.strftime("%d/%m/%y %H:%M")

        columns_display_names = {
            "date": "Date",
            "glucose": "Glucose",
            "bolus_insulin": "Bolus",
            "correction_insulin": "Correction",
            "basal_insulin": "Basal",
            "meal": "Meal",
            "carbs": "Carbohydrates",
        }
        number_columns = ["glucose", "carbs", "bolus_insulin",
                          "correction_insulin", "basal_insulin"]

        df = self.df_handler.df[list(columns_display_names.keys())].copy()
        df["meal"] = df["meal"].apply(meal_to_str)
        df["date"] = df["date"].apply(epoch_to_datetime)
        for c in number_columns:
            df[c] = df[c].fillna(0).apply(
                lambda x: f"{int(x)}" if x != 0 else '')
        # reverse order (recent entries first)
        df = df.rename(
            columns=columns_display_names)[::-1].reset_index(drop=True)
        self.store("entries_dataframe", df)

    def fill_report(self):
        """Compute and store all information to be reported"""
        self.save_hba1c()
        self.reset_df(15)
        self.save_tir()
        self.save_entry_count()
        self.save_fast_insulin_use()
        self.save_mean_glucose_by_hour()
        self.save_tir_by_hour()
        self.reset_df(5)
        self.save_entries_df()

    def create_report(self):
        """Must be overwritten by child classes"""
        pass


class JSONReportCreator(ReportCreator):
    """ReportCreator for JSON files"""

    def create_report(self, target: TextIO):
        """Dump base report dict into target JSON file"""
        entries_df = self.retrieve("entries_dataframe")
        self.store("entries_dataframe", entries_df.to_json())
        glucose_by_hour_series = self.retrieve("glucose_by_hour_series")
        for series in glucose_by_hour_series.keys():
            as_list = list(glucose_by_hour_series[series])
            as_python_int = map(int, as_list)
            glucose_by_hour_series[series] = list(as_python_int)
        self.store("glucose_by_hour_series", glucose_by_hour_series)
        for tir_variant in ["in", "above", "below"]:
            key = f"time_{tir_variant}_range_by_hour"
            value = self.retrieve(key)
            self.store(key, list(map(int, list(value))))
        for key, value in self.report_as_dict.items():
            if value is not None and np.issubdtype(type(value), np.number):
                self.report_as_dict[key] = int(value)
        print(self.report_as_dict)
        json.dump(self.report_as_dict, target)


class PDFReportCreator(ReportCreator):
    """ReportCreator for PDF files"""

    def __init__(self, dataframe_handler: DataFrameHandler):
        super().__init__(dataframe_handler)
        self.A5_FIGURE_SIZE: Final = (8.27, 5.83)
        self.PAGE_SIZE: Final = self.A5_FIGURE_SIZE

    def write_statistics_page(self):
        """Write basic statistics such as Time in Range and HbA1c"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, "Statistics", ha="left", va="top", fontsize=28)
        hba1c_value = self.retrieve("hba1c")
        if hba1c_value is None:
            hba1c_as_str = "N/A"
        else:
            hba1c_as_str = f"{hba1c_value:.2f}"
        plt.text(0, 0.8, f"HbA1c (last 3 months): {hba1c_as_str}%",
                 ha="left", va="top")
        plt.text(0, 0.7, "Last 15 days", ha="left", va="top")
        entry_count = self.retrieve("entry_count")
        mean_daily_entry_count = self.retrieve("mean_daily_entry_count")
        plt.text(
            0, 0.6,
            (f"Total entries: {entry_count},"
             + f" per day: {mean_daily_entry_count:.2f}"),
            ha="left", va="top")
        fast_per_day = self.retrieve("mean_daily_fast_insulin")
        std_fast_per_day = self.retrieve("std_daily_fast_insulin")
        plt.text(
            0, 0.5,
            f"Fast insulin/day: {fast_per_day:.2f} ± {std_fast_per_day:.2f}",
            ha="left", va="top")
        plt.axis("off")

        # time in range pie chart
        plt.text(.5, 0, "Time in Range", ha="center", va="bottom", fontsize=16)

        plt.subplot2grid((2, 1), (1, 0), aspect="equal")

        labels = ["Above range", "Below range", "In range"]
        sizes = [self.retrieve("time_above_range"),
                 self.retrieve("time_below_range"),
                 self.retrieve("time_in_range")]

        total = sum(sizes)
        if total == 0:
            plt.text(.7, 0, "Time in Range graph not available", ha="center",
                     va="bottom", fontsize=14)
        else:
            percentages = list(map(lambda x: f"{100*x/total:.2f}%", sizes))

            colors = ["tab:red", "tab:blue", "tab:olive"]

            plt.pie(sizes, labels=percentages, colors=colors)
            plt.legend(labels, loc="best", bbox_to_anchor=(1, 0, 1, 1))
        self.pdf.savefig(fig)

    def plot_glucose_by_hour_graph(self):
        """Plot a mean glucose by hour line graph"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = self.retrieve("glucose_by_hour_series")["hour"]
        glucose = self.retrieve("glucose_by_hour_series")["mean_glucose"]
        std = self.retrieve("glucose_by_hour_series")["std_error"]

        ax.errorbar(hour, glucose, yerr=std, fmt="-o",
                    capsize=3, elinewidth=2, capthick=2, color="royalblue",
                    ecolor="slategrey")
        ax.set_xlabel("Hour")
        ax.set_ylabel("Glucose (mg/dL)")

        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))
        for h in all_hours:
            ax.axvline(h, color="gray", linestyle="--", linewidth=.5)

        self.pdf.savefig(fig)

    def write_entries_dataframe(self):
        """Plot the entries DataFrame"""
        columns_display_names = {
            "Date": "Date",
            "Glucose": "Gluc",
            "Bolus": "Bolus",
            "Correction": "Corr.",
            "Basal": "Basal",
            "Meal": "Meal",
            "Carbohydrates": "Carbs",
        }
        columns = list(map(lambda x: columns_display_names.get(x),
                           self.retrieve("entries_dataframe").keys()))
        colWidths = [.15, .05, .05, .05, .05, 0.75, 0.05]
        entries_nparray = np.array(self.retrieve("entries_dataframe"))
        if len(entries_nparray) == 0:
            return None
        curr_start = 0
        curr_date = entries_nparray[0][0].split(' ')[0]
        intervals = []
        for i in range(len(entries_nparray)):
            new_date = entries_nparray[i][0].split(' ')[0]
            if new_date != curr_date:
                intervals.append((curr_start, i-1))
                curr_date = new_date
                curr_start = i
        for a, b in intervals:
            data = entries_nparray[a:b+1]

            fig = plt.figure(figsize=self.PAGE_SIZE)
            ax = fig.add_subplot(1, 1, 1)

            table = ax.table(cellText=data, colLabels=columns, loc="center",
                             fontsize=16, colWidths=colWidths)
            table.scale(1, 2)
            table.auto_set_font_size()
            ax.axis("off")

            self.pdf.savefig(fig)

    def plot_tir_by_hour_graph(self):
        """Plot a TIR by hour line graph"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = np.array(range(24))
        in_range = self.retrieve("time_in_range_by_hour").astype("float64")
        above_range = self.retrieve("time_above_range_by_hour").astype("float64")
        below_range = self.retrieve("time_below_range_by_hour").astype("float64")
        total = in_range + above_range + below_range
        for i in range(24):
            if total[i] > 0:
                in_range[i] /= total[i]
                above_range[i] /= total[i]
                below_range[i] /= total[i]

        width = .7
        below_range_bar = ax.bar(hour, below_range, width, label="Below Range",
                                 bottom=np.zeros(24), color="tab:blue")
        in_range_bar = ax.bar(hour, in_range, width, label="In Range",
                              bottom=below_range, color="tab:olive")
        above_range_bar = ax.bar(hour, above_range, width, label="Above Range",
                                 bottom=below_range+in_range, color="tab:red")

        ax.set_title("Time in Range per Hour")
        ax.legend(fontsize="xx-small", framealpha=.8)
        ax.set_xlabel("Hour")
        ax.set_ylabel("Percentage (%)")

        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))

        ax.set_yticks(list(map(lambda x: x/10, range(11))))
        ax.set_yticklabels(list(range(0, 110, 10)))

        self.pdf.savefig(fig)

    def create_report(self, target: BinaryIO):
        """Create PDF report to be saved in target file/buffer"""
        self.pdf = backend_pdf.PdfPages(target)

        self.write_statistics_page()
        self.plot_glucose_by_hour_graph()
        self.plot_tir_by_hour_graph()
        self.write_entries_dataframe()

        self.pdf.close()
