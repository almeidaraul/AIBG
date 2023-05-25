import json

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends import backend_pdf
from typing import BinaryIO, TextIO, Union, Final

from .dataframe_handler import DataFrameHandler


class ReportCreator():
    """Base reporter class

    This class' methods can be split into three categories:
    1. Utility functions for manipulating the explorer object and computing
       values to be reported
    2. The get_values function which uses all utility functions to produce
       the final report dictionary
    3. The report function, which produces the final report in a specific
       format (should be overwritten by child classes)
    """

    def __init__(self, f: TextIO):
        self.explorer = DataFrameHandler(f)
        self.report_dict = {}
        self.get_values()

    def reset_df(self, day_count: int):
        """Reset df to last x days"""
        self.explorer.reset_df().last_x_days(day_count)

    def update_hba1c(self):
        """HbA1c value based on glucose readings of last 90 days"""
        self.explorer.last_x_days(90)
        glucose = self.explorer.df["glucose"]
        self.report_dict["hba1c"] = (glucose.mean()+46.7)/28.7

    def update_tir(self, lower_bound: int = 70, upper_bound: int = 180):
        """Compute time in/below/above range

        Computes total number of entries in [lo, up), (, lo) and [up,)
        (i.e., in range, below range, and above range)
        """
        glucose = self.explorer.df["glucose"]
        in_range = glucose[(glucose >= lower_bound)
                           & (glucose < upper_bound)].count()
        below_range = glucose[glucose < lower_bound].count()
        above_range = glucose[glucose >= upper_bound].count()
        self.report_dict["in_range"] = in_range
        self.report_dict["below_range"] = below_range
        self.report_dict["above_range"] = above_range

    def update_entry_count(self):
        """Compute total and average (per day) number of entries"""
        # total
        total_entries = self.explorer.count()
        self.report_dict["total_entries"] = int(total_entries)
        # per day
        entries_per_day = self.groupby_day["date"].count().mean()
        self.report_dict["entries_per_day"] = float(entries_per_day)

    def update_insulin_use(self):
        """Compute fast insulin use per day (mean and std dev)"""
        fast_per_day = self.groupby_day["fast_insulin"].sum()
        self.report_dict["mean_fast_per_day"] = fast_per_day.mean()
        self.report_dict["std_fast_per_day"] = fast_per_day.std()

    def update_glucose(self):
        """Compute mean (and std dev) glucose per hour"""
        groupby_hour = self.explorer.groupby_hour()
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
        table = self.explorer.df[list(show_columns.keys())].copy()
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
        self.groupby_day = self.explorer.groupby_day()
        self.update_entry_count()
        self.update_insulin_use()
        self.update_glucose()
        self.update_table()
        return self.report_dict

    def report(self):
        """Should be overwritten by child classes"""
        pass


class JSONReportCreator(ReportCreator):
    """ReportCreator for JSON files"""

    def report(self, target: TextIO):
        """Dump base report dict into target JSON file"""
        json.dump(self.report_dict, target)


class PDFReportCreator(ReportCreator):
    """ReportCreator for PDF files and buffers"""

    def __init__(self, f: TextIO):
        super().__init__(f)
        self.A5_FIGURE_SIZE: Final = (8.27, 5.83)

    def plot_statistics(self):
        """Plots basic statistics such as TIR and HbA1c to target PDF"""
        fig = plt.figure(figsize=self.A5_FIGURE_SIZE)
        plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, "Statistics", ha="left", va="top", fontsize=28)
        plt.text(0, 0.8, f"HbA1c (last 3 months): {self.report['hba1c']:.2f}%",
                 ha="left", va="top")
        plt.text(0, 0.7, "Last 5 days", ha="left", va="top")
        total_entries = self.report['total_entries']
        entries_per_day = self.report['entries_per_day']
        plt.text(
            0, 0.6,
            f"Total entries: {total_entries}, per day: {entries_per_day:.2f}",
            ha="left", va="top")
        fast_per_day = self.report['mean_fast_per_day']
        std_fast_per_day = self.report['std_fast_per_day']
        plt.text(
            0, 0.5,
            f"Fast insulin/day: {fast_per_day:.2f} ± {std_fast_per_day:.2f}",
            ha="left", va="top")
        plt.axis('off')

        # time in range pie chart
        plt.text(.5, 0, "Time in Range", ha="center", va="bottom", fontsize=16)

        plt.subplot2grid((2, 1), (1, 0), aspect="equal")

        labels = ["Above range", "Below range", "In range"]
        sizes = [self.report["above_range"], self.report["below_range"],
                 self.report["in_range"]]

        total = sum(sizes)
        percentages = list(map(lambda x: f"{100*x/total:.2f}%", sizes))

        colors = ["tab:red", "tab:blue", "tab:olive"]

        plt.pie(sizes, labels=percentages, colors=colors)
        plt.legend(labels, loc="best", bbox_to_anchor=(1, 0, 1, 1))
        self.pdf.savefig(fig)

    def plot_mean_glucose_per_hour(self):
        """Plots a mean glucose/hour line graph to target PDF"""
        fig = plt.figure(figsize=self.A5_FIGURE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = self.report["mean_glucose_per_hour"]["hour"]
        glucose = self.report["mean_glucose_per_hour"]["mean_glucose"]
        std = self.report["mean_glucose_per_hour"]["std_error"]
        std = list(map(lambda x: 0.0 if np.isnan(x) else x, std)) # TODO tratar nan antes
        to_pop = [i for i in range(len(hour)-1, -1, -1) if np.isnan(glucose[i])] # TODO tratar nan antes
        for i in to_pop:
            hour.pop(i)
            glucose.pop(i)
            std.pop(i)

        ax.errorbar(hour, glucose, yerr=std, fmt='-o',
                    capsize=3, elinewidth=2, capthick=2, color="royalblue",
                    ecolor="slategrey")
        ax.set_xlabel('Hour')
        ax.set_ylabel('Glucose (mg/dL)')

        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))
        for h in all_hours:
            ax.axvline(h, color="gray", linestyle="--", linewidth=.5)

        self.pdf.savefig(fig)

    def plot_table(self):
        """Plots the created table (with daily records) to target PDF"""
        columns = list(self.report['table'].keys())
        all_data = np.array([self.report['table'][k] for k in columns]).T
        rows_per_page = 20
        num_steps = len(all_data) // rows_per_page
        if rows_per_page * num_steps < len(all_data):
            num_steps += 1
        for i in range(num_steps):
            data = all_data[i*rows_per_page:(i+1)*rows_per_page]

            fig = plt.figure(figsize=self.A5_FIGURE_SIZE)
            ax = fig.add_subplot(1, 1, 1)

            ax.table(cellText=data, colLabels=columns, loc='center',
                     fontsize=14)
            ax.axis('off')

            self.pdf.savefig(fig)

    def report(self, target: BinaryIO):
        """Create PDF report to be saved in target file/buffer"""
        self.report = super().get_values()
        self.pdf = backend_pdf.PdfPages(target)

        self.plot_statistics()
        self.plot_mean_glucose_per_hour()
        self.plot_table()

        self.pdf.close()