import datetime
import requests
import pandas as pd
from io import StringIO
from config import *

phishtank_baseapi = "https://checkurl.phishtank.com/checkurl/"
phishtank_db_url = f"http://data.phishtank.com/data/{phishtank_api_key}/online-valid.csv"
phish_init_url = "https://phishing-initiative.lu/api/"


def openphish_update():  # Updated every 12 hours
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    response = requests.get("https://openphish.com/feed.txt")

    if response.status_code == 200:
        openphish_feed = response.text.split('\n')

        df_openphish = pd.DataFrame(columns=['URL', 'Source'])

        df_openphish['URL'] = openphish_feed
        df_openphish = df_openphish.drop_duplicates(subset='URL', keep='first')
        df_openphish['URL'] = df_openphish['URL'].str.lower()

        df_openphish['Source'] = 'openphish'
        df_openphish['Date'] = timestamp
        df_openphish['Notes'] = 'Free Dataset'
        df_openphish['Target'] = 'Other'
        df_openphish['IP'] = 'N/A'

        return df_openphish


def phishstats_update():  # Updated every 1.5 hours
    response = requests.get("https://phishstats.info/phish_score.csv")

    if response.status_code == 200:
        data = StringIO(response.content.decode("utf-8"))
        df_phishstats = pd.read_csv(data, skiprows=9)

        df_phishstats.columns = ["Date", "Notes", "URL", "IP"]

        df_phishstats['URL'] = df_phishstats['URL'].str.lower()
        df_phishstats = df_phishstats.drop_duplicates(subset='URL', keep='first')  # Remove duplicate URL's
        df_phishstats = df_phishstats[~df_phishstats['Date'].str.contains(',')]  # Remove anomalies

        # Establish standardized columns
        df_phishstats['Notes'] = 'Score: ' + df_phishstats['Notes'].astype(str)
        df_phishstats['Source'] = 'phishstats'
        df_phishstats['Target'] = 'Other'

        return df_phishstats


def phishtank_update():  # Updated every 1 hour
    phishtank_cols = ['url', 'phish_detail_url', 'submission_time', 'target']  # Expected columns

    df_phishtank = pd.read_csv(phishtank_db_url, usecols=phishtank_cols)  # Read csv into dataframe from url

    # Standardize our column names
    df_phishtank.rename(columns={"url": "URL", "phish_detail_url": "Notes",
                                 "submission_time": "Date", "target": "Target"},
                        inplace=True)

    df_phishtank['URL'] = df_phishtank['URL'].str.lower()
    df_phishtank = df_phishtank.drop_duplicates(keep='first', subset='URL')  # Get rid of duplicate URL's
    df_phishtank['Source'] = 'phishtank'  # Tag data with source

    return df_phishtank


def primary_db_update():
    # Gather our initial dataframes from all available sources
    df_openphish = openphish_update()
    df_phishstats = phishstats_update()
    df_phishtank = phishtank_update()

    # Create primary dataframe from our component dataframes
    df_primary = df_openphish.append(df_phishstats)
    df_primary = df_primary.append(df_phishtank)

    # Try and append dataframe based on established data - Move on otherwise
    try:
        prev_primary = pd.read_csv('primary.csv')
        df_primary = df_primary.append(prev_primary)
    except FileNotFoundError:
        pass

    df_primary['URL'] = df_primary['URL'].str.lower()
    df_primary = df_primary.drop_duplicates(subset='URL', keep='first')  # Filter out any duplicate URL's
    df_primary['Date'] = pd.to_datetime(df_primary['Date'])  # Make sure our date is in ISO 8601

    df_primary.to_csv('primary.csv', index=False)  # Write primary dataframe to disk as a csv

    return df_primary


def primary_db_search(search_term, column, dataframe):
    results = dataframe[dataframe[column].str.contains(search_term, na=False)]

    return results


def primary_db_aggregate(csv):
    df_raw = pd.read_csv(csv)

    df_aggregate = df_raw.groupby('Target').agg({'URL': 'nunique'}).reset_index()  # Aggregate targets by attempts

    df_aggregate = df_aggregate.sort_values('URL', ascending=False)

    return df_aggregate


def phishtank_query(phishing_url):
    payload = {
        "url": phishing_url,
        "format": "json",
        "app_key": phishtank_api_key
    }

    response = requests.post(phishtank_baseapi, data=payload)

    if response.status_code == 200:
        return response.json()
    else:
        print(response.headers)
        print(response.text)


def phish_init_check(phishing_url):
    headers = {
        "Authorization": f"Token {phish_init_api_key}"
    }

    response = requests.get(phish_init_url + "v1/urls/lookup", headers=headers,
                            params={"url": phishing_url})

    if response.status_code == 200:
        return response.json()
    else:
        print(response.headers)
        print(response.text)


primary_db_update()
