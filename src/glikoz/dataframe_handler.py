import re
import pandas as pd
from typing import TextIO, List


class DiaguardCSVParser:
    """Parses a Diaguard CSV backup file into a DataFrame

    Each row in the produced dataframe is an entry. Its columns are:
    - date: datetime of the entry
    - glucose (optional): glucose (mg/dL)
    - bolus_insulin (optional): bolus insulin (IU)
    - correction_insulin (optional): correction insulin (IU)
    - basal_insulin (optional): basal insulin (IU)
    - fast_insulin: sum of bolus_insulin and correction_insulin
    - total_insulin: sum of fast_insulin and basal_insulin
    - activity: physical activity (minutes)
    - hba1c: hba1c (percentage)
    - meal: dictionary describing carbohydrates (g) consumed per food eaten
    - carbs: sum of consumed carbohydrates (g) in meal
    - tags: list of strings that tag the entry
    - comments: string providing considerations on the recorded entry
    """
    def __init__(self, f: TextIO):
        """Reads a Diaguard backup CSV file and creates its entry DataFrame

        Attributes created:
        - foods: a dictionary of edibles present in entries. Its keys
        are food names (strings)
        - entries: a list of dictionaries describing dataframe rows (it is
        later used in constructing the dataframe itself)
        - csv_lines: a list of preprocessed lines from the CSV backup
        """
        self.foods = {}  # format: `food: carbs (g) per 100g`
        self.entries = []
        self.csv_lines = [self.format_line(ln.strip()) for ln in f.readlines()]

    def parse_csv(self) -> pd.DataFrame:
        """Parse the CSV file and initialize the entry DataFrame"""
        self.process_lines()
        self.init_df()
        return self.df

    def init_df(self):
        """Initialize the entry DataFrame, sorted by ascending date

        The DataFrame is created from the entries list and derived columns"""
        self.df = pd.DataFrame(self.entries)
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["fast_insulin"] = (self.df["bolus_insulin"]
                                   + self.df["correction_insulin"])
        self.df["total_insulin"] = (self.df["fast_insulin"]
                                    + self.df["basal_insulin"])
        self.df["carbs"] = self.df["meal"].apply(lambda m: sum(m.values()))
        self.df.sort_values(by="date", ascending=True, inplace=True)

    def format_line(self, line):
        """
        Remove double quotes and semicolons from a line and split it into a
        list of semicolon-separated values
        """
        def clear_chars(s): return re.sub(r"^\"|\"$", '', s)
        line = list(map(clear_chars, line.split(';')))
        return line[0], line[1:]

    def process_food(self, food_info):
        """Format food name and save its glycemic index to foods dictionary"""
        food_name = food_info[0].lower()
        self.foods[food_name] = float(food_info[-1])

    def process_entry(self, content, i):
        """Process a single entry that starts in the i-th line in csv_lines

        An entry consists of many lines that describe some or all of the
        following information:
        - date (datetime): when the entry was created
        - comments (string): comments provided by the user (default: '')
        - measurement: measurement in one of the following categories
            - bloodsugar (int): glucose in mg/dL
            - insulin (tuple of 3 ints): injected bolus, correction and basal
            - meal (float): carbohydrates consumed, in g
            - activity (int): minutes of physical activity
            - hba1c (float): hba1c recorded
        - foodEaten: food consumed (its name and grams are provided)
        - entryTag (string): tag that describes the entry

        The end of valid field names indicates the end of an entry.
        """
        date, comments = content[:2]
        glucose, activity, hba1c = None, 0, None
        insulin = (0,)*3  # bolus, correction, basal
        meal = {}
        tags = []
        while i < len(self.csv_lines):
            field, values = self.csv_lines[i]
            if field == "measurement":
                category = values[0]
                if category == "bloodsugar":
                    glucose = int(float(values[1]))
                elif category == "insulin":
                    insulin = tuple(map(lambda x: int(float(x)), values[1:4]))
                elif category == "meal":
                    meal["carbs"] = float(values[1])
                elif category == "activity":
                    activity = int(float(values[1]))
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
            "basal_insulin": insulin[2],
            "activity": activity,
            "hba1c": hba1c,
            "meal": meal,
            "tags": tags,
            "comments": comments,
        })
        return i

    def process_lines(self):
        """Process the CSV backup lines sequentially"""
        i = 0
        while i < len(self.csv_lines):
            name, line_content = self.csv_lines[i]
            if name == "food":
                self.process_food(line_content)
                i = i+1
            elif name == "entry":
                i = self.process_entry(line_content, i+1)
            else:
                i = i+1


class DataFrameHandler:
    """Handler for manipulating the entry DataFrame

    This class provides many filter functions which conform to method chaining
    """

    def __init__(self, entry_df: pd.DataFrame):
        """Constructs the entry dataframe, sorted by ascending datetime

        Two versions of the dataframe are kept: the original one, and one with
        filter applied. This allows users to use the reset_df function
        """
        self.original_df = entry_df
        self.df = self.original_df.copy()

    def count(self):
        """Count total number of entries"""
        return len(self.df)

    def groupby_hour(self):
        """Group df by hour of the day"""
        return self.df.groupby(self.df["date"].dt.hour)

    def groupby_day(self):
        """Group df by date without hour"""
        return self.df.groupby(self.df["date"].dt.date)

    def groupby_weekday(self):
        """Group df by day of the week"""
        return self.df.groupby(self.df["date"].dt.day_name())

    # filters select data from df and return the handler itself
    # (so you can do handler.glucose(min=70, max=100).carbs(min=5, max=70).df)
    def reset_df(self):
        """Reset current df to original df"""
        self.df = self.original_df.copy()
        return self

    def col_lims(self, column: str, lower_bound: float = 0,
                 upper_bound: float = 9999):
        """Filter by column (numeric) values in [lower_bound, upper_bound)"""
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

    def tags_include(self, tags: List[str], include_any: bool = False):
        """Select all entries with all/one of given tags

        Arguments:
        tags: tags to be searched
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

    def date(self, lower_bound: str = "1990-01-01",
             upper_bound: str = "2100-01-01"):
        """Filter by date in format YYYY-MM-DD"""
        self.df = self.df[(self.df["date"] >= lower_bound)
                          & (self.df["date"] < upper_bound)]
        return self

    def last_x_days(self, x: int):
        """Select all entries in the most recent x days"""
        most_recent_timestamp = self.df["date"].max()
        delta = pd.Timedelta(-x, 'd')
        self.df = self.df[self.df["date"] > most_recent_timestamp + delta]
        return self
