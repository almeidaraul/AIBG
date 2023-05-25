import re
import pandas as pd
import sys
from typing import Union, TextIO, List


class DiaguardCSVParser():
    """Reads Diaguard CSV backup file into a dataframe for Explorer objects"""
    def __init__(self, f: TextIO):
        """Reads a diaguard backup csv file and creates the entry dataframe"""
        self.lines = [line.strip() for line in f.readlines()]
        self.foods = {}  # format: `food: carbs (g) per 100g`
        self.entries = []
        self.process_backup()
        self.df = pd.DataFrame(self.entries)
        self.df['date'] = pd.to_datetime(self.df['date'])

    def format_line(self, line):
        """Remove double quotes and semicolons and convert to list"""
        def clear_chars(s): return re.sub(r"^\"|\"$", "", s)
        line = list(map(clear_chars, line.split(';')))
        return line[0], line[1:]

    def process_food(self, food_info):
        """Format food name and save it into foods dictionary"""
        food_name = food_info[0].lower()
        self.foods[food_name] = float(food_info[-1])

    def process_entry(self, content, i):
        """Process a single entry starting at given index"""
        date, comments = content[:2]
        glucose, activity, hba1c = None, 0, None
        insulin = (0,)*3  # bolus, correction, basal
        meal = {}  # food: grams of carbs
        tags = []
        while i < len(self.lines):
            field, values = self.format_line(self.lines[i])
            if field == "measurement":
                category = values[0]
                if category == "bloodsugar":
                    glucose = int(float(values[1]))
                elif category == "insulin":
                    insulin = tuple(map(lambda x: int(float(x)), values[1:4]))
                elif category == "meal":
                    meal["carbs"] = float(values[1])
                elif category == "activity":
                    activity = float(values[1])
                elif category == "hba1c":
                    hba1c = float(values[1])
            elif field == "foodEaten":
                food_eaten = values[0].lower()
                food_weight = float(values[1])
                carb_ratio = self.foods[food_eaten]/100
                meal[food_eaten] = food_weight * carb_ratio
            elif field == "entryTag":
                tags.append(values[0])
            else:
                break
            i += 1
        self.entries.append({
            "date": date,
            "glucose": glucose,
            "bolus_insulin": insulin[0],
            "correction_insulin": insulin[1],
            "fast_insulin": sum(insulin[:2]),
            "basal_insulin": insulin[2],
            "total_insulin": sum(insulin),
            "activity": activity,
            "hba1c": hba1c,
            "meal": meal,
            "carbs": sum(meal.values()),
            "tags": tags,
            "comments": comments,
        })
        return i

    def process_backup(self):
        """Process the whole CSV backup file"""
        i = 0
        while i < len(self.lines):
            name, content = self.format_line(self.lines[i])
            if name == "food":
                self.process_food(content)
                i = i+1
            elif name == "entry":
                i = self.process_entry(content, i+1)
            else:
                i = i+1



class DataFrameHandler():
    """Explorer class for obtaining and filtering the entry dataframe"""
    def __init__(self, f: TextIO):
        """Constructs the entry dataframe, sorted by ascending datetime"""
        self.original_df = DiaguardCSVParser(f).df
        self.original_df.sort_values(by="date", ascending=True, inplace=True)
        self.df = self.original_df.copy()

    def count(self):
        """Count number of entries"""
        return self.df.count().max()

    def groupby_hour(self):
        """Returns df grouped by hour of the day"""
        return self.df.groupby(self.df["date"].dt.hour)

    def groupby_day(self):
        """Returns df grouped by date without hour"""
        return self.df.groupby(self.df["date"].dt.date)

    def groupby_weekday(self):
        """Returns df grouped by day of the week"""
        return self.df.groupby(self.df["date"].dt.day_name())

    # filters select data from df and return the explorer itself
    # (so you can do explorer.glucose(min=70, max=100).carbs(min=5, max=70).df)
    def reset_df(self):
        """go back to original df"""
        self.df = self.original_df.copy()
        return self

    def col_lims(self, column, lower_bound=0, upper_bound=9999):
        """Filter by column values in [lower_bound, upper_bound)"""
        self.df = self.df[(self.df[column] >= lower_bound)
                          & (self.df[column] < upper_bound)]
        return self

    def has_tags(self, invert_filter=False):
        """Select all entries with tags"""
        mask = self.df["tags"].astype(bool)
        if invert_filter:
            mask = ~mask
        self.df = self.df[mask]
        return self

    def tags_include(self, tags: Union[List[str], str],
                     include_any: bool = False):
        """Select all entries with all/one of given tags

        Arguments:
        tags: converted to unary list if it's a single string
        include_any: whether filtering will select entries with just some of
                     the tags
        """
        selector = any if include_any else all
        def filter_fn(row): return selector(t in row["tags"] for t in tags)

        if type(tags) == str:
            tags = [tags]

        filter_column = self.df.apply(filter_fn, axis=1)
        self.df = self.df[filter_column]
        return self

    def has_comments(self):
        """Select all entries with comments"""
        self.df = self.df[self.df["comments"].astype(bool)]
        return self

    def date(self, lower_bound='1990-01-01', upper_bound='2100-01-01'):
        """Filter by date in format YYYY-MM-DD"""
        self.df = self.df[(self.df['date'] >= lower_bound)
                          & (self.df['date'] < upper_bound)]
        return self

    def last_x_days(self, x=90):
        """Select all entries in the last x days"""
        # TODO pegar data recente
        now = pd.Timestamp.now()
        delta = pd.Timedelta(-x, 'd')
        self.df = self.df[self.df["date"] > now + delta]
        return self