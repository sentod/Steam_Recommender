import asyncio
import time
import streamlit as st
import regex as re
import json
import streamlit.components.v1 as components
# from fuzzywuzzy import fuzz, process
import pandas as pd

import calculation
import getData

st.set_page_config(
    page_title="Steam Game Recommender",
    # page_icon="🧊",
    # layout="wide",
    # initial_sidebar_state="expanded",
    # menu_items={
    #     'Get Help': 'https://www.extremelycoolapp.com/help',
    #     'Report a bug': "https://www.extremelycoolapp.com/bug",
    #     'About': "# This is a header. This is an *extremely* cool app!"
    # }
)

@st.fragment
def minimum_req_input(minimum, i, hardwareDataset, userSteam):
    with st.form(f"minimum_requirements_form{i}", border=False):
        submitted = st.form_submit_button("Check Compatibiliy") 
        if submitted:
            spec_recomend = calculation.spec_recomendation(minimum, hardwareDataset, userSteam)
            if type(spec_recomend) is not str:
                st.progress(spec_recomend['cpu_ratio'], text=f"CPU Compability")
                st.progress(spec_recomend['gpu_ratio'], text=f"GPU Compability")
                st.progress(spec_recomend['memory_ratio'], text=f"Memory Compability")
                st.divider()
                st.progress(spec_recomend['final_ratio'], text=f"Final Compability {round(spec_recomend['final_ratio']*100, 2)}%")
                st.text(spec_recomend['result'])
            if type(spec_recomend) is str: st.text(spec_recomend)
                
            
# @st.fragment
def search_input(userSteam): 
    st.title("Steam Game Recommender")
    # if st.session_state['searching'] == False:
        # print('steam_id_input_label' in st.session_state)
    with st.form('search steam id'):
        input_label = "Insert your steamid"
        if 'steam_id_input_label' in st.session_state:
            input_label = st.session_state['steam_id_input_label']
        steam_id_input = st.text_input(input_label, placeholder="for example 76561197960435530 or yourid333")
        submitted = st.form_submit_button("Submit") 
        if submitted:
            print(steam_id_input)
            with st.spinner():
                if not getData.search_steamid(steam_id_input, userSteam):
                    # st.session_state['steam_id_input_label'] = "Cannot find your SteamID, try again"
                    # print(F"yeahg {'steam_id_input_label' in st.session_state}")
                    st.rerun()
                    return False
                else: 
                    # print("True")
                    st.session_state['steam_id_input_label'] = "Insert your steamid"
                    # st.session_state['success_search_id'] = True
                    # st.rerun(scope='fragment')
                    return True
                # return search_steamid(steam_id_input)

@st.fragment
def user_spec_input(hardwareDataset, userSteam):
    with st.container():
        left, middle, right = st.columns([2,2,1])
        with left:
            option_cpu = st.selectbox(
                "Select your CPU",
                hardwareDataset.cpu_dataset,
                index=None,
                placeholder="Search CPU...",
            )   
            userSteam.user_cpu = option_cpu
        with middle:
            option_gpu = st.selectbox(
                "Select your CPU",
                hardwareDataset.gpu_dataset,
                index=None,
                placeholder="Search GPU...",
            )   
            userSteam.user_gpu = option_gpu
        with right:
            option_memory = st.number_input(
            "Insert your RAM size", value=None, min_value= 0.5, step= 0.5, placeholder="Ram size in GB..."
        )
        userSteam.user_memory = option_memory

def user_summaries_widget(userSteam, gameDataset):
    st.session_state.current_page = 1
    user_game = getData.get_user_game(userSteam, gameDataset)
    if user_game is not None:
        calculation.calculate_user_profile(user_game, gameDataset, userSteam)
        with st.sidebar:
            with st.container():
                left, right = st.columns([1,2])
                with left:
                    st.image(userSteam.user_summaries[0]['avatarfull'])
                with right:
                    st.title(userSteam.user_summaries[0]['personaname'])
                st.text(f"Games owned: {len(userSteam.user_games)}")
                if userSteam.user_playtime > 0:
                    st.write(f'Total Playtime: {round(userSteam.user_playtime/60, 2)} hours')
                    top_3_games = []
                    for games in sorted(userSteam.user_games, key=lambda x: x.get('playtime_forever', 0), reverse=True)[:3]:
                        game_data = getData.search_appid(gameDataset, games['appid'])
                        if game_data is not None:
                            top_3_games.append(game_data['name'])
                    st.text(f"Most Played Games: {', '.join(top_3_games)}")
            with st.container(border=True):
                st.header('Genres Played')
                left, right = st.columns([1,1])
                with left:
                    st.subheader("Genres")
                with right:
                    st.subheader("Preference")
                for index, row in userSteam.user_favorite_genre.iterrows():
                    with st.container():
                        left, right = st.columns([1,1])
                        with left:
                            st.text(row['desc'])
                        with right:
                            st.progress(row['cosine'], text=f"{round(row['cosine']*100, 2)}%")
            with st.container(border=True):
                st.header('Categories Played')
                left, right = st.columns([1,1])
                with left:
                    st.subheader("Categories")
                with right:
                    st.subheader("Preference")
                for index, row in userSteam.user_favorite_categories.iterrows():
                    with st.container():
                        left, right = st.columns([1,1])
                    with left:
                        st.text(row['desc'])
                    with right:
                        st.progress(row['cosine'], text=f"{round(row['cosine']*100, 2)}%")
        return True
    else: 
        st.warning("Cannot get user games")
        return False
         
def recommendation_result(gameDataset, userSteam, hardwareDataset):
    calculation.recommendation_calculation(gameDataset, userSteam)
    st_test = pd.DataFrame(userSteam.user_recommendation)
    recomendation_page(st_test, userSteam, hardwareDataset)
    
def paginate_dataframe(df, page_number, items_per_page, total_items):
    start_index = (page_number - 1) * items_per_page
    end_index = min(start_index + items_per_page, total_items)

    return df.iloc[start_index:end_index].copy()
    
@st.fragment  
def recomendation_page(dataframe ,userSteam, hardwareDataset):
    total_items = len(dataframe)
    total_pages = (total_items + 10 - 1) // 10
    
    st_test = paginate_dataframe(dataframe, st.session_state.current_page, 10, total_items)
    placeholder = st.empty()
    with placeholder.container():
        for i in range(0, len(st_test), 2):
            row1 = st_test.iloc[i]
            if i + 1 < len(st_test):
                row2 = st_test.iloc[i + 1]
            else:
                row2 = None
            
            col1, col2 = st.columns(2)
            with col1:
                with col1.container():
                    game_card(row1, hardwareDataset, userSteam)
            if row2 is not None:
                with col2.container():
                    game_card(row2, hardwareDataset, userSteam)
    
    pagination_cols = st.columns([3, 2, 2, 2, 1]) # Adjust column ratios for layout
    
    with pagination_cols[1]:
        if st.button("Previous"):
            if st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                placeholder.empty()
                time.sleep(1)
                st.rerun(scope="fragment") # Rerun to update content

    # Display current page number (or a selectbox for direct jump)
    with pagination_cols[2]:
        # Using a selectbox for direct page jump as seen in the image's '1 2 3 ... 50'
        # For a large number of pages, a selectbox is more practical than many buttons.
        page_options = [str(i) for i in range(1, total_pages + 1)]
        selected_page_str = st.selectbox(
            "Page",
            options=page_options,
            index=st.session_state.current_page - 1, # Adjust index to be 0-based
            label_visibility="collapsed",
            key="page_selector"
        )
        # Update current_page if a different page is selected from the dropdown
        if st.session_state.current_page != int(selected_page_str):
            st.session_state.current_page = int(selected_page_str)
            placeholder.empty()
            time.sleep(1)
            st.rerun(scope="fragment")

    with pagination_cols[3]:
        if st.button("Next"):
            if st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                placeholder.empty()
                time.sleep(1)
                st.rerun(scope="fragment") # Rerun to update content

    with pagination_cols[4]:
        st.write(f"Page {st.session_state.current_page} of {total_pages}")  

# @st.fragment 
def game_price(appid):
    with st.spinner("getting price..."):
        price = getData.get_games_price(appid)
    if price:
        if 'data' in price[str(appid)]:
            gamePrice = price[str(appid)]['data']
            if type(gamePrice) == dict :
                if gamePrice['price_overview']['discount_percent'] > 0 :
                    st.markdown(f''' 
                                :green[{gamePrice["price_overview"]['final_formatted']}] (:green[{gamePrice['price_overview']['discount_percent']}% off])
                                ''')
                else: st.text(gamePrice["price_overview"]['final_formatted'])
            else: st.text("Free")
        else: st.text("cannot get price")
        # st.success("Data fetched successfully!")
    # elif 'data' not in price[str(appid)]:
    #     st.text("cannot get price")
    else:
        st.text("cannot get price")
        # st.rerun(scope="fragment")
   
def game_card(data, hardwareDataset, userSteam):
    st.image(data['header_image'], caption=data['name'])
    st.progress(data['cosine'], text=f"Preference Compatibility: {round(data['cosine']*100, 2)}%")
    with st.container():
        left, right = st.columns([1,1])
        with left:
            game_price(data['steam_appid'])
        with right:
            st.link_button("Go to store page", f"https://store.steampowered.com/app/{data['steam_appid']}")
    with st.container():
        left, right = st.columns([2,5])
        with left:
            st.caption('Genres')
        with right:
            st.text(', '.join(data['genres']))
    with st.container():
        left, right = st.columns([2,5])
        with left:
            st.caption('Categories')
        with right:
            st.text(', '.join(data['categories']))
    with st.expander("Minimum Spesification"):
        left, right = st.columns([1,1])
        for name, value in get_spec_recomendation(data['minimum_req']).items():
            with st.container():
                left, right = st.columns([1,1])
                with left:
                    st.caption(name)
                with right:
                    st.text(value)
        minimum_req_input(data['minimum_req'], data['name'], hardwareDataset, userSteam)      
    st.divider()          
                    
def get_spec_recomendation(minimum):
    b = re.sub(r"[\[\]']", '', minimum)
    a = json.loads(b)
    return a
