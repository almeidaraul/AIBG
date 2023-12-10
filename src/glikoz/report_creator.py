import json

import datetime as dt
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
        self.GRAPH_DAYS = 15

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
        glucose = self.df_handler.df["glucose"].dropna()
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
            glucose_entry_count = self.df_handler.df["glucose"].dropna(
                ).count()
            dates_grouped_by_day = self.df_handler.groupby_day()["date"]
            glucose_grouped_by_day = (self.df_handler.groupby_day()
                                      )["glucose"]
            mean_daily_entry_count = dates_grouped_by_day.count().mean()
            mean_daily_glucose_entry_count = glucose_grouped_by_day.count(
                ).mean()
        self.store("entry_count", entry_count)
        self.store("glucose_entry_count", glucose_entry_count)
        self.store("mean_daily_entry_count", mean_daily_entry_count)
        self.store("mean_daily_glucose_entry_count",
                   mean_daily_glucose_entry_count)

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
                "max_glucose": np.array([]),
                "min_glucose": np.array([]),
            }
        else:
            glucose_by_hour = df.groupby(df["date"].dt.hour)
            mean_glucose = glucose_by_hour.mean().fillna(0)["glucose"]
            max_glucose = glucose_by_hour.max().fillna(0)["glucose"]
            min_glucose = glucose_by_hour.min().fillna(0)["glucose"]
            hour = list(glucose_by_hour.groups.keys())
            glucose_by_hour_series = {
                "mean_glucose": mean_glucose.values,
                "hour": np.array(hour),
                "max_glucose": max_glucose.values,
                "min_glucose": min_glucose.values
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
                                                     ].groupby(groupby_param
                                                               ).count()
            for hour, count in time_above_range_by_hour_count.iteritems():
                time_above_range_by_hour[hour] = count
            time_below_range_by_hour_count = glucose[glucose < lower_bound
                                                     ].groupby(groupby_param
                                                               ).count()
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

    def save_low_counts(
            self,
            threshold: int = 70,
            distribution_indexes: list = [
                (20, 30), (31, 40), (41, 50), (51, 60), (61, 69)]):
        """
        Compute amount of low blood sugar entries and distribution of their
        values

        Arguments
        - threshold: limit for considering an entry a low. Values < threshold
        are considered lows
        - distribution_indexes: list of tuples of the ranges to be considered
        in the distribution. The distribution represented by the tuple (a, b)
        will indicate how many lows are in the range [a, b].
        """
        low_count = 0
        distributions = {idx: 0 for idx in distribution_indexes}
        if not self.df_handler.df.empty:
            glucose = self.df_handler.df["glucose"].dropna()
            low_count = (glucose < threshold).sum()
            for a, b in distributions:
                count = ((glucose >= a) & (glucose <= b)).sum()
                distributions[(a, b)] = count
        self.store("low_bg_count", low_count)
        self.store("low_bg_distributions", distributions)

    def save_mean_daily_low_rate(self, threshold=70):
        """Compute and store mean daily low rate

        That is, the mean (across days) rate of entries with low
        blood sugars"""
        mean_daily_low_rate = 0.
        daily_low_rate_sum = 0.
        daily_low_rate_count = 0
        if not self.df_handler.df.empty:
            groupby = self.df_handler.groupby_day()
            for _, group in groupby:
                glucose = group["glucose"].dropna()
                total = glucose.count()
                low = (glucose < threshold).sum()
                if total > 0:
                    daily_low_rate_sum += low/total
                daily_low_rate_count += 1
            mean_daily_low_rate = daily_low_rate_sum / daily_low_rate_count
        self.store("mean_daily_low_rate", mean_daily_low_rate)

    def save_very_low_count_and_rate(self, threshold=55):
        """Compute and store very low glucose count and rate"""
        very_low_count = 0
        very_low_rate = 0.
        if not self.df_handler.df.empty:
            glucose = self.df_handler.df["glucose"].dropna()
            total = glucose.count()
            very_low_count = (glucose < threshold).sum()
            very_low_rate = very_low_count/total
        self.store("very_low_bg_count", very_low_count)
        self.store("very_low_bg_rate", very_low_rate)

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
            # "meal": "Meal",
            "carbs": "Carbohydrates",
        }
        number_columns = ["glucose", "carbs", "bolus_insulin",
                          "correction_insulin", "basal_insulin"]

        df = self.df_handler.df[list(columns_display_names.keys())].copy()
        # df["meal"] = df["meal"].apply(meal_to_str)
        df["date"] = df["date"].apply(epoch_to_datetime)
        for c in number_columns:
            df[c] = df[c].fillna(0).apply(
                lambda x: f"{int(x)}" if x != 0 else '')
        self.store("entries_dataframe", df)

    def fill_report(self):
        """Compute and store all information to be reported"""
        self.save_hba1c()
        self.reset_df(self.GRAPH_DAYS)
        self.save_tir()
        self.save_entry_count()
        self.save_fast_insulin_use()
        self.save_mean_glucose_by_hour()
        self.save_tir_by_hour()
        self.save_low_counts()
        self.save_mean_daily_low_rate()
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

    def write_statistics_page(self, show_hba1c: bool = True):
        """Write basic statistics such as Time in Range and HbA1c"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, f"Report for the last {self.GRAPH_DAYS} days",
                 ha="left", va="top", fontsize=34)
        plt.text(0, .7, "Statistics", ha="left", va="top", fontsize=28)
        if show_hba1c:
            hba1c_value = self.retrieve("hba1c")
            if hba1c_value is None:
                hba1c_as_str = "N/A"
            else:
                hba1c_as_str = f"{hba1c_value:.2f}"
            plt.text(0, 0.5, f"HbA1c (last 3 months): {hba1c_as_str}%",
                     ha="left", va="top")
        entry_count = self.retrieve("entry_count")
        mean_daily_entry_count = self.retrieve("mean_daily_entry_count")
        plt.text(
            0, 0.4,
            (f"Total entries: {entry_count},"
             + f" per day: {mean_daily_entry_count:.2f}"),
            ha="left", va="top")
        fast_per_day = self.retrieve("mean_daily_fast_insulin")
        std_fast_per_day = self.retrieve("std_daily_fast_insulin")
        plt.text(
            0, 0.3,
            f"Fast insulin/day: {fast_per_day:.2f} ± {std_fast_per_day:.2f}",
            ha="left", va="top")
        sizes = [self.retrieve("time_above_range"),
                 self.retrieve("time_below_range"),
                 self.retrieve("time_in_range")]
        total = sum(sizes)
        plt.axis("off")

        # time in range pie chart
        plt.text(.5, 0, "Time in Range", ha="center", va="bottom", fontsize=16)

        plt.subplot2grid((2, 1), (1, 0), aspect="equal")

        labels = ["Above range", "Below range", "In range"]
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

        series_dict = self.retrieve("glucose_by_hour_series")
        hour = series_dict["hour"]
        glucose = series_dict["mean_glucose"]
        mx_err = series_dict["max_glucose"] - glucose
        mn_err = glucose - series_dict["min_glucose"]
        mn_glucose = min(series_dict["min_glucose"])
        mx_glucose = max(series_dict["max_glucose"])

        ax.errorbar(hour, glucose, yerr=[mn_err, mx_err], fmt="-o",
                    capsize=3, elinewidth=2, capthick=2, color="royalblue",
                    ecolor="slategrey")
        ax.set_title("Mean Glucose by Hour*")
        ax.text(-.15, -.13, "*Error bars indicate maximum and minimum values",
                transform=ax.transAxes, ha="left", va="bottom")
        ax.set_xlabel("Hour")
        ax.set_ylabel("Glucose (mg/dL)")

        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))
        for h in all_hours:
            ax.axvline(h, color="gray", linestyle="--", linewidth=.5)

        glucose_lo = 25*(np.floor(mn_glucose/25))
        glucose_hi = 25*(np.floor(mx_glucose/25)+1)
        glucose_ticks = list(range(int(glucose_lo), int(glucose_hi), 25))
        ax.set_yticks(glucose_ticks)
        for t in ax.get_yticks():
            ax.axhline(t, color="gray", linestyle="--", linewidth=.5)

        self.pdf.savefig(fig)

    def plot_daily_glucose_graph(self, data):
        """Plot a glucose graph for a day in the entires DataFrame"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        ax.set_title("Glucose by Hour")
        ax.set_xlabel("Time")
        ax.set_ylabel("Glucose (mg/dL)")

        time, glucose = list(data[:, 0]), data[:, 1]
        to_remove = [i for i in range(len(glucose)) if glucose[i] == '']
        to_remove.reverse()
        for i in to_remove:
            glucose = np.delete(glucose, i)
            time.pop(i)
        time = np.array(list(map(
            lambda s: dt.datetime.strptime(s, "%d/%m/%y %H:%M").time(), time)))
        glucose = glucose.astype(np.dtype("int64"))
        ax.plot(time, glucose)

        """
        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))
        for h in all_hours:
            ax.axvline(h, color="gray", linestyle="--", linewidth=.5)
        """

        glucose_lo = min(glucose)
        glucose_hi = max(glucose)
        print(glucose)
        glucose_ticks = list(range(int(glucose_lo), int(glucose_hi), 25))
        ax.set_yticks(glucose_ticks)
        for t in ax.get_yticks():
            ax.axhline(t, color="gray", linestyle="--", linewidth=.5)

        self.pdf.savefig(fig)

    def write_entries_table(self, data):
        """Plot the table for a day in the entries DataFrame"""
        columns_display_names = {
            "date": "Date",
            "glucose": "Glucose (mg/dL)",
            "bolus_insulin": "Bolus (iu)",
            "correction_insulin": "Correction (iu)",
            "basal_insulin": "Basal (iu)",
            "carbs": "Carbohydrates (g)",
            "bolus_insulin": "Bolus (iu)",
            "correction_insulin": "Correction (iu)",
            "basal_insulin": "Basal (iu)",
            "carbs": "Carbohydrates (g)",
        }
        columns = list(map(lambda x: columns_display_names.get(x),
                           self.retrieve("entries_dataframe").keys()))
        colWidths = [.2, .16, .16, .16, .16, .16]

        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        table = ax.table(cellText=data, colLabels=columns, loc="center",
                         fontsize=16, colWidths=colWidths)
        table.scale(1, 2)
        table.auto_set_font_size()
        ax.axis("off")

        for i, c in enumerate(columns):
            ha = "left" if i == 0 else "center"
            ax.annotate(
                xy=(sum(colWidths[:i]), len(data)),
                text=c,
                ha=ha,
                va="bottom",
                weight="bold"
            )

        self.pdf.savefig(fig)

    def write_entries_dataframe(self):
        """Plot the entries DataFrame"""
        # start page: "entries in the last 15 days"
        fig = plt.figure(figsize=self.PAGE_SIZE)
        plt.subplot2grid((1, 1), (0, 0))
        plt.text(0, 1, "Entries in the last 15 days", fontsize=34)
        plt.axis("off")
        self.pdf.savefig(fig)

        # find index intervals corresponding to each day
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
        intervals.append((curr_start, len(entries_nparray)-1))
        for a, b in intervals:
            self.write_entries_table(entries_nparray[a:b+1])

    def plot_tir_by_hour_graph(self):
        """plot a tir by hour line graph"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = np.array(range(24))
        in_range = self.retrieve("time_in_range_by_hour").astype("float64")
        above_range = self.retrieve("time_above_range_by_hour"
                                    ).astype("float64")
        below_range = self.retrieve("time_below_range_by_hour"
                                    ).astype("float64")
        total = in_range + above_range + below_range
        for i in range(24):
            if total[i] > 0:
                in_range[i] /= total[i]
                above_range[i] /= total[i]
                below_range[i] /= total[i]

        width = .7
        ax.bar(hour, below_range, width, label="below range",
               bottom=np.zeros(24), color="tab:blue")
        ax.bar(hour, in_range, width, label="in range",
               bottom=below_range, color="tab:olive")
        ax.bar(hour, above_range, width, label="above range",
               bottom=below_range+in_range, color="tab:red")

        ax.set_title("Time in Range by Hour")
        ax.legend(fontsize="xx-small", framealpha=.8)
        ax.set_xlabel("Hour")
        ax.set_ylabel("Percentage (%)")

        all_hours = list(range(1, 24)) + [0]
        ax.set_xticks(all_hours)
        ax.set_xticklabels(list(map(lambda h: f"{h:0=2d}", all_hours)))

        ax.set_yticks(list(map(lambda x: x/10, range(11))))
        ax.set_yticklabels(list(range(0, 110, 10)))

        self.pdf.savefig(fig)

    def plot_lows_report(self):
        """plot a page with information on low blood sugars"""
        fig = plt.figure(figsize=self.PAGE_SIZE)
        plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, "Hypoglycemia-Related Statistics", ha="left", va="top",
                 fontsize=28)
        low_count = self.retrieve("low_bg_count")
        mean_daily_low_rate = self.retrieve("mean_daily_low_rate")
        plt.text(
            0, 0.7,
            f"Hypoglycemia episodes: {low_count}",
            ha="left", va="top")
        plt.text(
            0, 0.6,
            f"Mean daily hypoglycemia rate: {100*mean_daily_low_rate:.2f}%",
            ha="left", va="top")

        very_low_count = self.retrieve("very_low_bg_count")
        very_low_rate = 100*self.retrieve("very_low_bg_rate")

        plt.text(
            0, 0.5,
            (f"Very low hypoglycemia episodes (below 55): {very_low_count}"
             + f" ({very_low_rate:.2f}% of all entries)"),
            ha="left", va="top"
        )

        plt.axis("off")

        plt.text(.5, 0,
                 "Hypoglycemia Distribution",
                 ha="center", va="bottom", fontsize=16)

        ax = plt.subplot2grid((2, 1), (1, 0), aspect="auto")
        # ax = fig.add_subplot(1, 1, 1)
        distributions = self.retrieve("low_bg_distributions", {})

        labels = [f"{a}-{b}" for a, b in distributions]
        ax.set_xticks(range(len(labels)), labels)
        mn, mx = min(distributions.values()), max(distributions.values())
        ax.set_ylim(bottom=0, top=mx+20)
        ax.set_yticks(range(mn, mx+20, max(1, (mn+mx+20)//5)))
        ax.set_xlabel("Glucose Range (mg/dl - mg/dl)")
        ax.set_ylabel("Hypoglycemia Count")
        for i, ((a, b), count) in enumerate(distributions.items()):
            ax.bar(i, count, color="tab:blue", label=count)
            if count != 0:
                ax.text(i, count, count, ha="center", va="bottom",
                        fontsize=10)
        ax.tick_params(axis='x', which='major', labelsize=8)
        self.pdf.savefig(fig)

    def create_report(self, target: BinaryIO):
        """Create PDF report to be saved in target file/buffer"""
        self.pdf = backend_pdf.PdfPages(target)

        for days in [15]:
            self.save_hba1c()
            self.GRAPH_DAYS = days
            self.reset_df(self.GRAPH_DAYS)
            self.save_tir()
            self.save_entry_count()
            self.save_fast_insulin_use()
            self.save_mean_glucose_by_hour()
            self.save_tir_by_hour()
            self.save_low_counts()
            self.save_mean_daily_low_rate()
            self.save_very_low_count_and_rate()

            self.write_statistics_page(show_hba1c=(days >= 90))
            if days <= 30:
                self.plot_glucose_by_hour_graph()
            self.plot_tir_by_hour_graph()
            self.plot_lows_report()

        # Plot entries for the last 7 days
        self.reset_df(7)
        self.save_entries_df()
        self.write_entries_dataframe()

        self.pdf.close()
