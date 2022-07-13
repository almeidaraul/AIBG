from analyser import Analyser
from explorer import Explorer
import json

class Reporter():
    def __init__(self, explorer):
        self.explorer = explorer
        self.analyser = Analyser(self.explorer.df)

    def get_values(self):
        """calculate all necessary information"""
        report = {}
        self.explorer.last_x_days(90)
        # hba1c
        hba1c = self.analyser.hba1c()
        report["hba1c"] = float(hba1c)
        self.explorer.reset_df().last_x_days(15)
        self.analyser = Analyser(self.explorer.df)
        # tir
        in_range, below_range, above_range = self.analyser.tir(70, 180)
        tir_graph_fname = 'tir.png'
        report["in_range"] = float(in_range)
        report["below_range"] = float(below_range)
        report["above_range"] = float(above_range)
        # total entries
        total_entries = self.analyser.count()
        report["total_entries"] = int(total_entries)
        groupby_day = self.analyser.groupby_day()
        # mean entries per day
        entries_per_day = groupby_day["date"].count().mean()
        report["entries_per_day"] = float(entries_per_day)
        # fast insulin total, mean, std per day
        fast_per_day = groupby_day["fast_insulin"].sum()
        mean_fast_per_day = fast_per_day.mean()
        std_fast_per_day = fast_per_day.std()
        report["mean_fast_per_day"] = float(mean_fast_per_day)
        report["std_fast_per_day"] = float(std_fast_per_day)
        # glucose mean, std per hour
        groupby_hour = self.analyser.groupby_hour()
        glucose_per_hour = {
            "mean": groupby_hour["glucose"].mean(),
            "std": groupby_hour["glucose"].std(),
        }
        report["mean_glucose_per_hour"] = {
                "mean_glucose": [
                    float(x) for x in glucose_per_hour["mean"].tolist()
                ],
                "hour": list(groupby_hour.groups.keys()),
                "std_error": [
                    float(x) for x in glucose_per_hour["std"].tolist()
                ],
                }
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
        table = {
                "Date": table["Date"].astype(str).tolist(),
                "Glucose": [float(x) for x in table["Glucose"].tolist()],
                "Bolus": [int(x) for x in table["Bolus"].tolist()],
                "Correction": [int(x) for x in table["Correction"].tolist()],
                "Basal": [int(x) for x in table["Basal"].tolist()],
                "Meal": table["Meal"].tolist(),
                "Carbohydrates": [int(x) for x in table["Carbohydrates"].tolist()],
                }
        report["table"] = table
        return report

class JSONReporter(Reporter):
    def __init__(self, explorer):
        super().__init__(explorer)
    
    def save(self, filename="report.json"):
        report = super().get_values()
        with open(filename, 'w') as f:
            json.dump(report, f)

if __name__=="__main__":
    a = Explorer('diaguard.csv', verbose=False)
    b = JSONReporter(a)
    b.save()
