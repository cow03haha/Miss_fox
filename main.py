import discord
from discord.ext import commands
import json

with open('settings.json', 'r') as jfile:
    jdata = json.load(jfile)
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=jdata['prefix'], intents=intents)


@bot.event
async def on_ready():
    print(f'bot {bot.user} online!')
    ch = bot.get_channel(741685158335479950)
    await ch.send(f'bot {bot.user} online!')

@commands.is_owner()
@bot.command()
async def poweroff(ctx):
    """Shutdown bot."""
    await ctx.send('bot關閉成功')
    await bot.close()

@commands.is_owner()
@bot.command()
async def reload(ctx):
    """reload command"""
    bot.reload_extension('fox')
    await ctx.send('reload success')

@commands.is_owner()
@bot.command()
async def reboot(ctx):
    """restart bot."""
    await ctx.send('WIP...')


if __name__ == '__main__':
    bot.load_extension('fox')
    bot.run(jdata['token'])
            