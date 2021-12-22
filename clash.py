from requests import get
from urllib.parse import quote
from dotenv import load_dotenv
from os import environ

load_dotenv()
token = environ.get("CLASH_TOKEN")

def GetUpComingQualityChests(player_tag):
    player_tag = quote(player_tag)
    url = f"https://api.clashroyale.com/v1/players/{player_tag}/upcomingchests"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = get(url, headers=headers).json()
    chests = response["items"]
    return [chest for chest in chests if "gold" not in chest["name"].lower() and "silver" not in chest["name"].lower()]
    
    
def GetUpComingQualityChestsText(player_tag):
    chests = GetUpComingQualityChests(player_tag)
    output = "\n".join([f"{x['name']} {int(x['index'])} {'Következő' if int(x['index']) == 0 else 'chest múlva'}" for x in chests])
    return output
