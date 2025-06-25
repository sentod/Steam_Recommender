import requests
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup

# site_url = 'https://www.cpubenchmark.net/cpu_list.php'
site_url = 'https://www.videocardbenchmark.net/gpu_list.php'
output_csv = 'gpu_dataset.csv'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

def extractData(html_str):
    soup = BeautifulSoup(html_str, 'html.parser')
    table = soup.find('table', {'id': 'cputable'})
    # print(table)

    if not table:
        return None  # Table not found

    headers = [th.text.strip() for th in table.find_all('th')]
    headers.append('GPU Link')
    data = []

    for row in table.find_all('tr')[1:]:  # Skip header row
        cells = [td.text.strip() for td in row.find_all('td')]
        a_tag = row.find('a')
        if a_tag:   
            cells.append(a_tag['href'])
        if len(cells) == len(headers): #check to avoid malformed rows.
            data.append(dict(zip(headers, cells)))

    return json.dumps(data)

try:
    response = requests.get(site_url, headers=headers, timeout=30)
    # response.raise_for_status() 
    
    try:
        # data = response
        # print(extractData(response.text))
        result = json.loads(extractData(response.text))
        # result.append(extractData(response.text))
        # print(type(extractData(response.text)))
        df = pd.DataFrame(result)
        df.to_csv(output_csv, index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"', encoding='utf-8')
        print(f'Successfuly export to {output_csv}')
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response.")
        print("Response Text:", response.text)
        exit()

except requests.exceptions.Timeout:
    print(f"Error: The request to {site_url} timed out.")
except requests.exceptions.RequestException as e:
    print(f"Error during API request: {e}")
except KeyError as e:
    print(f"Error: Missing expected key '{e}' in API response data. Check response structure.")
except Exception as e: # Catches pandas errors too
    print(f"An unexpected error occurred: {e}")