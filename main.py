import discord
from discord.ext import commands
import random
import zipfile
import os
import sys
import asyncio
import time
import datetime
import json
spam = {}

with open('settings.json', 'r') as jfile:
    jdata = json.load(jfile)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=jdata['prefix'], intents=intents)

class Slaper(commands.Converter):
    async def convert(self, ctx, arg):
        to_slap = random.choice(ctx.guild.members)
        return '{0.author.mention} slapped {1.mention} because *{2}*'.format(ctx, to_slap, arg)

async def nowtime():
    await asyncio.sleep(60 - int(datetime.datetime.now().strftime('%S')))
    
    while not bot.is_closed():
        now_time = datetime.datetime.now().strftime('%H:%M')
        time = discord.Activity(type = discord.ActivityType.watching, name = f'現在時間: {now_time}')
        
        await bot.change_presence(activity = time)
        await asyncio.sleep(60)

async def antiSpam():
    while not bot.is_closed():
        remove = []
        for i in spam:
            spam[i]['time'] -= 1
            if  spam[i]['time'] <= 0:
                remove.append(i)
                
                if spam[i]['mute']:
                    role = discord.utils.get(spam[i]['member'].guild.roles, name = 'Muted')
                    await spam[i]['member'].remove_roles(role, reason = '自動防洗頻系統')

        for i in remove:
            del spam[i]
            
        await asyncio.sleep(1)


@bot.event
async def on_ready():
    bot.loop.create_task(nowtime())
    bot.loop.create_task(antiSpam())
    
    print(f'bot {bot.user} online!')
    ch = bot.get_channel(741685158335479950)
    await ch.send(f'bot {bot.user} online!')

@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    if msg.content == f'{bot.user.mention} prefix':
        await msg.channel.send(f'my prifx is `{bot.command_prefix}` !')

    try:
        if spam[msg.author.id]:
            spam[msg.author.id]['count'] += 1

            if spam[msg.author.id]['count'] >= 20:
                spam[msg.author.id]['time'] = 1800
                spam[msg.author.id]['count'] = 0
                spam[msg.author.id]['mute'] = True
                
                role = discord.utils.get(msg.guild.roles, name = 'Muted')
                await msg.author.add_roles(role, reason = '自動防洗頻系統')

                await msg.channel.purge(after = spam[msg.author.id]['msgTime'], bulk = True)

                await msg.channel.send(f'{msg.author.mention} 已被自動防洗頻系統靜音，如有誤判請通知管理員')
                
    except KeyError:
        spam[msg.author.id] = {
            'time': 60,
            'count': 1,
            'mute': False,
            'member': msg.author,
            'msgTime': msg.created_at - datetime.timedelta(microseconds = 1),
        }

    await bot.process_commands(msg)

@bot.listen()
async def on_command_error(ctx, error):
    if type(error) == discord.ext.commands.MessageNotFound:
        await ctx.send('找不到該訊息!')
    else:
        await ctx.send(f'未知錯誤\n```\n{error}\n```')

@bot.command()
async def ping(ctx):
    """測試延遲。"""
    t = time.perf_counter()
    await ctx.trigger_typing()
    t2 = time.perf_counter()
    await ctx.trigger_typing()

    this = round((t2 - t) * 1000)
    ws = int(bot.latency * 1000)
    await ctx.send(f'延遲：{this} 毫秒(ms)\nWebsocket：{ws} 毫秒(ms)')

@bot.command()
@commands.is_owner()
async def send_to(ctx, ch: int, *, text):
    """Send message to specific channel"""
    ch = bot.get_channel(ch)
    
    await ch.send(text)

@bot.command()
async def slap(ctx, *, reason: Slaper):
    """Slap random people in guild."""
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

@bot.command()
async def get_avatar(ctx, user: discord.User):
    """Get specific member's avatar."""
    await ctx.send(user.avatar_url)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def voicemoveall(ctx, origin: discord.VoiceChannel, target: discord.VoiceChannel):
    """Move all member from a to b."""
    if ctx.author.guild_permissions.move_members:
        if origin in ctx.guild.voice_channels and target in ctx.guild.voice_channels:
            for members in origin.members:
                await members.edit(voice_channel=target)
                
    res = f"把所有成員從 {origin.mention} 移動到 {target.mention} 成功"
    await ctx.send(res)

@commands.has_guild_permissions(manage_messages = True)
@bot.command()
async def clear_afterid(ctx, msg: discord.Message):
    """Clear message after message you specific(limit: 100)."""
    await ctx.trigger_typing()

    time = msg.created_at - datetime.timedelta(microseconds = 1)
    
    await msg.channel.purge(after = time, bulk = True)
    await ctx.send(f'**{msg.channel}** {msg.id} 後(含)的訊息刪除成功!', delete_after = 7)

@commands.is_owner()
@bot.command()
async def get_nick(ctx, member: discord.Member):
    """get specific member's nick"""
    await ctx.send(member.nick)

@bot.command()
@commands.is_owner()
async def nick(ctx, location = None, nick = None):
    msg = await ctx.send('progress...')

    if location == 'all':
        location = ctx.guild
    else:
        location = ctx.guild.get_channel(int(location))

    if nick == 'clear':
        nick = None

    members = location.members
    for i in members:
        try:
            await i.edit(nick = nick)
        except:
            continue
    
    await msg.edit(content = 'success')

@commands.has_guild_permissions(manage_messages = True)
@bot.command()
async def mute(ctx, member: discord.Member):
    spam[member.id] = {
            'time': 31536000,
            'count': 0,
            'mute': True,
            'member': member,
            'msgTime': datetime.datetime.now() - datetime.timedelta(microseconds = 1),
        }
    
    role = discord.utils.get(ctx.guild.roles, name = 'Muted')
    await member.add_roles(role, reason = '自動防洗頻系統(手動)')

    await ctx.send(f'以手動靜音 {member.mention} !')

@commands.has_guild_permissions(manage_messages = True)
@bot.command()
async def unmute(ctx, member: discord.Member):
    try:
        if not spam[member.id]['mute']:
            await ctx.send('這位成員沒有被靜音!')
            return 0
    except KeyError:
        await ctx.send('這位成員沒有被靜音!')
        return 0
        
    spam[member.id]['time'] = 60
    spam[member.id]['count'] = 0
    spam[member.id]['mute'] = False
    
    role = discord.utils.get(ctx.guild.roles, name = 'Muted')
    await member.remove_roles(role, reason = '自動防洗頻系統(手動)')

    await ctx.send(f'以解除靜音 {member.mention} !')

@commands.is_owner()
@bot.command()
async def poweroff(ctx):
    """Shutdown bot."""
    await ctx.send('bot關閉成功')
    await bot.close()

@commands.is_owner()
@bot.command()
async def reboot(ctx):
    """restart bot."""
    await ctx.send('WIP...')

if __name__ == '__main__':
    bot.run(jdata['token'])
            