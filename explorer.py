import pandas as pd
import numpy as np
import datetime as dt

class Explorer():
    def __init__(self, df, lo=70, up=180, begin_date='1990', end_date='2049'):
        """ df: dataframe with all the data this explorer needs
            lo: lower bound for bg care analysis
            up: upper bound for bg care analysis
            begin_date: begin date for studied interval
            end_date: end date for studied interval
        """
        # TODO: make {begin, end}_date paramaters be actual dates, not strings
        self.df = df
        self.lo = lo
        self.up = up
        self.begin_date = begin_date
        self.end_date = end_date

    def update(df=None, lo=None, up=None, begin_date=None, end_date=None):
        """update attributes in our explorer object"""
        if df:
            self.df = df
        if lo:
            self.lo = lo
        if up:
            self.up = up
        if begin_date:
            self.begin_date = begin_date
        if end_date:
            self.end_date = end_date

    def bg_count(self):
        """number of non-null blood glucose registries"""
        return self.df.bg.count()

    def interval_filter(self):
        """returns dataframe of registries inside self.interval"""
        return self.df.date >= self.begin_date and
                self.df.date <= self.end_date

    def meal_filter(self, meal='all', moment='before'):
        """returns boolean dataframe of registries of
        meals based on filters given as parameters
        moments: before, after, all
        meals: snack, breakfast, lunch, dinner, all"""
        meals = ['snack', 'dinner', 'lunch', 'breakfast'] if meal == 'all'
                else [meal]
        if moment == 'before':
            meals = ['before_'+meal for meal in meals]
        elif moment == 'all':
            meals += ['before_'+meal for meal in meals] 

        return len(set(self.df.tags.split(' ')).intersection(meals)) > 0

    def basic_stats(self, column, op, meal=None, moment=None):
        if not meal:
            filtered_df = self.df[column]
        else:
            filtered_df = self.df[column][self.meal_filter(meal, moment)]

        if op == 'cumsum': #cumulative sum
            return filtered_df.sum()
        elif op == 'avg':
            return filtered_df.mean()
        elif op == 'std': #std deviation
            return filtered_df.std()

    def range_time(self, region='in', count=False):
        """% of bg in, above or below range
        region: below, above, in"""
        if region == 'below':
            region_df = self.df.bg[self.df.bg < self.lo]
        elif region == 'above':
            region_df = self.df.bg[self.df.bg > self.up]
        else:
            region_df = self.df.bg[self.df.bg >= self.lo and
                                    self.df.bg <= self.up]

        region_df = region_df[self.interval_filter()]

        if count:
            return region_df.count()
        else:
            return region_df.count()*100/self.df.bg.count()

    def HbA1c(self):
        """glycated hemoglobin"""
        avg_bg = self.df.bg[
                self.df.date >= dt.datetime.now()-pd.DateOffset(months=3)
                ].mean()
        return (avg_bg+46.7)/28.7
