import time
import requests
import streamlit as st
from collections import deque
import ast
import json

import loadData

def user_api(id): 
    return f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=798368E586087D516B3A48D720A0B572&steamid={id}&format=json'
def user_summaries(id):
    return f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=798368E586087D516B3A48D720A0B572&steamids={id}'
def user_custom(id):
    return f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=798368E586087D516B3A48D720A0B572&vanityurl={id}'
def detail_game_url(appid):
    return f"https://store.steampowered.com/api/appdetails/?appids={appid}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

def search_steamid(id, userSteam):
    # st.session_state['searching'] = True
    # id = st.session_state.steam_id_input
    try:
        print('searching steam account')
        response1 = requests.get(user_custom(id), timeout=30) 
        data = (response1.json())['response']
        if data.get("steamid", {}):
            print(f'getting userid :{data["steamid"]}')
            isDone = False
            while not isDone:
                response2 = requests.get(user_api(data['steamid']), timeout=30)
                if response2.status_code == 429:
                    isDone = False
                    time.sleep(5)
                else: isDone = True
            isDone = False
            while not isDone:
                response3 = requests.get(user_summaries(data['steamid']), timeout=30)
                if response3.status_code == 429:
                    isDone = False
                    time.sleep(5)
                    # return False
                else: isDone = True
        else:
            print(f'getting steamid :{id}')
            isDone = False
            while not isDone:
                response2 = requests.get(user_api(id), timeout=30)
                if response2.status_code == 429:
                    isDone = False
                    time.sleep(5)
                else: isDone = True
            isDone = False
            while not isDone:
                response3 = requests.get(user_summaries(id), timeout=30)
                if response3.status_code == 429:
                    isDone = False
                    time.sleep(5)
                    # return False
                else: isDone = True
        data2 = (response2.json())['response']
        data3 = (response3.json())['response']
        if(data2.get('games', {})):
            userSteam.user_games = data2['games']
        if(data3.get('players', {})):
            userSteam.user_summaries = data3['players']
        # print(data3.get('players', {}))
        return True
        # st.session_state['searching'] = False
    except Exception as e: # Catches pandas errors too
        # st.experimental_rerun()
        print(f"An unexpected error occurred: {e}")
        st.session_state['steam_id_input_label'] = "Cannot find your SteamID, try again"
        return False
        # print(st.session_state['steam_id_input_label'])
        # st.session_state['searching'] = False
        
def get_user_game(userSteam, gameDataset):
    playtime = 0
    owned_game_data = []
    progress_text = 'getting all user games'
    initial_df_progress = st.progress(0, text=progress_text)
    user_games = deque(userSteam.user_games)
    index = 0
    print(gameDataset.ignored_games_dataset)
    while len(user_games) > 0:
        games = user_games.popleft()
        initial_df_progress.progress(index/len(userSteam.user_games), progress_text)
        try:
            is_in_dataset_game = gameDataset.games_dataset[gameDataset.games_dataset['steam_appid'] == int(games['appid'])]
            is_in_ignored_dataset_game = gameDataset.ignored_games_dataset[gameDataset.ignored_games_dataset['appid'] == int(games['appid'])]
            if not is_in_dataset_game.empty:
                data_game = gameDataset.games_dataset.iloc[is_in_dataset_game.index[0]].to_dict()
            elif is_in_dataset_game.empty and is_in_ignored_dataset_game.empty:
                response2 = requests.get(detail_game_url(games['appid']), headers=headers)
                if response2.status_code == 200:
                    data_game = (response2.json())[str(games['appid'])]
                    if data_game.get('data', {}):
                        data_game = (response2.json())[str(games['appid'])]['data']
                        loadData.add_games_to_csv(data_game, games['appid'])
                    else:
                        loadData.add_games_to_unsuccess_csv(games['appid'])
                        data_game = None
                elif response2.status_code == 429:
                    user_games.appendleft(games)
                    print(f"Too many requests. Put App ID {games['appid']} back to deque. Sleep for 10 sec")
                    time.sleep(10)
                    data_game = None
                    continue
            try:
                if data_game is not None:
                    owned_game_genres = []
                    if data_game.get('genres'):
                        if type(data_game['genres']) == str:
                            data_game['genres'] = ast.literal_eval(data_game['genres'])
                        if type(data_game['genres']) == list:
                            for game_genres in data_game['genres']:
                                owned_game_genres.append('1.'+game_genres['id'])
                        # print(index)
                    if data_game.get('categories'):
                        if type(data_game['categories']) == str:
                                data_game['categories'] = ast.literal_eval(data_game['categories'])
                        if type(data_game['categories']) == list:
                            for game_categories in data_game['categories']:
                                owned_game_genres.append('2.'+str(game_categories['id']))
                    owned_game_genres = list(map(float, set(owned_game_genres)))
                    data_game_result = {}
                    data_game_result['genres'] = owned_game_genres
                    data_game_result['playtimeInMinutes'] = games['playtime_forever']
                    owned_game_data.append(data_game_result)
                    # print(owned_game_genres)
            except json.JSONDecodeError:
                print("Error: Could not decode JSON response.")
                # print("Response Text:", response.text)
                exit()
        except Exception as e: # Catches pandas errors too
            print(f"An unexpected error occurred: {e} {type(data_game.get('genres', {}))}../")
            data_game = None 
            continue  
        playtime += games["playtime_forever"]
        userSteam.user_playtime = playtime
        index += 1
    initial_df_progress.empty()
    return owned_game_data

def search_appid(gameDataset, appid):
    is_in_dataset_game = gameDataset.games_dataset[gameDataset.games_dataset['steam_appid'] == int(appid)]
    if not is_in_dataset_game.empty:
        return gameDataset.games_dataset.iloc[is_in_dataset_game.index[0]].to_dict()
    else : return {}
