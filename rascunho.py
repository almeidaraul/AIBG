import numpy as np
import pandas as pd

# pega csv e transforma em dataframe do pandas
df = pd.read_csv('example_data.csv')

media = df['Glicemia'].mean()
total_registros = df['Glicemia'].count()
tir_bom = df.loc[df['Glicemia'] <= 180].loc[df['Glicemia'] >= 70]['Glicemia'].count()*100/total_registros
tir_baixo = df.loc[df['Glicemia'] < 70]['Glicemia'].count()*100/total_registros
tir_alto = df.loc[df['Glicemia'] > 180]['Glicemia'].count()*100/total_registros
print(df)
print("Média: ", media, "\nTIR: ", tir_bom, "\nABAIXO: ", tir_baixo, "\nACIMA: ", tir_alto)
