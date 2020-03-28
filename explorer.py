import pandas as pd
import numpy as np

class Explorer():
    def __init__(self, dataframe, lower_bound=70, upper_bound=180, interval=("'1990'", "'2049'")):
        self.df = dataframe
        self.lo = lower_bound
        self.up = upper_bound
        self.interval = interval

    def edit(df=None, lo=None, up=None, interval=None):
        if df:
            self.df = df
        if lo:
            self.lo = lo
        if up:
            self.up = up
        if interval[0]:
            self.interval[0] = interval[0]
        if interval[1]:
            self.interval[1] = interval[1]

    def bg_count(self):
        """number of non-null blood glucose registries"""
        return self.df.bg.count()

    def inside_interval(self):
        """returns dataframe of registries inside self.interval"""
        return self.df[
                self.date >= self.interval[0] and
                self.date <= self.interval[1]
                ].count()

    def bg_avg(self):
        """average blood glucose inside interval"""
        return self.df.bg.mean()

    def bg_stddev(self):
        """std deviation for blood glucose in given interval"""
        return self.df.bg.std()

    def time_in_range(self):
        """% of bg in given interval that is inside range given by
        lower and upper bound"""
        # TODO: rename blood_glucose in example data to bg
        in_range = self.df.bg[
                    self.df.bg >= self.df.lo and 
                    self.df.bg <= self.df.up and
                    self.inside_interval()
                    ].count()
        return in_range*100/self.bg_count()

    def time_above_range(self):
        """% of bg in given interval that is above upper bound"""
        above_range = self.df.bg[
                        self.df.bg > self.up and
                        self.inside_interval()
                        ].count()
        return above_range*100/self.bg_count()

    def time_below_range(self):
        """% of bg in given interval that is below upper bound"""
        below_range = self.df.bg[
                        self.df.bg < self.lo and
                        self.inside_interval()
                        ].count()
        return below_range*100/self.bg_count()

    def in_range(self):
        """number of registries in range"""
        return self.df.bg[
                self.df.bg <= self.up and
                self.df.bg >= self.lo and
                self.df.inside_interval()].count()

    def above_range(self):
        """number of registries above range"""
        return self.df.bg[
                self.df.bg > self.up and
                self.df.inside_interval()].count()

    def below_range(self):
        """registries below range"""
        return self.df.bg[
                self.df.bg < self.lo and
                self.df.inside_interval()].count()

    def HbA1c(self):
        """glycated hemoglobin"""
        avg_bg = self.bg_avg # TODO: make this last 3 months' avg
        return (avg_bg+46.7)/28.7
