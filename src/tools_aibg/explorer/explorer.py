import pandas as pd
import sys

from .loaders import DiaguardImportReader


class Explorer():
    def __init__(self, filename=None, verbose=False):
        self.verbose = verbose
        f = sys.stdin
        if filename:
            f = open(filename, 'r')

        self.original_df = DiaguardImportReader(f).df
        self.original_df = self.original_df.sort_values(
            by='date', ascending=True)

        self.df = self.original_df.copy()

        if verbose:
            print(self.df.info())
            print(self.df.describe())
            print(self.df.head())

    # filters select data from df and return the explorer itself
    # (so you can do explorer.glucose(min=70, max=100).carbs(min=5, max=70).df)
    def reset_df(self):
        """go back to original df"""
        self.df = self.original_df.copy()
        return self

    def col_lims(self, column, lower_bound=0, upper_bound=9999):
        self.df = self.df[(self.df[column] >= lower_bound)
                          & (self.df[column] < upper_bound)]
        return self

    def has_tags(self, invert_filter=False):
        """select all entries with tags"""
        mask = self.df["tags"].astype(bool)
        if invert_filter:
            mask = ~mask
        self.df = self.df[mask]
        return self

    def tags_include(self, tags, include_any=False):
        """
        select all entries with all given tags
        (or at least one, if include_any)
        - tags: list of str; converted to unary list if it's a single string
        """
        selector = any if include_any else all
        def filter_fn(row): return selector(t in row["tags"] for t in tags)

        if type(tags) == str:
            tags = [tags]

        filter_column = self.df.apply(filter_fn, axis=1)
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
        now = pd.Timestamp.now()
        delta = pd.Timedelta(-x, 'd')
        self.df = self.df[self.df["date"] > now + delta]
        return self


if __name__ == "__main__":
    a = Explorer('diaguard.csv', verbose=True)
