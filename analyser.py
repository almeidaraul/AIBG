class Analyser():
    def __init__(self, df):
        self.df = df

    def avg(self, column):
        """average value for given column"""
        return self.df[column].mean()

    def std(self, column):
        """std deviation for given column"""
        return self.df[column].std()

    def hba1c(self):
        """
        HbA1c value based on glucose readings

        WARNING: HbA1c value should be calculated based on a 3 month window,
        which is not verified by this function
        """
        return (self.avg("glucose")+46.7)/28.7
