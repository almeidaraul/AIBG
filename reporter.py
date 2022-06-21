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

    def plot_glucose(self, df, fname):
        """plot glucose by time"""
        # TODO
        plt.figure(figsize=(21, 12))
        plt.xticks(df["date"], rotation=90)
        plt.title("Glucose by Time")
        print(df)
        plt.plot(df["date"], df["glucose"])
        plt.savefig(fname)

    def get_values(self):
        """calculate all necessary information"""
        self.explorer.last_x_days(90)
        # hba1c
        hba1c = self.analyser.hba1c()
        self.explorer.reset_df().last_x_days(15)
        # glucose (all entries)
        glucose_entries = self.analyser.df[["date", "glucose"]]
        self.plot_glucose(glucose_entries, 'glucose.png')
        # tir
        in_range, below_range, above_range = self.analyser.tir(70, 180)
        tir_graph_fname = 'tir.png'
        self.plot_tir(in_range, below_range, above_range, 'tir.png')
        # total entries
        total_entries = self.analyser.count()
        groupby_day = self.analyser.groupby_day()
        # entries per day
        entries_per_day = groupby_day["date"].count()
        # fast insulin total, mean, std per day
        fast_insulin_per_day = {
            "total": groupby_day["fast_insulin"].sum(),
            "mean": groupby_day["fast_insulin"].mean(),
            "std": groupby_day["fast_insulin"].std(),
        }
        # glucose mean, std per hour
        groupby_hour = self.analyser.groupby_hour()
        glucose_per_hour = {
            "mean": groupby_hour["glucose"].mean(),
            "std": groupby_hour["glucose"].std(),
        }
        # glucose mean, std per week day
        groupby_weekday = self.analyser.groupby_weekday()
        glucose_per_weekday = {
            "mean": groupby_weekday["glucose"].mean(),
            "std": groupby_weekday["glucose"].std(),
        }
        # glucose by datetime
        glucose_entries = self.analyser.df[["date", "glucose"]].dropna() #TODO dropna?
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
