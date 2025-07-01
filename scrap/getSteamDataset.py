import requests
import pandas as pd
import time
import csv
from collections import deque
import regex as re
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import json # Sometimes needed

# --- Configuration ---
firstTimeGameSet = False
firstTimeGameIgnored = False
initial = 3396560
# initial = 2694480
isContinue = True
count = 10000
game_list_url = f"https://api.steampowered.com/IStoreService/GetAppList/v1/?key=798368E586087D516B3A48D720A0B572&include_dlc=false&include_software=false&include_videos=false&include_hardware=false&last_appid={initial}&max_results={count}"  # Replace with the actual API URL
def detail_game_url(appid):
    return f"https://store.steampowered.com/api/appdetails/?appids={appid}"
# print(game_list_url)
output_csv_file = "steam_games.csv"
output_ignored_csv_file = "ignored_steam_games.csv"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.9',
} # Add headers if needed
params = { } # Add params if needed
def remove_symbols_and_punctuation_regex(text):
    """Removes all symbol and punctuation characters using regular expressions."""
    return re.sub(r'\(TM\)|\(R\)|[^\w\s.@-]', '', text)
def html_to_json(html_str):
    soup = BeautifulSoup(html_str, 'html.parser')
    requirements = {}
    for li in soup.find_all('li'):
        text = li.get_text(strip=True)
        
        if ':' in text:
            key, value = text.split(':', 1)
            value = remove_symbols_and_punctuation_regex(value)
            requirements[key.strip('*:')] = value.strip()
            
        elif 'Requires' in text:
            requirements['Requires'] = text.strip()
    # print(json.dumps(requirements))
    return json.dumps(requirements)

# def remove_html_tags_using_parser(html_string):
#     """Removes HTML tags using HTMLParser."""
#     class HTMLFilter(HTMLParser):
#         text = ""
#         def handle_data(self, data):
#             self.text += data

#     parser = HTMLFilter()
#     parser.feed(html_string)
#     return parser.text
# def remove_html_tags_and_special_chars(html_string):
#     """Removes HTML tags and decodes HTML entities."""
#     from html import unescape

#     clean_text = remove_html_tags_using_parser(html_string)
#     return  unescape(clean_text).replace('\n', ' ').replace('\r', ' ')
# post_data = { } # Add data for POST if needed

# --- Make the API Request ---
try:
    # For GET requests:
    response = requests.get(game_list_url, headers=headers, params=params, timeout=30)

    # For POST requests (uncomment):
    # response = requests.post(api_url, headers=headers, json=post_data, timeout=30)

    response.raise_for_status() # Check for HTTP errors

    # --- Process the Response ---
    try:
        data = response.json()
        if data.get('response',{}).get('last_appid',{}):
            initial = data['response']['last_appid']
            if data['response']['have_more_results'] == False:
                exit()
        else: initial = "none"
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response.")
        print("Response Text:", response.text)
        exit()

    # **Crucial Step:** Identify the list of records within the response data.
    # Adjust this based on your API's response structure, similar to the first example.
    # if isinstance(data, list):
    #     records = data
    # elif isinstance(data, dict) and 'metadata' in data and isinstance(data['metadata'], list):
    #     records = data['metadata']
    #     print(records)
    # Add more specific checks if needed
    # else:
    #     print(f"Error: Unexpected data structure received from API. Type: {type(data)}")
    #     # print("Data sample:", str(data)[:500])
    #     exit()
        

    # if not records:
        print("No records found in the API response to write to CSV.")
        exit()

    getData = deque(data['response']['apps'])
    while len(getData) > 0:
        currGame = getData.popleft()
        appid = currGame['appid']
        # print(getData['appid'])
        try:
            response2 = requests.get(detail_game_url(appid), headers=headers, params=params, timeout=30)
            try:
                data2 = response2.json()
                if response2.status_code == 200:
                    if data2['steam_appid'] == appid and data2['type'] == "game" and data2.get('release_date', {}).get('coming_soon') == False and ((data2['is_free'] == False and data2.get('recommendations', {})) or data2['is_free'] == True) and (data2.get('genres', {}) or data2.get('categories', {})) and data2.get('pc_requirements', {}).get('minimum'):
                        print(f"Current game is {appid}")
                        currDataGame = {}
                        currDataGame["name"] = data2['name']
                        currDataGame["steam_appid"] = data2['steam_appid']
                        currDataGame["is_free"] = data2['is_free']
                        currDataGame["header_image"] = data2['header_image']
                        currDataGame["minimum_req"] = [html_to_json(data2['pc_requirements']['minimum'])]
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
                        df = pd.DataFrame(records)
                        if firstTimeGameSet:
                            df.to_csv(output_csv_file, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
                            firstTimeGameSet=False
                        else:
                            df.to_csv(output_csv_file, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
                    else:
                        unsuccess = [ ]
                        unsuccess.append(currGame)
                        df2 = pd.DataFrame(unsuccess)
                        if firstTimeGameIgnored:
                            df2.to_csv(output_ignored_csv_file, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
                            firstTimeGameIgnored=False
                        else:
                            df2.to_csv(output_ignored_csv_file, mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
                            firstTimeGameIgnored=False
                        print(f"Failed to get game data {appid}, stored in another dataset")
                elif response2.status_code == 429:
                    getData.appendleft(currGame)
                    print(f'Too many requests. Put App ID {appid} back to deque. Sleep for 10 sec')
                    time.sleep(10)
                    continue


                elif response2.status_code == 403:
                    getData.appendleft(currGame)
                    print(f'Forbidden to access. Put App ID {appid} back to deque. Sleep for 5 min.')
                    time.sleep(5 * 60)
                    continue

                else:
                    print("ERROR: status code:", response2.status_code)
                    print(f"Error in App Id: {appid}. Put the app to error apps list.")
                    continue
            except json.JSONDecodeError:
                print("Error: Could not decode JSON response.")
                print("Response Text:", response2.text)
                exit()
        except requests.exceptions.Timeout:
            print(f"Error: The request to {detail_game_url(getData['appid'])} timed out.")
    # --- Create DataFrame and Write to CSV using Pandas ---
    # Pandas can often directly understand a list of dictionaries
    

    # Write the DataFrame to a CSV file
    # index=False prevents pandas from writing the DataFrame index as a column
    

    print(f"Successfully fetched data and saved to {output_csv_file} using pandas, last appid ({initial})\n ignored games saved to {output_ignored_csv_file}")

except requests.exceptions.Timeout:
    print(f"Error: The request to {game_list_url} timed out.")
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")
except KeyError as e:
    print(f"Error: Missing expected key '{e}' in API response data. Check response structure.")
except Exception as e: # Catches pandas errors too
    print(f"An unexpected error occurred: {e}")