import discord
from discord.ext import commands
import random
import zipfile
import os
import sys
import asyncio
import datetime
import json
global spam
spam = {}

with open('settings.json', 'r') as jfile:
    jdata = json.load(jfile)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=jdata['prefix'], intents=intents)


class Slaper(commands.Converter):
    async def convert(self, ctx, arg):
        to_slap = random.choice(ctx.guild.members)
        return '{0.author.mention} slapped {1.mention} because *{2}*'.format(ctx, to_slap, arg)

async def time():
    await asyncio.sleep(60 - int(datetime.datetime.now().strftime('%S')))
    
    while not bot.is_closed():
        now_time = datetime.datetime.now().strftime('%H:%M')
        time = discord.Activity(type = discord.ActivityType.watching, name = f'現在時間: {now_time}')
        
        await bot.change_presence(activity = time)
        await asyncio.sleep(60)

async def antiSpam():
    while not bot.is_closed():
        for i in spam:
            if not spam[i]["time"]:
                spam[i]["time"] = 60
                spam[i]["count"] = 0
                spam[i]["mute"] = False
                
                role = spam[i]["member"].guild.get_role(808738303457230869)

                await spam[i]["member"].remove_roles(role, reason = "自動防洗頻系統")
            else:
                spam[i]["time"] -= 1

        await asyncio.sleep(1)


@bot.event
async def on_ready():
    bot.loop.create_task(time())
    bot.loop.create_task(antiSpam())

    print(f'bot {bot.user} online!')

@bot.event
async def on_message(msg):
    global spam

    try:
        if spam[msg.author.id]:
            spam[msg.author.id]["count"] += 1

            if spam[msg.author.id]["count"] == 20:
                spam[msg.author.id]["time"] = 1800
                spam[msg.author.id]["mute"] = True
                role = msg.guild.get_role(808738303457230869)

                await msg.author.add_roles(role, reason = "自動防洗頻系統")
                
    except KeyError:
        spam[msg.author.id] = {
            "time": 60,
            "count": 1,
            "mute": False,
            "member": msg.author,
        }

@bot.listen()
async def on_command_error(ctx, error):
    if type(error) == discord.ext.commands.MessageNotFound:
        await ctx.send('找不到該訊息!')

@bot.command()
@commands.is_owner()
async def send_to(ctx, ch: int, *, text):
    """Send message to specific channel"""
    ch = bot.get_channel(ch)
    
    await ch.send(text)

@bot.command()
async def slap(ctx, *, reason: Slaper):
    """Slap random people in guild.t"""
    await ctx.send(reason)

@bot.command()
async def get_emojis(ctx):
    """Get guild emojis."""
    await ctx.trigger_typing()

    emojis = await ctx.guild.fetch_emojis()
    if sys.platform == 'linux':
        rm = 'rm -rf'
    elif sys.platform == 'win32':
        rm = 'rmdir /S /Q'
    else:
        return 1

    os.system('mkdir tmp')

    with zipfile.ZipFile('tmp/emojis.zip', 'w') as z:
        for i in emojis:
            await i.url.save(f'tmp/{i.name}.gif')
            z.write(f'tmp/{i.name}.gif', f'{i.name}.gif')
    
    await ctx.send(file = discord.File(f'tmp/emojis.zip'))
    os.system(f'{rm} tmp')

@commands.has_guild_permissions(manage_messages = True)
@bot.command()
async def clear_afterid(ctx, msg: discord.Message):
    """Clear message after message you specific."""
    await ctx.trigger_typing()

    time = msg.created_at
    
    await msg.channel.purge(after = time, bulk = True)
    await ctx.send(f'**{msg.channel}** {msg.id} 後的訊息刪除成功!', delete_after = 7)

@commands.is_owner()
@bot.command()
async def poweroff(ctx):
    """Shutdown bot."""
    await ctx.send('bot關閉成功')
    await bot.logout()
    await bot.close()


if __name__ == '__main__':
    bot.run(jdata['token'])
