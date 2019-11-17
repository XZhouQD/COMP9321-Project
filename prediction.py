import pandas as pd
import numpy as np



def get_listing_data(df,listing):
    df = df.groupby(['listing_id'])
    df = df.get_group(listing)
    df.reset_index(drop=True)
    df.index = range(len(df.index))
    return df


if __name__ == '__main__':
    df = pd.read_csv("calender.csv")