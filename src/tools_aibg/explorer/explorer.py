import pandas as pd
import sys
from typing import Union, TextIO, List

from .loaders import DiaguardImportReader


class Explorer():
    """Explorer class for obtaining and filtering the entry dataframe"""
    def __init__(self, f: Union[str, TextIO] = None, verbose: bool = False):
        """Constructs the entry dataframe with DiaguardImportReader"""
        if f is None:
            f = sys.stdin
        elif type(f) == str:
            f = open(f, 'r')

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
        now = pd.Timestamp.now()
        delta = pd.Timedelta(-x, 'd')
        self.df = self.df[self.df["date"] > now + delta]
        return self


if __name__ == "__main__":
    a = Explorer('diaguard.csv', verbose=True)
