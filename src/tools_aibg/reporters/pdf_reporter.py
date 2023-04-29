import numpy as np
import matplotlib.backends.backend_pdf as backend_pdf
import matplotlib.pyplot as plt
import sys
from .base_reporter import Reporter
from math import isnan


class PDFReporter(Reporter):
    def __init__(self, explorer):
        super().__init__(explorer)
        self.A5_FIGURE_SIZE=(8.27, 5.83)

    def plot_statistics(self):
        fig = plt.figure(figsize=self.A5_FIGURE_SIZE)
        ax1 = plt.subplot2grid((2, 1), (0, 0))

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

        ax2 = plt.subplot2grid((2, 1), (1, 0), aspect="equal")

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
        fig = plt.figure(figsize=self.A5_FIGURE_SIZE)
        ax = fig.add_subplot(1, 1, 1)

        hour = self.report["mean_glucose_per_hour"]["hour"]
        glucose = self.report["mean_glucose_per_hour"]["mean_glucose"]
        std = self.report["mean_glucose_per_hour"]["std_error"]
        std = list(map(lambda x: 0.0 if isnan(x) else x, std))

        ax.errorbar(hour, glucose, yerr=std, fmt='-o', capsize=3,
                    elinewidth=2, capthick=2, color="royalblue",
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

            table = ax.table(cellText=data, colLabels=columns, loc='center',
                             fontsize=14)
            ax.axis('off')

            self.pdf.savefig(fig)

    def report(self, filename=None):
        self.report = super().get_values()
        self.pdf = backend_pdf.PdfPages("output.pdf")
        
        self.plot_statistics()
        self.plot_mean_glucose_per_hour()
        self.plot_table()

        self.pdf.close()
