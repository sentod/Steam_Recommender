import json
import re
from fuzzywuzzy import fuzz, process
import streamlit as st
import pandas as pd
import ast
from scipy.spatial.distance import cosine

def calculate_user_profile(owned_game_data, gameDataset, userSteam):
    # data = (response.json())['response']['games']
    # data_user = (response_user_summaries.json())['response']['players']
    # print(data_user)
    
    # print(owned_game_data)

    user_profile = []
    progress_text = 'calculating user profile'
    initial_df_progress = st.progress(0, text=progress_text)
    # initial_df_progress = st.progress(0, text=progress_text)
    for index, owned_games in enumerate(owned_game_data):
        initial_df_progress.progress(index/len(owned_game_data), progress_text)
        game_one_hot = []
        for each_genres in gameDataset.all_genres_categories:
            one_hot_genres = {}
            if userSteam.user_playtime == 0 :
                weight = 1
            else: weight = owned_games['playtimeInMinutes']/userSteam.user_playtime
            for owned_games_genres in owned_games['genres']:
                if each_genres in owned_games['genres']:
                    one_hot_genres['count'] = 1
                    one_hot_genres['profile'] = 1*weight
                    one_hot_genres['genres'] = each_genres
                elif len(one_hot_genres)==0:
                    one_hot_genres['count'] = 0
                    one_hot_genres['profile'] = 0*weight
                    one_hot_genres['genres'] = each_genres
                elif one_hot_genres['count']>0 :
                    one_hot_genres['count'] = 1
                    one_hot_genres['profile'] = 1*weight
                    one_hot_genres['genres'] = each_genres
            game_one_hot.append(one_hot_genres)
        if len(user_profile)==0:
            user_profile = game_one_hot
        else:
            i=0
            for a in game_one_hot:
                user_profile[i]['count'] += a['count']
                if userSteam.user_playtime == 0:
                    user_profile[i]['profile'] = user_profile[i]['count']
                else: user_profile[i]['profile'] += a['profile'] 
                # print(user_profile)
                i += 1
    userarray_profile = []
    # print(len(owned_game_data))
    # print(user_profile)
    for profile in user_profile:
        if userSteam.user_playtime == 0:
            profile['profile'] /= len(owned_game_data)
        userarray_profile.append(profile['profile'])
    
    userSteam.user_favorite_genre = []
    userSteam.user_favorite_categories = []
    # print([list(row) for row in zip(*[gameDataset.all_genres_categories, userarray_profile])])
    for item in [list(row) for row in zip(*[gameDataset.all_genres_categories, userarray_profile])]:
        # tempgenres = []
        # tempcategories = []
        getid = str(item[0]).split(".")
        # print(getid)
        if getid[0] == '1':
            for item2 in gameDataset.all_genres:
                if getid[1] == str(item2[0]) and item[1]>0:
                    # tempgenres.append([getid[1], item2[1], item[1]])
                    userSteam.user_favorite_genre.append([getid[1], item2[1], item[1]])
            # print(userSteam.user_favorite_genre)
        elif getid[0] == '2':
            for item2 in gameDataset.all_categories:
                if getid[1] == str(item2[0]) and item[1]>0:
                    # tempcategories.append([getid[1], item2[1], item[1]])
                    userSteam.user_favorite_categories.append([getid[1], item2[1], item[1]])
    
    userSteam.user_favorite_genre = pd.DataFrame(userSteam.user_favorite_genre, columns=['id', 'desc', 'cosine']).sort_values('cosine', ascending=False)
    userSteam.user_favorite_categories = pd.DataFrame(userSteam.user_favorite_categories, columns=['id', 'desc', 'cosine']).sort_values('cosine', ascending=False)
    userSteam.user_profile = userarray_profile
    initial_df_progress.empty()
    # print(userarray_profile)
    
def recommendation_calculation(gameDataset, userSteam):    
    cosine_all_games = []
    # print(df[0])
    progress_text = 'calculating recommendation for games'
    initial_df_progress = st.progress(0, text=progress_text)
    user_unowned_games_filter = pd.DataFrame(gameDataset.games_dataset[~gameDataset.games_dataset['steam_appid'].isin([game['appid'] for game in userSteam.user_games])])
    i = 0
    for row in user_unowned_games_filter.itertuples():
        initial_df_progress.progress(i/len(gameDataset.games_dataset), progress_text)
        game_profile = {}
        game_profile['name'] = row.name
        game_profile['header_image'] = row.header_image
        game_profile['steam_appid'] = row.steam_appid
        game_profile['minimum_req'] = row.minimum_req
        game_profile['genres'] = []
        game_profile['categories'] = []
        game_profile['profile'] = []
        gamearray_profile = []
        id_genres_game = []
        if type(row.genres) == str:
            df_game_genres = pd.Series(ast.literal_eval(row.genres))
            for d in df_game_genres:
                id_genres_game.append(float('1.'+d['id']))
                game_profile['genres'].append(d['description'])
        if type(row.categories) == str:
            df_game_categories = pd.Series(ast.literal_eval(row.categories))
            game_profile['categories'].append(d['description'])
            for dd in df_game_categories:
                id_genres_game.append(float('2.'+str(dd['id'])))
        for each_genres in gameDataset.all_genres_categories:
            # print(type(row.genres))
            one_hot_games_profile = {}
            for games_genres in id_genres_game:
                if each_genres in id_genres_game:
                    one_hot_games_profile['count'] = 1
                    one_hot_games_profile['genres'] = each_genres
                elif len(one_hot_games_profile)==0:
                    one_hot_games_profile['count'] = 0
                    one_hot_games_profile['genres'] = each_genres
                elif one_hot_games_profile['count']>0 :
                    one_hot_games_profile['count'] = 1
                    one_hot_games_profile['genres'] = each_genres
            game_profile['profile'].append(one_hot_games_profile)
        for profile in game_profile['profile']:
            gamearray_profile.append(profile['count'])
        # print(len(gamearray_profile))    
        cosine_distance = cosine(userSteam.user_profile, gamearray_profile)
        cosine_similarity = 1 - cosine_distance
        game_profile['cosine'] = cosine_similarity
        # print(f"Cosine Similarity (from SciPy): {cosine_similarity}")
        cosine_all_games.append(game_profile)
        i += 1
    sort_by_cosine = sorted(cosine_all_games, key=lambda item: item['cosine'], reverse=True)
    userSteam.user_recommendation = sort_by_cosine
    initial_df_progress.empty()
    
    
                    
    #     st_test.head(10),
    #     column_config={
    #         "header_image": st.column_config.ImageColumn("Product Image", help="Image of the product"),
    #         "profile": None
    #     },
    #     hide_index=True,
    # )
    # for i in range(10):
    #     print(sort_by_cosine[i]['steam_appid'])    
    #     print(sort_by_cosine[i]['cosine'])    
        
    # print(one_hot_all_games[0])
    # for each_one_hot_game in game_one_hot:
    #     user_profile['weight'] += each_one_hot_game['profile']
    #     user_profile['genre'] = each_one_hot_game['genres']

def spec_recomendation(minimum, hardwareDataset, userSteam):
    b = re.sub(r"[\[\]']", '', minimum)
    a = json.loads(b)
    if a.get('Processor'):
        delimiters = [" or ", " and above "]
        pattern = '|'.join(re.escape(d) for d in delimiters)
        parts = re.split(pattern, a['Processor'])
        processors = [part.strip() for part in parts if part.strip()]
        # processors = a['Processor'].split(" or ")
        list_cpu = hardwareDataset.cpu_dataset['CPU Name'].tolist()
        list_gpu = hardwareDataset.gpu_dataset['Videocard Name'].tolist()
        best_match, score = process.extractOne(processors[0], list_cpu, scorer=fuzz.token_set_ratio)
        if score >= 80:  # Adjust threshold as needed
            minimum_cpu = best_match
            result_cpu = best_match
        else:
            minimum_cpu = processors[0]
            result_cpu = None
        print(score)
        print(minimum_cpu)
    else: result_cpu = None
    if a.get('Graphics'):
        delimiters = [" or ", " and above ", "  ", "nvidia"]
        pattern = '|'.join(re.escape(d) for d in delimiters)
        parts = re.split(pattern, a['Graphics'].lower())
        gpu = [part.strip() for part in parts if part.strip()]
        list_gpu = hardwareDataset.gpu_dataset['Videocard Name'].tolist()
        best_match, score = process.extractOne(gpu[0], list_gpu, scorer=fuzz.token_set_ratio)
        if score >= 80:  # Adjust threshold as needed
            minimum_gpu = best_match
            result_gpu = best_match
        else:
            minimum_gpu = gpu[0]
            result_gpu = None
        print(score)
        print(minimum_gpu)
    else: result_gpu = None
    if a.get('Memory'):
        memory = a['Memory'].split(" ")
        if memory[0].isdigit():
            if memory[1].lower() == 'mb':
                result_memory = int(memory[0]) / 1000
            if memory[1].lower() == 'gb':
                result_memory = int(memory[0])
        else: result_memory = None
    else: result_memory = None

    if result_cpu is not None and result_gpu is not None and result_memory is not None and userSteam.user_cpu is not None and userSteam.user_gpu is not None and userSteam.user_memory is not None:
        cpu_weight = 0.4
        gpu_weight = 0.3
        memory_weight = 0.3
        
        user_cpu_mark = hardwareDataset.cpu_dataset[hardwareDataset.cpu_dataset['CPU Name'] == userSteam.user_cpu]
        game_cpu_mark = hardwareDataset.cpu_dataset[hardwareDataset.cpu_dataset['CPU Name'] == result_cpu]
        user_gpu_mark = hardwareDataset.gpu_dataset[hardwareDataset.gpu_dataset['Videocard Name'] == userSteam.user_gpu]
        game_gpu_mark = hardwareDataset.gpu_dataset[hardwareDataset.gpu_dataset['Videocard Name'] == result_gpu]
        
        cpu_mark_range = sorted([user_cpu_mark['CPU Mark(higher is better)'].item(), game_cpu_mark['CPU Mark(higher is better)'].item()])
        gpu_mark_range = sorted([user_gpu_mark['Passmark G3D Mark (higher is better)'].item(), game_gpu_mark['Passmark G3D Mark (higher is better)'].item()])
        memory_range = sorted([userSteam.user_memory, result_memory])
        
        # cpu_normalization = (user_cpu_mark['CPU Mark(higher is better)'].item() - cpu_mark_range[0])/(cpu_mark_range[1] - cpu_mark_range[0])
        # gpu_normalization = (user_gpu_mark['Passmark G3D Mark (higher is better)'].item() - gpu_mark_range[0])/(gpu_mark_range[1] - gpu_mark_range[0])
        # memory_normalization = (userSteam.user_memory - memory_range[0])/(memory_range[1] - memory_range[0])
        
        cpu_normalization = user_cpu_mark['CPU Mark(higher is better)'].item() / cpu_mark_range[1]
        gpu_normalization = user_gpu_mark['Passmark G3D Mark (higher is better)'].item() / gpu_mark_range[1]
        memory_normalization = userSteam.user_memory / memory_range[1]
        
        return {
            'cpu_ratio' : cpu_normalization,
            'gpu_ratio' : gpu_normalization,
            'memory_ratio' : memory_normalization,
            'final_ratio' : cpu_normalization*cpu_weight + gpu_normalization*gpu_weight + memory_normalization*memory_weight
        }
        # print(cpu_ratio)
        # print(gpu_ratio)
        # print(memory_ratio)
        # print(cpu_ratio*cpu_weight + gpu_ratio*gpu_weight + memory_ratio*memory_weight)
    elif result_cpu is None or result_gpu is None or result_memory is None: return 'Cannot Retrieve Minimum Specification Data'
    elif userSteam.user_cpu is None or userSteam.user_gpu is None or userSteam.user_memory is None : return 'Please Input Your Specification'