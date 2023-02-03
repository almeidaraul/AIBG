import matplotlib.backends.backend_pdf as backend_pdf
import matplotlib.pyplot as plt
import sys
from reporter import Reporter


class PDFReporter(Reporter):
    def __init__(self, explorer):
        super().__init__(explorer)

    def report(self, filename=None):
        report = super().get_values()

        pdf = backend_pdf.PdfPages("output.pdf")

        A5_FIGURE_SIZE=(8.27, 5.83)

        # statistics
        fig = plt.figure(figsize=A5_FIGURE_SIZE)
        ax1 = plt.subplot2grid((2, 1), (0, 0))

        plt.text(0, 1, "Statistics", ha="left", va="top", fontsize=28)
        plt.text(0, 0.8, f"HbA1c (last 3 months): {report['hba1c']:.2f}%", ha="left",
                 va="top")
        plt.text(0, 0.7, "Last 5 days", ha="left", va="top")
        total_entries = report['total_entries']
        entries_per_day = report['entries_per_day']
        plt.text(
            0, 0.6, 
            f"Total entries: {total_entries}, per day: {entries_per_day}",
            ha="left", va="top")
        fast_per_day = report['mean_fast_per_day']
        std_fast_per_day = report['std_fast_per_day']
        plt.text(
            0, 0.5,
            f"Fast insulin/day: {fast_per_day:.2f} ± {std_fast_per_day:.2f}",
            ha="left", va="top")
        plt.axis('off')

        # time in range pie chart
        plt.text(.5, 0, "Time in Range", ha="center", va="bottom", fontsize=16)

        ax2 = plt.subplot2grid((2, 1), (1, 0), aspect="equal")

        labels = ["Above range", "Below range", "In range"]
        sizes = [
            report["above_range"], report["below_range"], report["in_range"]]

        total = sum(sizes)
        percentages = list(map(lambda x: f"{100*x/total:.2f}%", sizes))

        colors = ["tab:red", "tab:blue", "tab:olive"]

        plt.pie(sizes, labels=percentages, colors=colors)
        plt.legend(labels, loc="best", bbox_to_anchor=(1, 0, 0.5, 1))
        pdf.savefig(fig)

        pdf.close()
