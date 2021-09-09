from typing import Dict, List
import discord

def find_invite_bycode(invites: List[discord.Invite], code: str) -> discord.Invite.code:
    for i in invites:
        if i.code == code:
            return i

def find_use_invite(before: List[discord.Invite], after: List[discord.Invite]) -> discord.Invite:
    for i in after:
        old = find_invite_bycode(before, i.code)
        if i.uses > old.uses:
            return i