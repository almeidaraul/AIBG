import sys
import datetime as dt
import numpy as np
import pandas as pd
from explorer import Explorer

def preprocessing(filename='example_data.csv'):
    df = pd.read_csv('example_data.csv')
    # turn all dates into actual datetime objects:
    df.date = df.date.apply(lambda date_string 
        : dt.datetime.strptime(date_string, '%Y-%m-%d %H:%M'))
    return df

df = preprocessing()
ex = Explorer(df)
print(ex.bg_count())
print(ex.HbA1c())
print(ex.range_time('in'))
print(ex.range_time('below'))
print(ex.range_time('above'))
print(ex.basic_stats('bg', 'avg'))
print(ex.basic_stats('bg', 'std'))
print(ex.basic_stats('applied_insulin', 'cumsum'))
