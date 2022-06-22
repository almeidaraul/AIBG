from analyser import Analyser
from explorer import Explorer
import matplotlib.pyplot as plt
import numpy as np

class Reporter():
    def __init__(self, explorer):
        self.explorer = explorer
        self.analyser = Analyser(self.explorer.df)

    def plot_tir(self, in_range, below_range, above_range, fname):
        """plot time in range piechart"""
        values = np.array([in_range, below_range, above_range])
        total = in_range + below_range + above_range
        in_range = int(100*in_range/total)
        below_range = int(100*below_range/total)
        above_range = int(100*above_range/total)
        labels = [f"In Range ({in_range}%)", f"Below Range({below_range}%)",
                  f"Above Range({above_range}%)"]
        plt.pie(values, labels=labels, startangle=90)
        plt.title("Time in Range")
        plt.savefig(fname)
        plt.clf()

    def plot_grouped_glucose(self, y, x, error, xlabel, ylabel, title,
            fname, incline_xlabel=False):
        """plot glucose entries per hour of the day (mean and std)"""
        plt.xticks(x, rotation=(90 if incline_xlabel else 0))
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.errorbar(x, y, error, linestyle='-', marker='o', ecolor='green',
                     capsize=2)
        plt.title(title)
        plt.savefig(fname)
        plt.clf()

    def get_values(self):
        """calculate all necessary information"""
        self.explorer.last_x_days(90)
        # hba1c
        hba1c = self.analyser.hba1c() #TODO
        self.explorer.reset_df().last_x_days(15)
        # tir
        in_range, below_range, above_range = self.analyser.tir(70, 180)
        tir_graph_fname = 'tir.png'
        self.plot_tir(in_range, below_range, above_range, 'tir.png') #TODO
        # total entries
        total_entries = self.analyser.count() #TODO
        groupby_day = self.analyser.groupby_day()
        # entries per day
        entries_per_day = groupby_day["date"].count() #TODO
        # fast insulin total, mean, std per day
        fast_per_day = groupby_day["fast_insulin"].sum()
        mean_fast_per_day = fast_per_day.mean() #TODO
        std_fast_per_day = fast_per_day.std() #TODO
        # glucose mean, std per hour
        groupby_hour = self.analyser.groupby_hour()
        glucose_per_hour = {
            "mean": groupby_hour["glucose"].mean(),
            "std": groupby_hour["glucose"].std(),
        }
        self.plot_grouped_glucose(y=glucose_per_hour["mean"],
                                  x=np.array(range(24)),
                                  error=glucose_per_hour["std"],
                                  xlabel="Hour", ylabel="Glucose (mg/dL)",
                                  title="Glucose per Hour",
                                  fname="glucose_hour.png") #TODO
        # all entries table (pretty)
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
        meal_to_str = lambda meal: '; '.join(
                [f"{x}, {meal[x]:.1f}g" for x in meal.keys()])
        table["meal"] = table["meal"].apply(meal_to_str)
        numeric_columns = ["glucose", "carbs", "bolus_insulin",
                           "correction_insulin", "basal_insulin"]
        for col in numeric_columns:
            table[col] = table[col].fillna(0).apply(lambda x: int(x))
        table = table.rename(columns=show_columns)

if __name__=="__main__":
    a = Explorer('diaguard.csv', verbose=True)
    b = Reporter(a)
    b.get_values()
