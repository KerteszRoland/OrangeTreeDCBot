import discord, asyncio
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, FFmpegOpusAudio
import os
import requests
from os import path
from pydub import AudioSegment
import youtube_dl
import random
import osu


def GetBearerToken():
    bearer_token = "NOT LOADED"
    with open("Bearer_token.txt", "r") as file:
        bearer_token = file.readline()
    return bearer_token


client = commands.Bot(command_prefix = '!')
TOKEN = GetBearerToken()

SOUND_EFFECTS_DIR = "Sound_Effects/"
SONGS_DIR = "Songs/"


async def GetFileNames(dir):
    file_names_ext =  os.listdir(dir)
    file_names = list()
    for file_name_ext in file_names_ext:
        file_names.append(file_name_ext.split('.')[0])
    return file_names


async def PlaySound(voice, sound_path):
    source = FFmpegOpusAudio(sound_path)
    voice.play(source)


async def SaveSound(sound, where):
    file = open(where, "wb")
    file.write(sound.content)
    file.close()


async def ConvertMP3ToWAV(name):
    sound = AudioSegment.from_mp3(name+".mp3")
    sound.export(name+".wav", format="wav")
    os.remove(name+".mp3")
    

async def ConvertFileToWAV(file_path):
    sound = AudioSegment.from_file(file_path)
    new_file_path = file_path.rstrip("."+file_path.split(".")[-1])+".wav"
    sound.export(new_file_path, format="wav")
    os.remove(file_path)
    return new_file_path


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

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
async def sbls(ctx):
    await ctx.channel.send(await GetFileNames(SOUND_EFFECTS_DIR))

@client.command()
async def djls(ctx):
    await ctx.channel.send(await GetFileNames(SONGS_DIR))


@client.command()
async def sb(ctx, *arg):
    if len(arg) <= 0:
        await ctx.channel.send("Please give the sound effect's name!")
        return
        
    sound_name = arg[0]
    sound_effect_names = await GetFileNames(SOUND_EFFECTS_DIR)
    if sound_name in sound_effect_names:
        if not ctx.voice_client:
            await join(ctx)
        await PlaySound(ctx.voice_client, SOUND_EFFECTS_DIR+sound_name)
    else:
        await ctx.channel.send(f"There isn't a sound effect with the name: {sound_name}")
        return
    
               
@client.command()
async def dj(ctx, *args):
    if len(args) <= 0:
        await ctx.channel.send("Please give a song name!")
        return
    
    search_name = args[0]
    if "https://" in search_name:
        await PlaySongFromYT(ctx, search_name)
        return
    song_names = await GetFileNames(SONGS_DIR)
        
    for song_name in song_names:  
        if search_name.lower() in song_name.lower():
            if not ctx.voice_client:
                await join(ctx)
            await PlaySound(ctx.voice_client, SONGS_DIR+song_name)
            return ""
    await ctx.channel.send(f"There isn't a song with the name: {search_name}")

    
    
@client.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()    


@client.command()
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()


@client.command()
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()


@client.command()
async def upload(ctx, *args):
    if ctx.message.attachments and len(args)>0:
        attachment = ctx.message.attachments[0]
        ext = attachment.filename.split('.')[-1]
        initial_name = attachment.filename
        if len(args)>= 2:
            initial_name = args[1]
        else:
            if len(initial_name) > 10:
                initial_name = initial_name[:10]
        filename = initial_name.rstrip("."+ext).strip().replace(' ','_').replace('.','_').lower()
        while filename[-1] == '_' or filename[-1] == '.' or filename[-1] == '-':
            filename = filename[:-2]
        
        if ext == "mp3" or ext == "wav":
            url = attachment.url
            response = requests.get(url)
       
            if args[0] == "sound":
                while filename in await GetFileNames(SOUND_EFFECTS_DIR):
                    filename = filename+"_copy"
                
                await SaveSound(response, SOUND_EFFECTS_DIR+filename+f".{ext}")
                if ext == "mp3":
                    await ConvertMP3ToWAV(SOUND_EFFECTS_DIR+filename)
                if filename in await GetFileNames(SOUND_EFFECTS_DIR):
                    await ctx.channel.send(f"Upload Successful! You can access it as: {filename}")
                else:
                    await ctx.channel.send("Something went wrong!")
            elif args[0] == "song":
                while filename in await GetFileNames(SONGS_DIR):
                    filename = filename+"_copy"
                
                await SaveSound(response, SONGS_DIR+filename+f".{ext}")
                if ext == "mp3":
                    await ConvertMP3ToWAV(SONGS_DIR+filename)
                if filename in await GetFileNames(SONGS_DIR):
                    await ctx.channel.send(f"Upload Successful! You can access it as: {filename}")
                else:
                    await ctx.channel.send("Something went wrong!")
            else:
                ctx.channel.send("Please set what you desire to upload. (song or sound)")
        else:
            ctx.channel.send("Upload Inturrepted! Please only send mp3 or wav files!")
    else:
        await ctx.channel.send("Please set what you desire to upload. (song or sound) and what name should it be!")


@client.command()
async def coinflip(ctx):
    result = ""
    coin = random.randint(0, 1)
    if coin == 0:
        result = "Tails"
    else:
        result = "Heads"
    await ctx.channel.send(result)
    

balance = 10000
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


async def PlaySongFromYT(ctx, url):
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        I_URL = info['formats'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
        ctx.voice_client.play(source)
        ctx.voice_client.is_playing()

@tasks.loop(seconds=86400)
async def refresh_token():
    osu.TOKEN = await osu.GetToken()
  

@tasks.loop(seconds=10)
async def osubot():
    users = osu.GetUsers()
    for user in users:  
        status = await osu.AddRecentBeatmapScore(user)
        if status == None:
            continue
        osu_channel = client.get_channel(834551161960792084)
        #await osu_channel.send(f"<@{users[user]}>") 
        await osu_channel.send(embed=status) 
    

@client.command()
async def osuadd(ctx, url):
    discord_id = str(ctx.author.id)
    osu_id = url.split('/')[-1]
    text = await osu.AddUser(discord_id, osu_id)
    await ctx.channel.send(text)    
    
    
@client.command()
async def osuremove(ctx):
    discord_id = str(ctx.author.id)
    text = await osu.RemoveUser(discord_id)
    await ctx.channel.send(text)    

refresh_token.start()
osubot.start()
client.run(TOKEN)