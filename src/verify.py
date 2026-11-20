import pandas as pd

df = pd.read_csv("data/titanic.csv")
print(df.groupby("Pclass")["Survived"].mean())