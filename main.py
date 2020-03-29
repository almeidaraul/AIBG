import datetime as dt
import numpy as np
import pandas as pd
from explorer import Explorer

# tests on example data

df = pd.read_csv('example_data.csv')

# turn all dates into actual datetime objects:
df.date = df.date.apply(lambda date_string 
    : dt.datetime.strptime(date_string, '%Y-%m-%d %H:%M'))

ex = Explorer(df)
print(ex.basic_stats('bg', 'avg', 'snack', 'before'), 
    " +- ", ex.basic_stats('bg', 'std', 'snack', 'before'))
print(ex.HbA1c())
print(ex.range_time())
ex.plot_range_time(out=None)
