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
ex.report()
