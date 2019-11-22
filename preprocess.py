#!/usr/bin/python3

'''
UNSW COMP9321 19T3
Assignment 2
Team Data Analysis Towards Abbreviation

Members (In order of Last Name)
Genyuan Liang z5235682
Jiasi Lu z5122462
Yefeng Niu z5149500
Haiyan Xu z5135077
Xiaowei Zhou z5108173

Environment:
Python 3.7
pandas 0.25.0
sqlalchemy 1.3.10
'''

import pandas as pd


def read_csv(csv_file):
    return pd.read_csv(csv_file)


def write_csv(df, target):
    df.to_csv(target, sep=',', encoding='utf-8')


def print_df(df, print_col=True, print_row=False):
    if print_col:
        print(','.join([column for column in df]))

    if print_row:
        print(",".join([str(row[column]) for column in df]))


if __name__ == '__main__':
    print("====== Starting Preprocess ======")

    # related files
    data_dir = "syd_airbnb_open_data/"

    # ==================== preprocess for neighbourhoods_dec18.csv ======================
    print('preprocessing neighbourhoods_dec18.csv')

    neighbourhoods_file = data_dir + "neighbourhoods_dec18.csv"
    neighbourhoods_df = read_csv(neighbourhoods_file)

    # discard unwanted columns
    neighbourhoods_df = neighbourhoods_df[['neighbourhood']]

    # write file
    write_csv(neighbourhoods_df, "neighbour.csv")

    # ======================= preprocess for listings_dec18.csv =========================
    print('preprocessing listings_dec18.csv')

    listings_file = data_dir + "listings_dec18.csv"
    listings_df = read_csv(listings_file)

    # discard unwanted columns
    to_keep = ["id", "name", "host_id", "host_name", "host_response_time", "host_response_rate", "host_neighbourhood",
               "city", "property_type", "room_type", "accommodates", "bathrooms", "bedrooms", "beds", "amenities",
               "price", "security_deposit", "cleaning_fee", "guests_included", "availability_60", "availability_365",
               "review_scores_rating", "review_scores_accuracy", "review_scores_cleanliness", "review_scores_checkin",
               "review_scores_communication", "review_scores_location", "review_scores_value", "latitude", "longitude"]
    listings_df = listings_df[to_keep]

    # set index to id
    listings_df.set_index("id", inplace=True)

    # make host_response rate from 10% -> 0.1
    listings_df["host_response_rate"] = listings_df["host_response_rate"].str.strip('%')
    listings_df["host_response_rate"] = pd.to_numeric(listings_df["host_response_rate"]) / 100

    # remove dollar sign and comma
    cols = ['price', 'security_deposit', 'cleaning_fee']
    for col in cols:
        listings_df[col] = listings_df[col].str.strip('$')
        listings_df[col] = listings_df[col].str.replace(',', '')

    # write file
    write_csv(listings_df, "listing.csv")

    # ======================= preprocess for calendar_dec18.csv =========================
    print('preprocessing calendar_dec18.csv')

    calendar_file = data_dir + "calendar_dec18.csv"
    calendar_df = read_csv(calendar_file)

    # discard rows which have no price
    calendar_df.dropna(inplace=True)

    # discard column 'avaliable'
    calendar_df.drop(columns=['available'], inplace=True)

    # remove dollar sign
    calendar_df["price"] = calendar_df["price"].str.strip('$')
    listings_df[col] = listings_df[col].str.replace(',', '')


    # for debug
    # print(calendar_df.head(100).to_string())
    write_csv(calendar_df, "calendar.csv")

    print("====== Preprocess Finished ======")
