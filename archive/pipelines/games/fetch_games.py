import time
import os
import cfbd
from cfbd.models.division_classification import DivisionClassification
from cfbd.models.game import Game
from cfbd.models.season_type import SeasonType
from cfbd.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv
import pandas as pd
import logging

# Load environment variables from .env file
load_dotenv()

# Defining the host is optional and defaults to https://api.collegefootballdata.com
# See configuration.py for a list of all supported configuration parameters.
configuration = cfbd.Configuration(
    host = "https://api.collegefootballdata.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: apiKey
configuration = cfbd.Configuration(
    access_token = os.getenv("BEARER_TOKEN")
)

# Enter a context with an instance of the API client
with cfbd.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = cfbd.GamesApi(api_client)
    classification = cfbd.DivisionClassification("fbs")
    start_year = 2004
    end_year = 2025

    # Initialize empty dataframe
    df = pd.DataFrame()

    # Loops from start_year through end_year and append new dataframe
    for year in range(start_year,end_year):
        try:
            logging.info("Calling Games API for year {}".format(year))
            api_response = api_instance.get_games(year=year, classification=classification)
            games_dicts = [g.to_dict() for g in api_response]
            new_df = pd.DataFrame(games_dicts)
            df = pd.concat([df, new_df], ignore_index=True)
        except Exception as e:
            logging.error("Exception when calling GamesApi->get_games: %s\n" % e)
    
    # Save to CSV
    df.to_csv("data/raw/games_raw.csv", index=False)