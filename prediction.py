import datetime

import pandas as pd
import numpy as np
from sklearn import linear_model
import matplotlib.pyplot as plt


def get_listing_data(df, listing):
    df1 = df.copy()
    new = df1.groupby(['listing_id']).get_group(listing)
    return new


def get_listings(df):
    df["listing_id"] = df["listing_id"].apply(str)
    df["listing_id"] = pd.to_numeric(df["listing_id"])
    my_list = df["listing_id"].values
    uniqueVals = np.unique(my_list)
    return uniqueVals


def predict(suburb, date):
    df = pd.read_csv('calendar.csv')

    a = get_listings(df)
    # print(a)
    listing = get_listing_data(df, suburb)
    listing.drop(['listing_id'], axis=1, inplace=True)
    listing.set_index("date", inplace=True)
    listing = listing[::-1]
    listing.reset_index(inplace=True)
    start = listing['date'][0]
    starts = datetime.datetime.strptime(start, '%Y-%m-%d')
    difference = (datetime.datetime.strptime(date, '%Y-%m-%d') - starts).days

    # print(listing)

    vertical = listing.index.tolist()
    # print(vertical)
    horizontal = listing['price'].tolist()

    length = len(vertical)
    vertical = np.array(vertical).reshape([length, 1])
    horizontal = np.array(horizontal)

    minV = min(vertical)
    maxV = max(vertical)
    X = np.arange(minV, maxV).reshape([-1, 1])

    linear = linear_model.LinearRegression()
    linear.fit(vertical, horizontal)
    y = linear.coef_ * difference + linear.intercept_
    y = round(float(y), 2)
    if len(listing) <= 10:
        y = None

    # print(y)
    # plt.scatter(vertical, horizontal, color='red')
    # plt.plot(X, linear.predict(X), color='blue')
    # plt.xlabel('Date')
    # plt.ylabel('Price')
    # plt.title(suburb)
    # plt.show()
    return y

predict(30592505, '2019-08-01')
