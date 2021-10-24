from typing import final
import discord
from discord import utils
from discord.ext import commands, tasks
import utils
import datetime
import time
import json
import requests
import sys
import os
from importlib import reload
import zipfile
import random

with open('settings.json', 'r') as jfile:
    jdata = json.load(jfile)

class Slaper(commands.Converter):
    async def convert(self, ctx, arg):
        to_slap = random.choice(ctx.guild.members)
        return '{0.author.mention} slapped {1.mention} because *{2}*'.format(ctx, to_slap, arg)

class Fox(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam = {}
        self.invites = {}
        self.initial.start()
        self.nowTime.start()
        self.antiSpam.start()
    
    def cog_unload(self):
        reload(utils)
        self.spam = {}
        self.nowTime.cancel()
        self.antiSpam.cancel()

    @tasks.loop(seconds=1)
    async def initial(self):
        if self.bot.is_ready():
            for i in self.bot.guilds:
                self.invites[i.id] = await i.invites()

            self.initial.cancel()

    @tasks.loop(seconds=1)
    async def nowTime(self):
        if self.bot.is_ready() and datetime.datetime.now().second == 0:
            offset = time.timezone if not time.localtime().tm_isdst else time.altzone
            offset = 8 - offset // 60 // 60 * -1
            now_time = (datetime.datetime.now() + datetime.timedelta(hours=offset)).strftime('%H:%M')
            
            activity = discord.Activity(type = discord.ActivityType.watching, name = f'現在時間: {now_time}')
            await self.bot.change_presence(activity = activity)

    @tasks.loop(seconds=1)
    async def antiSpam(self):
        if self.bot.is_ready():
            remove = []
            for i in self.spam:
                self.spam[i]['time'] -= 1
                if self.spam[i]['time'] <= 0:
                    remove.append(i)
                    
                    if self.spam[i]['mute']:
                        role = discord.utils.get(self.spam[i]['member'].guild.roles, name = 'Muted')
                        await self.spam[i]['member'].remove_roles(role, reason = '自動防洗頻系統')

            for i in remove:
                del self.spam[i]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # 可用變數: member, invite
        new_invites = await member.guild.invites()
        invite = utils.find_use_invite(self.invites[member.guild.id], new_invites)
        self.invites[member.guild.id] = new_invites
        with open('guild.json', 'r', encoding='utf8') as jfile:
            jdata = json.load(jfile)
        
        key = str(member.guild.id)
        if not jdata.get(key): return
        if not jdata[key]['config']['event']['join']: return
        
        ch = member.guild.get_channel(jdata[key]['join']['id'])
        await ch.send(eval(jdata[key]['join']['message']))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # 可用變數: member
        with open('guild.json', 'r', encoding='utf8') as jfile:
            jdata = json.load(jfile)
        
        key = str(member.guild.id)
        if not jdata.get(key): return
        if not jdata[key]['config']['event']['leave']: return
        
        ch = member.guild.get_channel(jdata[key]['leave']['id'])
        await ch.send(eval(jdata[key]['leave']['message']))

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        if self.bot.user.mentioned_in(msg):
            if msg.content.endswith('prefix'):
                await msg.channel.send(f'My preifx is `{self.bot.command_prefix}` !')

        try:
            if self.spam[msg.author.id] and isinstance(msg.channel, discord.TextChannel):
                self.spam[msg.author.id]['count'] += 1
                if msg.channel not in self.spam[msg.author.id]['chs']:
                    self.spam[msg.author.id]['chs'].append(msg.channel)

                if self.spam[msg.author.id]['count'] >= 20 and not self.spam[msg.author.id]['mute']:
                    self.spam[msg.author.id]['time'] = 1800
                    self.spam[msg.author.id]['mute'] = True
                    
                    role = discord.utils.get(msg.guild.roles, name = 'Muted')
                    await msg.author.add_roles(role, reason = '自動防洗頻系統')

                    for ch in self.spam[msg.author.id]['chs']:
                        await ch.purge(after = self.spam[msg.author.id]['msgTime'], check = lambda n: n.author == msg.author, bulk = True)
                    await msg.channel.send(f'{msg.author.mention} 已被自動防洗頻系統靜音，如有誤判請通知管理員')
        except KeyError:
            self.spam[msg.author.id] = {
                'time': 60,
                'count': 1,
                'mute': False,
                'member': msg.author,
                'msgTime': msg.created_at - datetime.timedelta(microseconds = 1),
                'chs' : [msg.channel]
            }

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if type(error) == discord.ext.commands.MessageNotFound:
            await ctx.send('找不到該訊息!')
        else:
            await ctx.send(f'未知錯誤\n```\n{error}\n```')
    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self.invites[invite.guild.id].append(invite)
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self.invites[invite.guild.id].remove(invite)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        with open('guild.json', 'r') as jfile:
            jdata = json.load(jfile)
        
        cfg = jdata.get(str(member.guild.id))
        if not cfg: return
        if not cfg['config']['log']['voice_state']: return

        ch = member.guild.get_channel(cfg['log']['voice_state'])
        if before.channel == None and isinstance(after.channel, discord.VoiceChannel):
            embed = discord.Embed(
                description = f'**{member.mention} 加入了語音頻道 {after.channel.mention}**',
                color = discord.Color.green(),
                timestamp = datetime.datetime.utcnow()
            )
            embed.set_author(
                name = f'{member.name}#{member.discriminator}',
                icon_url = member.avatar_url
            )
            await ch.send(embed = embed)
        elif isinstance(before.channel, discord.VoiceChannel) and after.channel == None:
            embed = discord.Embed(
                description = f'**{member.mention} 離開了語音頻道 {before.channel.mention}**',
                color = discord.Color.red(),
                timestamp = datetime.datetime.utcnow()
            )
            embed.set_author(
                name = f'{member.name}#{member.discriminator}',
                icon_url = member.avatar_url
            )
            await ch.send(embed = embed)
        elif None not in [before.channel, after.channel] and before.channel != after.channel:
            embed = discord.Embed(
                description = f'**{member.mention} 從 {before.channel.mention} 移動到 {after.channel.mention}**',
                color = discord.Color.blurple(),
                timestamp = datetime.datetime.utcnow()
            )
            embed.set_author(
                name = f'{member.name}#{member.discriminator}',
                icon_url = member.avatar_url
            )
            await ch.send(embed = embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        with open('guild.json', 'r') as jfile:
            jdata = json.load(jfile)

        cfg = jdata.get(str(after.guild.id))
        if not cfg: return
        if not cfg['config']['log']['message_update']: return

        if before.content == after.content: return
        ch = after.guild.get_channel(cfg['log']['message_update'])
        embed = discord.Embed(
            description = f'**一則在 {after.channel.mention} 的訊息被編輯了** [查看訊息]({after.jump_url})',
            color = discord.Color.blurple(),
            timestamp = datetime.datetime.utcnow()
        )
        embed.set_footer(text=f'User ID: {after.author.id}')
        embed.add_field(name='編輯前', value=before.content if before.content else '(無)', inline=False)
        embed.add_field(name='編輯後', value=after.content, inline=False)
        embed.set_author(
            name = f'{after.author.name}#{after.author.discriminator}',
            icon_url = after.author.avatar_url
        )
        await ch.send(embed = embed)

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        with open('guild.json', 'r') as jfile:
            jdata = json.load(jfile)

        cfg = jdata.get(str(msg.guild.id))
        if not cfg: return
        if not cfg['config']['log']['message_update']: return

        ch = msg.guild.get_channel(cfg['log']['message_update'])
        embed = discord.Embed(
            description = f'**{msg.author.mention} 在 {msg.channel.mention} 發送的訊息被刪除了**\n{msg.content}',
            color = discord.Color.red(),
            timestamp = datetime.datetime.utcnow()
        )
        embed.set_footer(text=f'Author: {msg.author.id} | Message ID: {msg.id}')
        embed.set_author(
            name = f'{msg.author.name}#{msg.author.discriminator}',
            icon_url = msg.author.avatar_url
        )
        notice = await ch.send(embed = embed)
        if msg.attachments:
            await notice.reply("該訊息的附件", files = [await i.to_file() for i in msg.attachments])

    @commands.is_owner()
    @commands.command()
    async def test(self, ctx):
        print(utils.abc())

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def dm_all(self, ctx, *msg):
        """dm specificate message to all guild member(carefully use)"""
        humans = [i for i in ctx.guild.members if not i.bot and i != ctx.author]
        unsend = {'disable_dm': [], 'unknown': []}
        count = 0
        notice = await ctx.send('發送中...')
        
        for member in humans:
            now = count
            try:
                await member.send(f'**{ctx.guild.name}** 公告\n作者: {ctx.author.mention}\n' + ' '.join(msg))
                count += 1
            except discord.Forbidden:
                unsend['disable_dm'].append(member)
            finally:
                if now == count and member not in unsend['disable_dm']:
                    unsend['unknown'].append(member)
        
        await notice.edit(content = 
        '發送成功!\n'
        f'實際發送人數/伺服器人數: {count}/{len(humans)}\n'
        f'關閉伺服器私訊: {" ".join([i.mention for i in unsend["disable_dm"]])}\n'
        f'其他原因: {" ".join([i.mention for i in unsend["unknown"]])}')

    @commands.command()
    async def ping(self, ctx):
        """Check Latency."""
        t = time.perf_counter()
        await ctx.trigger_typing()
        t2 = time.perf_counter()
        await ctx.trigger_typing()

        this = round((t2 - t) * 1000)
        ws = int(self.bot.latency * 1000)
        await ctx.send(f'延遲：{this} 毫秒(ms)\nWebsocket：{ws} 毫秒(ms)')

    @commands.is_owner()
    @commands.command()
    async def send_to(self, ctx, ch: int, *, text):
        """Send message to specific channel"""
        ch = self.bot.get_channel(ch)
        
        await ch.send(text)

    @commands.command()
    async def weather(self, ctx, locationName):
        url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-D0047-001'
        parms = {
            'Authorization': jdata['weather_auth'],
            'locationName': locationName,
            'elementName': 'PoP12h',
        }
        data = requests.get(url=url, params=parms)
        resault = json.loads(data.text)

        embed = discord.Embed(title='未來3天每12小時降雨機率', description=f'宜蘭縣 {locationName}', color=0x0080ff)
        for i in resault['records']['locations'][0]['location'][0]['weatherElement'][0]['time']:
            embed.add_field(name=i['startTime'], value=f'{i["elementValue"][0]["value"]}%', inline=True)
        embed.set_footer(text="資料來源:中央氣象局")
        await ctx.send(embed=embed)

    @commands.command()
    async def earthquake(self, ctx):
        """Get latest earthquake info."""
        url1 = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0015-001'
        url2 = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001'
        parms = {
            'Authorization': jdata['weather_auth']
        }
        resault1 = json.loads(requests.get(url1, params=parms).text)
        resault2 = json.loads(requests.get(url2, params=parms).text)
        if resault1['records']['earthquake'][0]['earthquakeInfo']['originTime'] > resault2['records']['earthquake'][0]['earthquakeInfo']['originTime']:
            resault = resault1
        else:
            resault = resault2

        embed = discord.Embed()
        embed.set_image(url=resault['records']['earthquake'][0]['reportImageURI'])
        await ctx.send(f'{resault["records"]["earthquake"][0]["reportContent"]}\n資料來源:中央氣象局\n網址:{resault["records"]["earthquake"][0]["web"]}', embed=embed)

    @commands.command()
    async def slap(self, ctx, *, reason: Slaper):
        """Slap random people in guild."""
        await ctx.send(reason)

    @commands.command()
    async def get_emojis(self, ctx):
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
    
    @commands.is_owner()
    @commands.command()
    async def custom_emoji(self, ctx, name, *roles):
        await ctx.trigger_typing()

        if not ctx.message.attachments:
            await ctx.send('你沒有上傳任何檔案!')
            return

        if not roles:
            await ctx.send('你沒有指定可用的身份組!')
            return
        
        for count, file in enumerate(ctx.message.attachments):
            await ctx.guild.create_custom_emoji(
                name = name + count+1,
                image = await file.read(),
                roles = [i for i in ctx.guild.roles for j in roles if i.mention == j],
                reason = 'custom_emoji'
            )

        await ctx.send(f'{len(ctx.message.attachments)}個表情符號增加成功!')

    @commands.command()
    async def get_avatar(self, ctx, user: discord.User):
        """Get specific member's avatar."""
        await ctx.send(user.avatar_url)

    @commands.has_permissions(manage_channels=True)
    @commands.command()
    async def voicemoveall(self, ctx, origin: discord.VoiceChannel, target: discord.VoiceChannel):
        """Move all member from a to b."""
        if ctx.author.guild_permissions.move_members:
            if origin in ctx.guild.voice_channels and target in ctx.guild.voice_channels:
                for members in origin.members:
                    await members.edit(voice_channel=target)
                    
        res = f"把所有成員從 {origin.mention} 移動到 {target.mention} 成功"
        await ctx.send(res)

    @commands.has_guild_permissions(manage_messages = True)
    @commands.command()
    async def clear_afterid(self, ctx, msg: discord.Message):
        """Clear message after message you specific(limit: 100)."""
        await ctx.trigger_typing()

        time = msg.created_at - datetime.timedelta(microseconds=1)
        
        await msg.channel.purge(after = time, bulk = True)
        await ctx.send(f'**{msg.channel}** {msg.id} 後(含)的訊息刪除成功!', delete_after = 7)

    @commands.is_owner()
    @commands.command()
    async def clear_aroundid(self, ctx, start: discord.Message, end: discord.Message):
        await ctx.trigger_typing()

        start_time = start.created_at - datetime.timedelta(microseconds=1)
        end_time = end.created_at + datetime.timedelta(microseconds=1)
        
        await ctx.channel(after=start_time, before=end_time, bulk=True)
        await ctx.send(f'**{ctx.channel}** {start.id} 到 {end.id} 的訊息刪除成功!', delete_after=7)

    @commands.is_owner()
    @commands.command()
    async def get_nick(self, ctx, member: discord.Member):
        """Get specific member's nick."""
        await ctx.send(member.nick)

    @commands.is_owner()
    @commands.command()
    async def nick(self, ctx, location = None, nick = None):
        """Change member's nick."""
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
    @commands.command()
    async def mute(self, ctx, member: discord.Member):
        """Mute member."""
        self.spam[member.id] = {
                'time': 31536000,
                'mute': True,
                'member': member
            }
        
        role = discord.utils.get(ctx.guild.roles, name = 'Muted')
        await member.add_roles(role, reason = '自動防洗頻系統(手動)')

        await ctx.send(f'以手動靜音 {member.mention} !')

    @commands.has_guild_permissions(manage_messages = True)
    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        """Unmute member."""
        try:
            if not self.spam[member.id]['mute']:
                await ctx.send('這位成員沒有被靜音!')
                return 0
        except KeyError:
            await ctx.send('這位成員沒有被靜音!')
            return 0
            
        del self.spam[member.id]
        
        role = discord.utils.get(ctx.guild.roles, name = 'Muted')
        await member.remove_roles(role, reason = '自動防洗頻系統(手動)')

        await ctx.send(f'以解除靜音 {member.mention} !')


def setup(bot: commands.Bot):
    bot.add_cog(Fox(bot))