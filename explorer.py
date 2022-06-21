from tqdm import trange
import pandas as pd

class Explorer():
    def __init__(self, filename, verbose=False):
        self.original_df = self.read_diaguard_backup(filename)
        columns_with_nans = ["bolus_insulin", "correction_insulin",
                             "basal_insulin", "activity"]
        for column in columns_with_nans:
            self.original_df[column] = self.original_df[column].fillna(0)
        self.df = self.original_df.copy()
        if verbose:
            print(self.df.info())
            print(self.df.describe())
            print(self.df.head())

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
                numeric_bolus = bolus_insulin
                if bolus_insulin == None:
                    numeric_bolus = 0
                numeric_correction = correction_insulin
                if correction_insulin == None:
                    numeric_correction = 0
                numeric_basal = basal_insulin
                if basal_insulin == None:
                    numeric_basal = 0
                fast_insulin = numeric_bolus + numeric_correction
                total_insulin = fast_insulin + numeric_bolus
                entries.append({
                    "date": date,
                    "glucose": glucose,
                    "bolus_insulin": bolus_insulin,
                    "correction_insulin": correction_insulin,
                    "fast_insulin": fast_insulin,
                    "basal_insulin": basal_insulin,
                    "total_insulin": total_insulin,
                    "activity": activity,
                    "hba1c": hba1c,
                    "meal": meal,
                    "carbs": sum(meal.values()),
                    "tags": tags,
                    "comments": comments,
                })
        df = pd.DataFrame(entries)
        df['date']= pd.to_datetime(df['date'])
        return df

    # filters select data from df and return the explorer itself
    # (so you can do explorer.glucose(min=70, max=100).carbs(min=5, max=70).df)
    def reset_df(self):
        """go back to original df"""
        self.df = self.original_df.copy()

    def glucose(self, lower_bound=0, upper_bound=9999):
        """filter by glucose"""
        self.df = self.df[(self.df["glucose"] >= lower_bound)
                          & (self.df["glucose"] < upper_bound)]
        return self

    def carbs(self, lower_bound=0, upper_bound=9999):
        """filter by carbs (g)"""
        self.df = self.df[(self.df["carbs"] >= lower_bound)
                          & (self.df["carbs"] < upper_bound)]
        return self

    def bolus(self, lower_bound=0, upper_bound=9999):
        """filter by bolus insulin units"""
        self.df = self.df[(self.df["bolus_insulin"] >= lower_bound)
                          & (self.df["bolus_insulin"] < upper_bound)]
        return self

    def correction(self, lower_bound=0, upper_bound=9999):
        """filter by correction insulin units"""
        self.df = self.df[(self.df["correction_insulin"] >= lower_bound)
                          & (self.df["correction_insulin"] < upper_bound)]
        return self

    def basal(self, lower_bound=0, upper_bound=9999):
        """filter by basal insulin units"""
        self.df = self.df[(self.df["basal_insulin"] >= lower_bound)
                          & (self.df["basal_insulin"] < upper_bound)]
        return self

    def fast_insulin(self, lower_bound=0, upper_bound=9999):
        """filter by bolus and correction insulin units"""
        self.df = self.df[(self.df["fast_insulin"] >= lower_bound)
                          & (self.df["fast_insulin"] < upper_bound)]
        return self

    def total_insulin(self, lower_bound=0, upper_bound=9999):
        """filter by total insulin units"""
        self.df = self.df[(self.df["total_insulin"] >= lower_bound)
                          & (self.df["total_insulin"] < upper_bound)]
        return self

    def activity(self, lower_bound=0, upper_bound=9999):
        """filter by physical activity (minutes)"""
        self.df = self.df[(self.df["activity"] >= lower_bound)
                          & (self.df["activity"] < upper_bound)]
        return self

    def has_tags(self):
        """select all entries with tags"""
        self.df = self.df[self.df["tags"].astype(bool)]
        return self

    def no_tags(self):
        """select all entries with no tags"""
        self.df = self.df[~self.df["tags"].astype(bool)]
        return self

    def tags_include_any(self, tags):
        """
        select all entries with at least one of given tags
        - tags: list of str; converted to unary list if it's a single string
        """
        if type(tags) == str:
            tags = [tags]
        filter_column = self.df.apply(lambda row: any(t in row["tags"] for t in tags), axis=1)
        self.df = self.df[filter_column]
        return self

    def tags_include_all(self, tags):
        """
        select all entries where all tags are present
        - tags: list of str; converted to unary list if it's a single string
        """
        if type(tags) == str:
            tags = [tags]
        filter_column = self.df.apply(lambda row: all(t in row["tags"] for t in tags), axis=1)
        self.df = self.df[filter_column]
        return self

    def has_comments(self):
        """select all entries with comments"""
        self.df = self.df[self.df["comments"].astype(bool)]
        return self

    def date(self, lower_bound='1990-01-01', upper_bound='2100-01-01'):
        """filter by date in format YYYY-MM-DD"""
        self.df = self.df[(self.df['date'] >= lower_bound)
                          & (self.df['date'] < upper_bound)]
        return self

    def last_x_days(self, x=90):
        """select all entries in the last x days"""
        self.df = self.df[self.df["date"] > pd.Timestamp.now() + pd.Timedelta(-x, "d")]
        return self


if __name__=="__main__":
    a = Explorer('diaguard.csv', verbose=True)
