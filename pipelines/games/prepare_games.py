import pandas as pd

#Load the CSV
df = pd.read_csv("data/raw/games_raw.csv", low_memory=False)

#Populate the columns to keep and generate a new dataframe
cols_to_keep = [
    "homeId",
    "homePoints",
    "awayId",
    "awayPoints",
    "homePregameElo",
    "awayPregameElo"
]

df = df[cols_to_keep]

# Drop any rows with null values
df = df.dropna()

# Add spread column
df["spread"] = df["homePoints"] - df["awayPoints"]

# Save to CSV
df.to_csv("data/prepared/games_prepared.csv", index=False)
