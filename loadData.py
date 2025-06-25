import pandas as pd
import streamlit as st
import ast
import csv


import helper

csv_data = 'datasets/steam_games_2.csv'
ignored_csv_file = "datasets/ignored_steam_games.csv"
csv_data_cpu = 'datasets/cpu_dataset.csv'
csv_data_gpu = 'datasets/gpu_dataset.csv'


def load_dataframe(hardwareDataset, gameDataset):
    try:
        df = pd.read_csv(csv_data)
        df3 = pd.read_csv(ignored_csv_file)
        df2 = pd.read_csv(csv_data_cpu)
        df4 = pd.read_csv(csv_data_gpu)
        hardwareDataset.cpu_dataset = df2
        hardwareDataset.gpu_dataset = df4
        gameDataset.games_dataset = df
        gameDataset.ignored_games_dataset = df3
        df2['CPU Mark(higher is better)'] = df2['CPU Mark(higher is better)'].astype(str).str.replace(',', '')
        df2['CPU Mark(higher is better)'] = pd.to_numeric(df2['CPU Mark(higher is better)'])
        df2 = df2.sort_values(by='CPU Mark(higher is better)', ascending=True)
    except FileNotFoundError:
        print(f"Error: File not found at '{csv_data}'")
    except Exception as e:
        print(f"An error occurred: {e}")
        
def extract_genres_categories(gameDataset):
    progress_text = 'Loading all genres'
    initial_df_progress = st.progress(0, text=progress_text)
    genres = gameDataset.games_dataset['genres']
    categories = gameDataset.games_dataset['categories']
    all_genres = [ ]
    gameDataset.all_genres = [ ]
    gameDataset.all_categories = [ ]
    extracted_genres = [ ]
    extracted_categories = [ ]
    i = 0
    for item in genres:
        initial_df_progress.progress((i)/len(genres), progress_text)
        if type(item) == str:
            game_genres = pd.Series(item for item in ast.literal_eval(genres[i]))
            for game_genres in game_genres:
                extracted_genres.append([int(game_genres['id']),game_genres['description']])
                all_genres.append('1.'+game_genres['id'])
        i += 1
    j = 0
    progress_text = 'Loading all categories'
    for item2 in categories:
        initial_df_progress.progress((j)/len(categories), progress_text)
        if type(item2) == str:
            game_categories = pd.Series(item2 for item2 in ast.literal_eval(categories[j]))
            for game_categories in game_categories:
                extracted_categories.append([game_categories['id'],game_categories['description']])
                str(game_categories)
                all_genres.append('2.'+str(game_categories['id']))
        j += 1
    all_genres = list(map(float, set(all_genres)))
    all_genres.sort()
    seen = set()
    for item in extracted_genres:
        first_value = item[0]
        if first_value not in seen:
            gameDataset.all_genres.append(item)
            seen.add(first_value)
    for item in extracted_categories:
        first_value = item[0]
        if first_value not in seen:
            gameDataset.all_categories.append(item)
            seen.add(first_value)
    gameDataset.all_genres_categories = all_genres
    gameDataset.all_genres.sort()
    gameDataset.all_categories.sort()
    initial_df_progress.empty()
    
def add_games_to_csv(data2, appid):
    if data2['steam_appid'] == appid and data2['type'] == "game" and data2.get('release_date', {}).get('coming_soon') == False and ((data2['is_free'] == False and data2.get('recommendations', {})) or data2['is_free'] == True) and (data2.get('genres', {}) or data2.get('categories', {})) and data2.get('pc_requirements', {}).get('minimum'):
        print(f"Current game is {data2['steam_appid']}")
        currDataGame = {}
        currDataGame["name"] = data2['name']
        currDataGame["steam_appid"] = data2['steam_appid']
        currDataGame["is_free"] = data2['is_free']
        currDataGame["header_image"] = data2['header_image']
        # print(html_to_json(data2['pc_requirements']['minimum']))
        currDataGame["minimum_req"] = [helper.html_to_json(data2['pc_requirements']['minimum'])]
        if data2.get('genres', {}):
            currDataGame["genres"] = data2['genres']
        else: currDataGame["genres"] = ''
        if data2.get('categories', {}):
            currDataGame["categories"] = data2['categories']
        else: currDataGame["categories"] = ''
        if currDataGame["is_free"] == False :
            currDataGame["recommendations"] = data2['recommendations']['total']
        else: currDataGame["recommendations"] = ''
        currDataGame["release_date"] = data2['release_date']['date']
        records = [ ]
        records.append(currDataGame)
        dfa = pd.DataFrame(records)
        dfa.to_csv(csv_data, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
    else:
        add_games_to_unsuccess_csv(appid)
    
def add_games_to_unsuccess_csv(appid):
    unsuccess = [ ]
    unsuccess.append(appid)
    df2 = pd.DataFrame(unsuccess)
    df2.to_csv(ignored_csv_file, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
    print(f"Failed to get game data {appid}, stored in another dataset")
    
