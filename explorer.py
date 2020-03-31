import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class Explorer():
    def __init__(self, df, lo=70, up=180, 
            begin_date=dt.datetime(1700, 1, 1, 0, 0), 
            end_date=dt.datetime(2200, 1, 1, 0, 0)):
        """ df: dataframe with all the data this explorer needs
            lo: lower bound for bg care analysis
            up: upper bound for bg care analysis
            begin_date: begin date for studied interval
            end_date: end date for studied interval
        """
        self.df = df
        self.lo = lo
        self.up = up
        self.begin_date = begin_date
        self.end_date = end_date

    def update(df=None, lo=None, up=None, begin_date=None, end_date=None):
        """Update attributes in our explorer object"""
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
        """Number of non-null blood glucose registries"""
        return self.df.bg.count()

    def interval_filter(self):
        """Returns dataframe of registries inside self.interval"""
        return ((self.df.date >= self.begin_date) &
            (self.df.date <= self.end_date))

    def meal_filter(self, meal='all', moment='before'):
        """Returns boolean dataframe of registries of
        meals based on filters given as parameters.

        moments: before, after, all

        meals: snack, breakfast, lunch, dinner, all
        """
        meals = (['snack', 'dinner', 'lunch', 'breakfast'] if meal == 'all'
                else [meal])

        if moment == 'after':
            meals = ['after_'+meal for meal in meals]
        elif moment == 'all':
            meals += ['after_'+meal for meal in meals] 

        # The lambda function defined below will return True for any tag that
        # intersects with the meals variable.
        return self.df.tags.apply(
            lambda tag : 
            len([m for m in meals if m in tag]) > 0 if isinstance(tag, str) 
            else False)

    def basic_stats(self, column, op, meal=None, moment=None):
        """Basic stats should handle any operation that depends only
        on a row's value (not on next row, or on a group of rows) and
        uses this class' standard interval and meal filters.
        """
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
        """Percentage (our count) of registries with bg in, above or below
        range.

        region: below, above, in
        """
        if region == 'below':
            region_df = self.df.bg[self.df.bg < self.lo]
        elif region == 'above':
            region_df = self.df.bg[self.df.bg > self.up]
        else:
            region_df = (self.df.bg[(self.df.bg >= self.lo)
                & (self.df.bg <= self.up)])

        region_df = region_df[self.interval_filter()]

        if count:
            return region_df.count()
        else:
            return region_df.count()*100/self.df.bg.count()

    def HbA1c(self, up_until=None):
        """Glycated hemoglobin starting 3 months before up_until and ending at
        up_until.

        If up_until == None, calculates HbA1c starting 3 months from today.
        """
        if up_until:
            start_date = up_until
        else:
            start_date = dt.datetime.now()
        start_date -= pd.DateOffset(months=3)

        avg_bg = self.df.bg[self.df.date >= start_date].mean()
        return (avg_bg+46.7)/28.7

    def plot_range_time(self, out='tir.png'):
        """Plot time in range as pie chart.
        By default, saves output to 'tir.png'
        """
        in_range = self.range_time('in')
        above_range = self.range_time('above')
        below_range = self.range_time('below')

        labels = ['In range ({}%)'.format(int(in_range)),
                'Above range({}%)'.format(int(above_range)),
                'Below range({}%)'.format(int(below_range))]

        sizes = [in_range, above_range, below_range]
        colors = ['mediumseagreen', 'gold', 'orangered']

        plt.pie(sizes, labels=labels, colors=colors)
        plt.axis('equal')
        if out:
            plt.savefig(out)
        else:
            plt.show()
    
    def report(self):
        """Give a report"""
        print("BLOOD GLUCOSE")
        print("Mean and std deviation: {} ({})".format(
            self.basic_stats('bg', 'avg'),
            self.basic_stats('bg', 'std')))
        print("Time in range: {}%".format(self.range_time('in')))
        print("Time below range: {}%".format(self.range_time('below')))
        print("Time above range: {}%".format(self.range_time('above')))
        print("Mean and std deviation before all meals: {} ({})".format(
            self.basic_stats('bg', 'avg', 'all', 'before'),
            self.basic_stats('bg', 'std', 'all', 'before')))
        print("Mean and std deviation after all meals: {} ({})".format(
            self.basic_stats('bg', 'avg', 'all', 'after'),
            self.basic_stats('bg', 'std', 'all', 'after')))
        print("HbA1c: ", self.HbA1c())
        print("INSULIN")
        print("Total used: {}u".format(
            self.basic_stats('applied_insulin', 'cumsum')))
        print("Average (and std deviation) for use before any meal: ",
            "{} ({})u".format(
            self.basic_stats('applied_insulin', 'avg', 'all', 'before'),
            self.basic_stats('applied_insulin', 'std', 'all', 'before')))
        print("Average (and std deviation) for use after any meal: {} ({})u".format(
            self.basic_stats('applied_insulin', 'avg', 'all', 'after'),
            self.basic_stats('applied_insulin', 'std', 'all', 'after')))
        print("Average (and std deviation) for general use: {} ({})u".format(
            self.basic_stats('applied_insulin', 'avg'),
            self.basic_stats('applied_insulin', 'std')))
        print("CARBOHYDRATES - Average and std deviation: {} ({})".format(
            self.basic_stats('carbohydrates', 'avg'),
            self.basic_stats('carbohydrates', 'std')))
        print("PROTEINS - Average and std deviation: {} ({})".format(
            self.basic_stats('proteins', 'avg'),
            self.basic_stats('proteins', 'std')))
        print("FAT - Average and std deviation: {} ({})".format(
            self.basic_stats('fat', 'avg'),
            self.basic_stats('fat', 'std')))

