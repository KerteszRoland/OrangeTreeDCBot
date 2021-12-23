from requests import get
from urllib.parse import quote
from dotenv import load_dotenv
from os import environ
import json

load_dotenv()
token = environ.get("CLASH_TOKEN")
FILE_PATH = "clash_ids.json"
users = {}


def save_users(users):
    with open(FILE_PATH, 'w', encoding='utf-8') as file:
        json.dump(users, file, indent=2)


def load_users():
    with open(FILE_PATH, "r") as f:
        return json.load(f)
    return []


users = load_users()


def register_user(dc_id, clash_id):
    if dc_id in users:
        return "You already registered!"
    users[dc_id]= clash_id
    save_users(users)
    return "Successful registration!"
    

def delete_user(dc_id):
    if dc_id not in users:
        return "You are not registered! Please register by typing: !clash_reg <player_tag>"
    del users[dc_id]
    save_users(users)
    return "Successful deletion!"


def get_clash_id_by_dc_id(dc_id):
    return users[dc_id]


def get_upcoming_quality_chests(player_tag):
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
    
    
def get_upcoming_quality_chests_text(dc_id):
    if dc_id not in users:
        return "Please register before asking for chests!"
    player_tag = get_clash_id_by_dc_id(dc_id)
    chests = get_upcoming_quality_chests(player_tag)
    output = "\n".join([f"{x['name']} {'Next' if int(x['index']) == 0 else 'after ' + str(x['index']) + ' chests'}" for x in chests])
    return output
    