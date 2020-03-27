import numpy as np
import pandas as pd
from explorer import Explorer

# pega csv e transforma em dataframe do pandas
df = pd.read_csv('example_data.csv')
ex = Explorer(df)
print(ex.bg_avg())
