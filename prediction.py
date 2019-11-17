import pandas as pd
import numpy as np


# input arg df: df return by clean(df)
# input arg input_sub: suburb that customer inputing
def get_listing_data(df,input_sub):
    df = df.groupby(['listing_id'])
    df = df.get_group(input_sub)
    df.reset_index(drop=True)
    df.index = range(len(df.index))
    return df


if __name__ == '__main__':
    df = pd.read_csv("calender.csv")