#!/usr/bin/python
import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, FFmpegOpusAudio
from youtubesearchpython.__future__ import VideosSearch
import os
from os import environ
import requests
from pydub import AudioSegment
import youtube_dl
import random
import osu
import sp
from collections import deque
from dotenv import load_dotenv

from localCraiyon import craiyon_generate

SOUND_EFFECTS_DIR = "Sound_Effects/"
load_dotenv()
queue = deque()
current_track = None
balance = 10000
sp_client = sp.get_test_sp()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


def get_file_names(directory):
    return [".".join(x.split('.')[:-1]) for x in os.listdir(directory)]


def play_sound(voice, sound_path):
    source = FFmpegPCMAudio(sound_path)
    voice.play(source)
    voice.is_playing()


def save_sound(sound, where):
    with open(where, "wb") as f:
        f.write(sound.content)


def convert_file_to_wav(file_path):
    sound = AudioSegment.from_file(file_path)
    new_file_path = f"{'.'.join(file_path.split('.')[:-1])}.wav"
    sound.export(new_file_path, format='wav')
    os.remove(file_path)
    return new_file_path


async def get_yt_url_from_name(name):
    videos_result = await VideosSearch(name, limit=1).next()
    return str(videos_result["result"][0]["link"])


async def play_song_from_yt(vc, url, name=''):
    if name != '':
        url = await get_yt_url_from_name(name)
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    ydl_options = {'format': 'bestaudio/best', 'noplaylist': 'True'}
    try:
        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=False)
            i_url = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(i_url, **ffmpeg_options)
            vc.play(source)
            vc.is_playing()
    except youtube_dl.utils.DownloadError as e:
        print("error")
        if str(e.exc_info[1]) == "Sign in to confirm your age\nThis video may be inappropriate for some users.":
            spotify_channel = bot.get_channel(860291347029295124)
            await spotify_channel.send("The song is age restricted on youtube :(")


class Track:
    def __init__(self, name='', youtube_url='', spotify_url=''):
        self.name = name
        self.youtube_url = youtube_url
        self.spotify_url = spotify_url

        if self.youtube_url != '':
            self.name = "temp"
            #self.name = self.get_name_from_yt()
        elif self.spotify_url != '':
            if self.name == '':
                self.name = self.get_name_from_spotify()

    def __repr__(self):
        return self.name

    def get_name_from_yt(self):
        try:
            ydl_options = {'format': 'bestaudio/best', 'noplaylist': 'True'}
            with youtube_dl.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(self.youtube_url, download=False)
                return info['title']
        except Exception as e:
            print('error', e)
            return None

    def get_name_from_spotify(self):
        global sp_client
        return sp.get_current_playing_song_name(sp_client)

    async def play(self):
        if self.youtube_url != '':
            await play_song_from_yt(bot.voice_clients[0], url=self.youtube_url)
        else:
            await play_song_from_yt(bot.voice_clients[0], url="", name=self.name)


@tasks.loop(seconds=86400)
async def refresh_osu_token():
    osu.TOKEN = osu.get_token()


@tasks.loop(seconds=10)
async def osubot():
    users = osu.get_users()
    for user in users:
        status = osu.add_recent_beatmap_score(user)
        if status is None:
            continue
        osu_channel = bot.get_channel(834551161960792084)
        await osu_channel.send(embed=status)


@tasks.loop(seconds=5)
async def spoti_check():
    global sp_client
    global current_track
    if not bot.voice_clients:
        return

    music_name = sp.get_current_playing_song_name(sp_client)
    music_url = sp.get_current_playing_song_url(sp_client)

    if music_name is not None:
        if current_track is None:
            queue.append(Track(name=music_name, spotify_url=music_url))
        else:
            if queue:
                if music_name != queue[-1].name:
                    queue.append(Track(name=music_name, spotify_url=music_url))
            else:
                if music_name != current_track.name:
                    queue.append(Track(name=music_name, spotify_url=music_url))


@tasks.loop(seconds=2)
async def check_if_music_is_playing():
    global current_track
    # print(queue)
    if bot.voice_clients and not bot.voice_clients[0].is_playing():
        if queue:
            current_track = queue.popleft()

            await current_track.play()


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    refresh_osu_token.start()
    osubot.start()
    check_if_music_is_playing.start()


@bot.command()
async def cray(ctx, *args):
    image_paths = await craiyon_generate(" ".join(args))
    await ctx.channel.send(f"Cray-chan: ", files=[discord.File(x) for x in image_paths])

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.channel.send("Please join to a voice channel!")


@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()


@bot.command()
async def sb(ctx, sound_name):
    if sound_name is None:
        await ctx.channel.send("Please give the sound effect's name!")
        return

    sound_effect_names = get_file_names(SOUND_EFFECTS_DIR)
    if sound_name in sound_effect_names:
        if not ctx.voice_client:
            await join(ctx)
        play_sound(ctx.voice_client, SOUND_EFFECTS_DIR + sound_name + ".wav")
    else:
        await ctx.channel.send(f"There isn't a sound effect with the name: {sound_name}")


@bot.command()
async def skip(ctx):
    current_track = None
    bot.voice_clients[0].stop()


@bot.command()
async def sbls(ctx):
    await ctx.channel.send(", ".join(get_file_names(SOUND_EFFECTS_DIR)))


@bot.command()
async def dj(ctx, url):
    if url is None or "yout" not in url:
        await ctx.channel.send("Please give a youtube url that is correct!")
        return

    if (not ctx.voice_client) and ctx.author.voice:
        channel = ctx.author.voice.channel
        voice = await channel.connect()
    queue.append(Track("", youtube_url=url))


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()


@bot.command()
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()
        ctx.voice_client.is_paused()


@bot.command()
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()


@bot.command()
async def upload(ctx):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        file = attachment.filename
        file_name, ext = file.split('.')[-2:]

        if ext in ["mp3", "mp4", "avi", "wav"]:
            response = requests.get(attachment.url)
            save_sound(response, SOUND_EFFECTS_DIR + file)

            if ext != "wav":
                convert_file_to_wav(SOUND_EFFECTS_DIR + file)
            if file_name in get_file_names(SOUND_EFFECTS_DIR):
                await ctx.channel.send(f"Upload Successful! You can access it as: {file_name}")
            else:
                await ctx.channel.send("Something went wrong!")
        else:
            await ctx.channel.send("Upload Failed! Please only send an mp3, mp4, avi or wav file!")


@bot.command()
async def coinflip(ctx):
    await ctx.channel.send("Tails" if bool(random.randint(0, 1)) else "Heads")


@bot.command()
async def spotify(ctx):
    if not ctx.voice_client:
        await join(ctx)
    levente = 527567352460607488
    if ctx.author.id == levente:
        sp_switch("lecsi")
    else:
        sp_switch("roland")
    try:
        spoti_check.start()
    except:
        pass


@bot.command()
async def song(ctx):
    spotify_channel = bot.get_channel(860291347029295124)
    await spotify_channel.send(f"{current_track.name}\n{current_track.youtube_url}\n{current_track.spotify_url}")


@bot.command()
async def sp_next(ctx):
    global sp_client
    sp.next_song(sp_client)


def sp_switch(name):
    if name == "lecsi":
        temp_filename = ".l_cache"
    elif name == "roland":
        temp_filename = ".r_cache"
    else:
        raise Exception
    cache_data = ""
    with open(temp_filename, "r") as f:
        cache_data = f.readline()
    with open(".cache", "w") as f:
        f.write(cache_data)


@bot.command()
async def osu_reg(ctx, url):
    discord_id = str(ctx.author.id)
    osu_id = url.split('/')[-1]
    text = osu.add_user(discord_id, osu_id)
    await ctx.channel.send(text)


@bot.command()
async def osu_del(ctx):
    discord_id = str(ctx.author.id)
    text = osu.remove_user(discord_id)
    await ctx.channel.send(text)

if __name__ == "__main__":
    bot.run(environ.get("DC_TOKEN"))
