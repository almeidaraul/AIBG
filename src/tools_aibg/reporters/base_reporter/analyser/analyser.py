class Analyser():
    def __init__(self, df):
        self.df = df

    def hba1c(self):
        """
        HbA1c value based on glucose readings

        WARNING: HbA1c value should be calculated based on a 3 month window,
        which is not verified by this function
        """
        return (self.df["glucose"].mean()+46.7)/28.7

    def tir(self, lower_bound=70, upper_bound=180):
        """
        time in range

        returns total number of entries in [lo, up), (, lo) and [up,)
        (i.e., in range, below range, and above range)
        """
        glucose = self.df["glucose"]
        in_range = glucose[(glucose >= lower_bound)
                           & (glucose < upper_bound)].count()
        below_range = glucose[glucose < lower_bound].count()
        above_range = glucose[glucose >= upper_bound].count()
        return in_range, below_range, above_range

    def count(self):
        """count number of entries"""
        return self.df.count().max()

    def groupby_hour(self):
        """returns df grouped by hour of the day"""
        return self.df.groupby(self.df["date"].dt.hour)

    def groupby_day(self):
        """returns df grouped by date without hour"""
        return self.df.groupby(self.df["date"].dt.date)

    def groupby_weekday(self):
        """returns df grouped by day of the week"""
        return self.df.groupby(self.df["date"].dt.day_name())