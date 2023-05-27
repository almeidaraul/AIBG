import json

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends import backend_pdf
from typing import BinaryIO, TextIO, Final

from .dataframe_handler import DiaguardCSVParser, DataFrameHandler


class ReportCreator():
    """Base report creator class

    This class' methods can be split into three categories:
    1.  Utility functions for manipulating the DataFrameHandler object and
        computing/storing values to be reported
    2.  The fill_report function which uses all utility functions to store
        all data in the final report
    3.  The create_report function which produces the final report in a
        specific format (overwritten by child classes)
    """

    def __init__(self, f: TextIO):
        df = DiaguardCSVParser(f).parse_csv()
        self.df_handler = DataFrameHandler(df)
        print(self.df_handler.df.info())
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
        glucose = self.df_handler.df["glucose"]
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
        total_entries: int = self.df_handler.count()
        entries_per_day = self.df_handler.groupby_day()["date"].count().mean()
        self.store("total_entries", total_entries)
        self.store("entries_per_day", entries_per_day)

    def save_fast_insulin_use(self):
        """Compute and store daily fast insulin use (mean and std dev)"""
        fast_insulin_sum = self.df_handler.groupby_day()["fast_insulin"].sum()
        mean_fast_insulin_per_day: float = fast_insulin_sum.mean()
        std_fast_insulin_per_day: float = fast_insulin_sum.std()
        self.store("mean_fast_insulin_per_day", mean_fast_insulin_per_day)
        self.store("std_fast_insulin_per_day", std_fast_insulin_per_day)

    def save_mean_glucose_by_hour(self):
        """Compute and store mean and std dev of glucose by hour"""
        df = self.df_handler.df[["date", "glucose"]].dropna()
        glucose_by_hour = df.groupby(df["date"].dt.hour)
        glucose_by_hour_series = {
            "mean_glucose": glucose_by_hour.mean().fillna(0)["glucose"].values,
            "hour": glucose_by_hour.groups.keys(),
            "std_error": glucose_by_hour.std().fillna(0)["glucose"].values,
        }
        self.store("glucose_by_hour_series", glucose_by_hour_series)

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
            df[c] = df[c].fillna(0).apply(lambda x: str(x) if x != 0 else '')
        # reverse order (recent entries first)
        df = df.rename(
            columns=columns_display_names)[::-1].reset_index(drop=True)
        self.store("entries_dataframe", df)

    def fill_report(self):
        """Compute and store all information to be reported"""
        self.save_hba1c()
        self.reset_df(15)
        self.save_tir()
        self.reset_df(5)
        self.save_entry_count()
        self.save_fast_insulin_use()
        self.save_mean_glucose_by_hour()
        self.save_entries_df()

    def create_report(self):
        """Must be overwritten by child classes"""
        pass


class JSONReportCreator(ReportCreator):
    """ReportCreator for JSON files"""

    def create_report(self, target: TextIO):
        """Dump base report dict into target JSON file"""
        json.dump(self.report_as_dict, target)


class PDFReportCreator(ReportCreator):
    """ReportCreator for PDF files"""

    def __init__(self, f: TextIO):
        super().__init__(f)
        self.A5_FIGURE_SIZE: Final = (8.27, 5.83)
        self.PAGE_SIZE: Final = self.A5_FIGURE_SIZE

    def write_statistics_page(self):
        """Write basic statistics such as Time in Range and HbA1c"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, "Statistics", ha="left", va="top", fontsize=28)
        hba1c_value = self.report_as_dict["hba1c"]
        plt.text(0, 0.8, f"HbA1c (last 3 months): {hba1c_value:.2f}%",
                 ha="left", va="top")
        plt.text(0, 0.7, "Last 5 days", ha="left", va="top")
        total_entries = self.report_as_dict["total_entries"]
        entries_per_day = self.report_as_dict["entries_per_day"]
        plt.text(
            0, 0.6,
            f"Total entries: {total_entries}, per day: {entries_per_day:.2f}",
            ha="left", va="top")
        fast_per_day = self.report_as_dict["mean_fast_insulin_per_day"]
        std_fast_per_day = self.report_as_dict["std_fast_insulin_per_day"]
        plt.text(
            0, 0.5,
            f"Fast insulin/day: {fast_per_day:.2f} ± {std_fast_per_day:.2f}",
            ha="left", va="top")
        plt.axis("off")

        # time in range pie chart
        plt.text(.5, 0, "Time in Range", ha="center", va="bottom", fontsize=16)

        plt.subplot2grid((2, 1), (1, 0), aspect="equal")

        labels = ["Above range", "Below range", "In range"]
        sizes = [self.report_as_dict["time_above_range"],
                 self.report_as_dict["time_below_range"],
                 self.report_as_dict["time_in_range"]]

        total = sum(sizes)
        percentages = list(map(lambda x: f"{100*x/total:.2f}%", sizes))

        colors = ["tab:red", "tab:blue", "tab:olive"]

        plt.pie(sizes, labels=percentages, colors=colors)
        plt.legend(labels, loc="best", bbox_to_anchor=(1, 0, 1, 1))
        self.pdf.savefig(fig)

    def plot_glucose_by_hour_graph(self):
        """Plot a mean glucose by hour line graph"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = self.report_as_dict["glucose_by_hour_series"]["hour"]
        glucose = self.report_as_dict["glucose_by_hour_series"]["mean_glucose"]
        std = self.report_as_dict["glucose_by_hour_series"]["std_error"]

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
        columns = list(self.report_as_dict["entries_dataframe"].keys())
        entries_nparray = np.array(self.report_as_dict["entries_dataframe"])
        rows_per_page = 20
        num_steps = len(entries_nparray) // rows_per_page
        if rows_per_page * num_steps < len(entries_nparray):
            num_steps += 1
        for i in range(num_steps):
            data = entries_nparray[i*rows_per_page:(i+1)*rows_per_page]

            fig = plt.figure(figsize=self.PAGE_SIZE)
            ax = fig.add_subplot(1, 1, 1)

            ax.table(cellText=data, colLabels=columns, loc="center",
                     fontsize=14)
            ax.axis("off")

            self.pdf.savefig(fig)

    def create_report(self, target: BinaryIO):
        """Create PDF report to be saved in target file/buffer"""
        self.pdf = backend_pdf.PdfPages(target)

        self.write_statistics_page()
        self.plot_glucose_by_hour_graph()
        self.write_entries_dataframe()

        self.pdf.close()
