import numpy as np
import pandas as pd
import datetime as dt
from explorer import Explorer

# get example data and put it into a pandas dataframe
df = pd.read_csv('example_data.csv')

# turn all dates into actual datetime objects:
df.date = df.date.apply(lambda date_string : 
        dt.datetime.strptime(date_string, '%Y-%m-%d %H:%M')

ex = Explorer(df)
