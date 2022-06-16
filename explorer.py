from tqdm import trange
import pandas as pd

class Explorer():
    def __init__(self, filename):
        self.original_df = self.read_diaguard_backup(filename)
        self.df = original_df.copy()

    def clean_diaguard_line(self, line):
        """
        remove double quotes and semicolons from line and convert it to
        list

        line is expected to come from a diaguard backup csv
        """
        clean_line = []
        for item in line.split(';'):
            if len(item) > 0:
                if item[0] == '"':
                    item = item[1:]
                if item[-1] == '"':
                    item = item[:-1]
            clean_line.append(item)
        return clean_line
    
    def read_diaguard_backup(self, filename):
        """read a diaguard backup csv file to create the entry dataframe"""
        f = open(filename, 'r')
        lines = [line.strip() for line in f.readlines()]
        foods = {} # food: carbs (g) per 100g
        entries = []
        for i in trange(len(lines), desc=f"Read Diaguard backup {filename}", unit="lines"):
            line = self.clean_diaguard_line(lines[i])
            name = line[0]
            if name == "food":
                food_name = line[1].lower()
                foods[food_name] = float(line[-1])
            elif name == "entry":
                date = line[1]
                comments = line[2]
                glucose = None
                bolus_insulin = None
                correction_insulin = None
                basal_insulin = None
                activity = None
                hba1c = None
                meal = {} # food: grams of carbs
                tags = []
                j = i+1
                while j < len(lines):
                    line = self.clean_diaguard_line(lines[j])
                    name = line[0]
                    if name == "measurement":
                        category = line[1]
                        if category == "bloodsugar":
                            glucose = int(float(line[2]))
                        elif category == "insulin":
                            bolus_insulin = int(float(line[2]))
                            correction_insulin = int(float(line[3]))
                            basal_insulin = int(float(line[4]))
                        elif category == "meal":
                            meal["carbs"] = float(line[2])
                        elif category == "activity":
                            activity = float(line[2])
                        elif category == "hba1c":
                            hba1c = float(line[2])
                    elif name == "foodEaten":
                        food_eaten = line[1].lower()
                        food_weight = float(line[2])
                        carb_ratio = foods[food_eaten]/100
                        meal[food_eaten] = food_weight * carb_ratio
                    elif name == "entryTag":
                        tags.append(line[1])
                    else:
                        break
                    j += 1
                food_str = [f"{x} ({meal[x]}g)" for x in meal.keys()]
                meal_str = ", ".join(food_str)
                #tags = ", ".join(tags)
                entries.append({
                    "date": date,
                    "glucose": glucose,
                    "bolus_insulin": bolus_insulin,
                    "correction_insulin": correction_insulin,
                    "basal_insulin": basal_insulin,
                    "activity": activity,
                    "hba1c": hba1c,
                    "meal": meal,
                    "tags": tags,
                })
        df = pd.DataFrame(entries)
        df['date']= pd.to_datetime(df['date'])
        return df

    # filters select data from df and return the explorer itself
    # (so you can do explorer.glucose(min=70, max=100).carbs(min=5, max=70).df)
    def reset_df(self):
        """go back to original df"""
        self.df = self.original_df.copy()

    def glucose(lower_bound=0, upper_bound=1000):
        """filter by glucose"""
        self.df = self.df[(self.df["glucose"] >= lower_bound)
                          & (self.df["glucose"] < upper_bound)]
        return self


if __name__=="__main__":
    Explorer('diaguard.csv')
