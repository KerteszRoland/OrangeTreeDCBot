import requests
import json
import discord
from datetime import datetime
from dotenv import load_dotenv
from os import environ


load_dotenv()
OSU_USERS_FILE = "osu_users.txt"
OSU_SCORE_IDS = "osu_score_ids.txt"
SEPARATOR = ";"
CLIENT_ID = environ.get("OSU_CLIENT_ID")
CLIENT_SECRET = environ.get("OSU_CLIENT_SECRET")


class BeatmapScore:
    def __init__(self, score):
        self.user_pic = score['user']['avatar_url']
        self.mods = ' '.join(score['mods'])
        self.id = score['id']
        self.score = score['score']
        self.accuracy = score['accuracy']
        self.beatmap_name = score['beatmapset']['title']
        self.beatmap_star = score['beatmap']['difficulty_rating']
        self.ranked = score['beatmap']['ranked']
        self.beatmap_link = score['beatmap']['url']
        self.fc = score['perfect']
        self.count_100 = score['statistics']['count_100']
        self.count_50 = score['statistics']['count_50']
        self.count_miss = score['statistics']['count_miss']
        self.combo = score['max_combo']
        self.username = score['user']['username']
        self.pp = score['pp']
        self.rank = score['rank']
        self.best_score_id = score['best_id']
        self.url = f"https://osu.ppy.sh/scores/osu/{score['best_id']}"
        self.beatmap_pic = score['beatmapset']['covers']['list@2x']
        self.user_url = f"https://osu.ppy.sh/users/{score['user']['id']}"
 
        if self.rank == 'D':
            self.rank_color = 0xFF0000
        elif self.rank == 'C':
            self.rank_color = 0xFF56FF
        elif self.rank == 'B':
            self.rank_color = 0x0097FF
        elif self.rank == 'A':
            self.rank_color = 0x00FF47
        elif self.rank == 'S' or self.rank == 'X':
            self.rank_color = 0xFFE300
        elif self.rank == 'SH' or self.rank == 'XH':
            self.rank_color = 0xDEDEDE

        if self.rank == "SH":
            self.rank = "S"
        if self.rank == "X" or self.rank == "XH":
            self.rank = "SS"

    def __repr__(self):
        s = f"{self.username} "
        s += f"{self.rank} "

        if self.fc == "True":
            s += "FC "
        s += f"{int(self.accuracy*10000)/100}% "
        if self.mods != "":
            s += self.mods + " "
        s += f"100:{self.count_100} "
        s += f"50:{self.count_50} "
        s += f"Miss:{self.count_miss} "
        s += f"{self.beatmap_name} "
        s += f"{self.beatmap_star}* "
        return s

    def get_embed(self):
        description = f"Rank: **{self.rank}** \n Accuracy: **{int(self.accuracy*10000)/100}%**"
        if self.fc:
            description += "\n Combo: **FC**"
        else:
            description += f"\n Combo: **{self.combo}x**"
        description += f"\n Score: **{self.score}**"
        if self.pp is not None:
            description += f"\n PP: **{self.pp}**"
        if self.mods != "":
            description += f"\n Mods: **{self.mods}**"
        embed = discord.Embed(title=f"{self.beatmap_name} {self.beatmap_star}*", color=self.rank_color,url=self.beatmap_link,description=description)
        if 'http' not in self.user_pic:
            self.user_pic = "https://a.ppy.sh/"
        
        embed.set_author(name=self.username, icon_url=self.user_pic, url=self.user_url)
        embed.set_thumbnail(url=self.beatmap_pic)
        embed.add_field(name="100", value=self.count_100, inline=True)
        embed.add_field(name="50", value=self.count_50, inline=True)
        embed.add_field(name="Miss", value=self.count_miss, inline=True)
        embed.set_footer(text=datetime.now().strftime("%Y.%m.%d %H:%M:%S"), icon_url="https://orangethereal.hu/orange.jpg")
        return embed

    def get_all_info(self):
        s = f"Title: {self.beatmap_name}\n" \
            f"Score:{self.score}\n" \
            f"Accuracy: {self.accuracy}\n" \
            f"Rank: {self.rank}\n" \
            f"Star: {self.beatmap_star}\n" \
            f"Mods: {self.mods}\n" \
            f"Ranked: {self.ranked}\n" \
            f"Beatmap Link: {self.beatmap_link}\n" \
            f"FC: {self.fc}\n" \
            f"100: {self.count_100}\n" \
            f"50: {self.count_50}\n" \
            f"Miss: {self.count_miss}\n" \
            f"Combo: {self.combo}\n" \
            f"Username: {self.username}\n" \
            f"PP: {self.pp}\n" \
            f"Best score id: {self.best_score_id}\n" \
            f"Url: {self.url}\n" \
            f"Id: {self.id}\n" \
            f"User pic: {self.user_pic}\n" \
            f"User url: {self.user_url}\n" \
            f"Beatmap pic: {self.beatmap_pic}\n"
        return s


def get_token():
    url = "https://osu.ppy.sh/oauth/token"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    body = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",  
        "scope": "public"
    }
    access_token = requests.post(url=url, data=json.dumps(body), headers=headers).json()['access_token']
    return access_token


def save_score_ids(score_ids):
    with open(OSU_SCORE_IDS, 'w') as file:
        for score_id in score_ids:
            file.write(f"{score_id}\n")


def read_score_ids():
    with open(OSU_SCORE_IDS, 'r') as file:
        return [int(numeric_string) for numeric_string in file.read().splitlines()]


TOKEN = ""
beatmap_scores = list()
beatmap_score_ids = read_score_ids()


def get_recent_score(user_id, token):
    url = f"https://osu.ppy.sh/api/v2/users/{user_id}/scores/recent?mode=osu&limit=1"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response)
        return []
    return response.json()


def add_recent_beatmap_score(user_id):
    score = get_recent_score(user_id, TOKEN)
    if not score:
        return None
    score = score[0]
    if score['id'] not in beatmap_score_ids:
        beatmap = BeatmapScore(score)
        beatmap_scores.append(beatmap)
        beatmap_score_ids.append(beatmap.id)
        save_score_ids(beatmap_score_ids)
        print(beatmap)
        return beatmap.get_embed()


def get_user_data(user_id, token):
    url = f"https://osu.ppy.sh/api/v2/users/{user_id}/osu?key=id"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        print(response)
    return response.json()


def is_user_in_users(discord_id):
    with open(OSU_USERS_FILE, 'r') as file:
        for line in file.read().splitlines():
            if line.split(SEPARATOR)[0] == discord_id:
                return True
    return False
    

def get_users():
    temp = dict()
    with open(OSU_USERS_FILE, 'r') as file:
        for line in file.read().splitlines():
            if line == "":
                continue
            discord_id = line.split(SEPARATOR)[0]
            osu_id = line.split(SEPARATOR)[1]
            temp[osu_id] = discord_id
    return temp


def remove_user(discord_id):
    all_lines = ""
    with open(OSU_USERS_FILE, 'r') as file:
        all_lines = file.read().splitlines()
    with open(OSU_USERS_FILE, 'w') as file:
        for line in all_lines:
            if line.split(SEPARATOR)[0] != discord_id:
                file.write(line)
    return "Osu profile removed successfully!"


def add_user(discord_id, osu_id):
    if is_user_in_users(discord_id):
        all_lines = ""
        with open(OSU_USERS_FILE, 'r') as file:
            all_lines = file.readlines()
        with open(OSU_USERS_FILE, 'w') as file:
            for line in all_lines:
                if line.split(SEPARATOR)[0] == discord_id:
                    file.write(f"{discord_id}{SEPARATOR}{osu_id}\n")
                else:
                    file.write(line)
        return "Osu profile changed successfully!"
    else:
        with open(OSU_USERS_FILE, 'a+') as file:
            file.write(f"{discord_id}{SEPARATOR}{osu_id}\n")
        return "Osu profile added successfully!"
