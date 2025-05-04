import pandas as pd
import streamlit as st
import requests
import json
from howlongtobeatpy import HowLongToBeat

def get_db_connection(db_name):
    conn = st.connection(db_name, type='sql')
    return conn


class GamingDashboard:

    def __init__(self, database_connection, giantbomb_api_key):
        self.db_conn = database_connection
        self.gb_key = giantbomb_api_key
        self.playing_dict = dict()


    def get_giantbomb_details(self, game_id):
        giantbomb_id = self.db_conn.query(f"SELECT giantbomb_id FROM game_info WHERE game_id={game_id}")
        resource_type = 'game'
        resource_id = giantbomb_id.values[0][0]
        response_data_format = 'json'
        field_list = 'deck,image,name,site_detail_url'

        # Getting game resource from Giantbomb
        url = f"http://www.giantbomb.com/api/{resource_type}/{resource_id}/?api_key={self.gb_key}&format={response_data_format}&field_list={field_list}"
        headers = {'User-Agent': 'LaggyHammer Personal'}
        response = requests.request("GET", url, headers=headers)
        gb_data = json.loads(response.text)

        gb_game_details = dict()
        if gb_data.get('error') == 'OK':
            game_brief = gb_data.get('results').get('deck')
            game_icon_url = gb_data.get('results').get('image').get('icon_url')
            game_url = gb_data.get('results').get('site_detail_url')

            gb_game_details['game_brief'] = game_brief
            gb_game_details['game_icon_url'] = game_icon_url
            gb_game_details['game_url'] = game_url

        return gb_game_details

    def get_howlongtobeat_data(self, game_id):

        game_title = self.db_conn.query(f"SELECT name FROM game_info WHERE game_id={game_id}").values[0][0]

        hltb_game_details = dict()
        # Making request
        results_list = HowLongToBeat().search(game_name=game_title)
        if results_list is not None and len(results_list) > 0:
            best_element = max(results_list, key=lambda element: element.similarity)
            hltb_game_details['main_story'] = best_element.main_story
            hltb_game_details['main_plus_extra'] = best_element.main_extra
            hltb_game_details['completionist'] = best_element.completionist

        return hltb_game_details

    def get_playing_table(self):
        topline_queries = {'status_wise_counts': "SELECT status, COUNT(game_id) AS no_of_games FROM game_status GROUP BY status;",
                           'playing_games_details':"SELECT gs.game_id, gs.date, gi.giantbomb_id, gi.name FROM game_status gs JOIN game_info gi ON gs.game_id = gi.game_id WHERE gs.status = 'playing';"}

        # Status-wise Counts
        status_wise_counts = self.db_conn.query(topline_queries['status_wise_counts'])
        status_wise_counts = status_wise_counts.set_index('status')
        playing_count = status_wise_counts.at['playing', 'no_of_games']
        rolled_credits_count = status_wise_counts.at['rolled_credits', 'no_of_games']

        # Playing Games' Details
        playing_games_details = self.db_conn.query(topline_queries['playing_games_details'])
        playing_games_details['date'] = pd.to_datetime(playing_games_details.date)
        









def get_topline_section(db_connection):
    topline_queries = {'status_wise_counts': 'SELECT status, COUNT(game_id) AS no_of_games FROM game_status GROUP BY status;'}
    status_wise_counts = db_connection.query(topline_queries['status_wise_counts'])
    status_wise_counts = status_wise_counts.set_index('status')
    playing = status_wise_counts.at['playing', 'no_of_games']
    rolled_credits = status_wise_counts.at['rolled_credits', 'no_of_games']
    st.write(f'Playing {playing} game(s) right now. Rolled credits on {rolled_credits} games.')
    with st.expander("See Counts"):
        st.dataframe(status_wise_counts)

def get_giantbomb_link(game_id):
    raise NotImplementedError




# def
if __name__ == "__main__":
    db_conn = get_db_connection('games_database')
    giantbomb_api_key = st.secrets.api_keys.giantbomb
    st.title('Hi LaggyHammer!')

    st.header('At A Glance')
    get_topline_section(db_conn)
