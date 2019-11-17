import pandas as pd
import numpy as np



def get_listing_data(df,listing):
    df = df.groupby(['listing_id'])
    df = df.get_group(listing)

    return df

def get_listings(df):
    df["listing_id"] = df["listing_id"].apply(str)
    df["listing_id"] = pd.to_numeric(df["listing_id"])
    my_list = df["listing_id"].values
    uniqueVals = np.unique(my_list)
    return uniqueVals

if __name__ == '__main__':
    df = pd.read_csv('calendar.csv')
    # df.set_index("listing_id", inplace=True)
    # print(df)
    a = get_listings(df)
    print(a)
    listing = get_listing_data(df, a[0])
    listing.drop(['listing_id'], axis=1, inplace=True)
    print(listing)