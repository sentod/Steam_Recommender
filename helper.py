from bs4 import BeautifulSoup
import json
import regex as re

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