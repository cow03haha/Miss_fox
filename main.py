import discord
from discord.ext import commands
import random
import zipfile
import os
import asyncio
import datetime
import json
global bg_task

with open('settings.json', 'r') as jfile:
    jdata = json.load(jfile)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)


class Slaper(commands.Converter):
    async def convert(self, ctx, arg):
        to_slap = random.choice(ctx.guild.members)
        return '{0.author.mention} slapped {1.mention} because *{2}*'.format(ctx, to_slap, arg)

async def interval():
    await asyncio.sleep(60 - int(datetime.datetime.now().strftime('%S')))
    
    while not bot.is_closed():
        now_time = datetime.datetime.now().strftime('%H:%M')
        time = discord.Activity(type = discord.ActivityType.watching, name = f'現在時間: {now_time}')
        
        await bot.change_presence(activity = time)
        await asyncio.sleep(60)


@bot.event
async def on_ready():
    global bg_task
    bg_task = bot.loop.create_task(interval())

    print(f'bot {bot.user} online!')

@bot.command()
@commands.is_owner()
async def send_to(ctx, ch: int, *, text):
    """send message to specific channel"""
    ch = bot.get_channel(ch)
    
    await ch.send(text)

@bot.command()
async def slap(ctx, *, reason: Slaper):
    """you can try it"""
    await ctx.send(reason)

@bot.command()
async def get_emojis(ctx):
    """獲取伺服器表情"""
    await ctx.trigger_typing()

    emojis = await ctx.guild.fetch_emojis()
    data = []

    for i in emojis:
        data.append((i.name, i.url))
    
    os.system('mkdir tmp')
    for i in range(len(data)):
        await data[i][1].save(f'tmp/{data[i][0]}.gif')
    
    with zipfile.ZipFile('tmp/emojis.zip', 'w') as z:
        for i in range(len(data)):
            z.write(f'tmp/{data[i][0]}.gif')
    
    await ctx.send(file = discord.File(f'tmp/emojis.zip'))
    os.system(f'rm -r tmp')

@commands.is_owner()
@bot.command()
async def poweroff(ctx):
    """關閉bot。"""
    await ctx.send('bot關閉成功')
    await bot.logout()
    await bot.close()


if __name__ == '__main__':
    bot.run(jdata['token'])
