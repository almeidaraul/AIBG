import pandas as pd
import numpy as np

class Explorer():
    def __init__(self, dataframe, lower_bound=70, upper_bound=180, interval=None):
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
        if interval:
            self.interval = interval

    def bg_avg(self):
        """average blood glucose inside interval"""
        pass

    def bg_stddev(self):
        """std deviation for blood glucose in given interval"""
        pass

    def time_in_range(self):
        """% of bg in given interval that is inside range given by
        lower and upper bound"""
        pass

    def time_above_range(self):
        """% of bg in given interval that is above upper bound"""
        pass

    def time_below_range(self):
        """% of bg in given interval that is below upper bound"""
        pass

    def in_range_count(self):
        """number of registries in range"""
        pass

    def above_range_count(self):
        """number of registries above range"""
        pass

    def below_range_count(self):
        """registries below range"""
        pass

    def HbA1c(self):
        """glycated hemoglobin"""
        pass
