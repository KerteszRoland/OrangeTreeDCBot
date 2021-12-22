import discord, asyncio
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, FFmpegOpusAudio
import os
from os import environ
import requests
from pydub import AudioSegment
import youtube_dl
import random
import osu, sp, clash
from collections import deque
from dotenv import load_dotenv

load_dotenv()

SOUND_EFFECTS_DIR = "Sound_Effects/"
QUEUE = deque()

client = commands.Bot(command_prefix = '!')
musics = []
current_music = ""
sp_client = sp.GetTestSP()
balance = 10000


def GetFileNames(dir):
    return [".".join(x.split('.')[:-1]) for x in os.listdir(dir)]


def PlaySound(voice, sound_path):
    source = FFmpegPCMAudio(sound_path)
    voice.play(source) 
    voice.is_playing()


def SaveSound(sound, where):
    with open(where, "wb") as f:
        f.write(sound.content)


def ConvertFileToWAV(file_path):
    sound = AudioSegment.from_file(file_path)
    new_file_path = f"{'.'.join(file_path.split('.')[:-1])}.wav"
    sound.export(new_file_path, format="wav")
    os.remove(file_path)
    return new_file_path


async def PlaySongFromYT(vc, url):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
    try:
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            I_URL = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
            vc.play(source)
            vc.is_playing()
    except youtube_dl.utils.DownloadError as e:
        print("error")
        if str(e.exc_info[1]) == "Sign in to confirm your age\nThis video may be inappropriate for some users.":
            spotify_channel = client.get_channel(860291347029295124)
            await spotify_channel.send("The song is age restricted on youtube :(")


@tasks.loop(seconds=86400)
async def refresh_osu_token():
    osu.TOKEN = await osu.GetToken()
  

@tasks.loop(seconds=10)
async def osubot():
    users = osu.GetUsers()
    for user in users:  
        status = await osu.AddRecentBeatmapScore(user)
        if status == None:
            continue
        osu_channel = client.get_channel(834551161960792084)
        await osu_channel.send(embed=status) 


@tasks.loop(seconds=5)
async def spoti_check():
    global sp_client
    global current_music
    if len(client.voice_clients) == 0:
        return
    
    music_name = sp.GetCurrentPlayingSongName(sp_client)
    if music_name != current_music and music_name != None:
        #musics.append(music_name)
        current_music = music_name
        from youtubesearchpython.__future__ import VideosSearch
        videosResult = await VideosSearch(music_name, limit = 1).next()
        url = videosResult["result"][0]["link"]
        if client.voice_clients[0].is_playing():
            client.voice_clients[0].stop()
        await PlaySongFromYT(client.voice_clients[0], url)
   

@tasks.loop(seconds=5)
async def CheckIfMusicIsPlaying():
    if not client.voice_clients[0].is_playing():
        if len(QUEUE) > 0:
            await PlaySongFromYT(client.voice_clients[0], QUEUE.popleft())
        else:
            CheckIfMusicIsPlaying.stop()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    refresh_osu_token.start()
    osubot.start()


@client.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice = await channel.connect()
    else:
        await ctx.channel.send("Please join to a voice channel!")

  
@client.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    

@client.command()
async def sb(ctx, sound_name):
    if sound_name is None:
        await ctx.channel.send("Please give the sound effect's name!")
        return
        
    sound_effect_names = GetFileNames(SOUND_EFFECTS_DIR)
    if sound_name in sound_effect_names:
        if not ctx.voice_client:
            await join(ctx)
            PlaySound(ctx.voice_client, SOUND_EFFECTS_DIR+sound_name+".wav")
    else:
        await ctx.channel.send(f"There isn't a sound effect with the name: {sound_name}")
        return


@client.command()
async def sbls(ctx):
    await ctx.channel.send(", ".join(GetFileNames(SOUND_EFFECTS_DIR)))


@client.command()
async def dj(ctx, url):
    if url is None:
        await ctx.channel.send("Please give a youtube url!")
        return
    if "yout" not in url:
        await ctx.channel.send("Incorrect url given!")
        return
        
    if not ctx.voice_client:
        await join(ctx)
    
    if ctx.voice_client.is_playing():
        QUEUE.append(url)
        if not CheckIfMusicIsPlaying.is_running():  
            CheckIfMusicIsPlaying.start()
        return
        
    await PlaySongFromYT(ctx.voice_client, url)

    
@client.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop() 


@client.command()
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()
        ctx.voice_client.is_paused()


@client.command()
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()


@client.command()
async def upload(ctx):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        file = attachment.filename
        file_name, ext = file.split('.')[-2:]

        if ext in ["mp3", "mp4", "avi", "wav"]:
            response = requests.get(attachment.url)       
            SaveSound(response, SOUND_EFFECTS_DIR+file)
            
            if ext != "wav":
                ConvertFileToWAV(SOUND_EFFECTS_DIR+file)
            if file_name in GetFileNames(SOUND_EFFECTS_DIR):
                await ctx.channel.send(f"Upload Successful! You can access it as: {file_name}")
            else:
                await ctx.channel.send("Something went wrong!")
        else:
            await ctx.channel.send("Upload Failed! Please only send an mp3, mp4, avi or wav file!")


@client.command()
async def coinflip(ctx):
    await ctx.channel.send("Tails" if bool(random.randint(0, 1)) else "Heads")
    

@client.command()
async def roulette(ctx, *args):
    global balance
    color = args[0]
    wager = int(args[1])
     
    if wager<=0:
        await ctx.channel.send("Your wager have to be greater than 0!")
        return
    
    if wager>balance:
        await ctx.channel.send("You don't have enough money!")
        return
    
    roll = random.randint(0, 14)
    if roll == 0 and color == "green":
        balance += wager*12
        await ctx.channel.send(f"Green is correct! You won: {wager*12}") 
        await ctx.channel.send(f"Your balance now is: {balance}") 
    elif (roll%2==0 and color == "red") or (roll%2!=0 and color == "black"):
        balance += wager
        await ctx.channel.send(f"{color[0].upper()+color[1:]} is correct! You won: {wager}") 
        await ctx.channel.send(f"Your balance now is: {balance}")
    else:
        balance -= wager
        await ctx.channel.send(f"You lost: {wager}, better luck next time!") 
        await ctx.channel.send(f"Your balance now is: {balance}")


@client.command()
async def spotify(ctx):
    if not ctx.voice_client:
            await join(ctx)
    spoti_check.start()
 

@client.command()
async def song(ctx):
    global sp_client
    music_name = sp.GetCurrentPlayingSongName(sp_client)
    spotify_channel = client.get_channel(860291347029295124)
    await spotify_channel.send(music_name)


@client.command()
async def sp_next(ctx):
    global sp_client
    sp.NextSong(sp_client)

   
@client.command()
async def sp_switch(ctx, name):
    if name == "lecsi":
        temp_filename = ".l_cache"
    elif name == "roland":
        temp_filename = ".r_cache"
    else:
        await ctx.channel.send(f"There isn't a spotify account with a name: {name}")
        return
    cache_data = ""
    with open(temp_filename, "r") as f:
        cache_data = f.readline()
    with open(".cache", "w") as f:
        f.write(cache_data)
    

@client.command()
async def osu_add(ctx, url):
    discord_id = str(ctx.author.id)
    osu_id = url.split('/')[-1]
    text = osu.AddUser(discord_id, osu_id)
    await ctx.channel.send(text)    
    
    
@client.command()
async def osu_remove(ctx):
    discord_id = str(ctx.author.id)
    text = osu.RemoveUser(discord_id)
    await ctx.channel.send(text)    


@client.command()
async def clash_chest(ctx, player_tag):
    await ctx.channel.send(clash.GetUpComingQualityChestsText(player_tag))

client.run(environ.get("DC_TOKEN"))
