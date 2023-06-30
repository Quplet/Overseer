import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from enum import Enum

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

valid_slugcats_rw = ['monk', 'survivor', 'hunter']
valid_slugcats_dp = ['gourmand', 'artificer', 'rivulet', 'spearmaster', 'saint', 'inv']

class Action(Enum):
    START = 0
    FINISH = 1
    UPGRADE = 2

@bot.event
async def on_ready():
    global bot_channel, info_channel, rw_category, dp_category, read_false_permissions, read_true_permissions
    guild = bot.get_guild(os.getenv('SERVER_ID'))
    bot_channel = discord.utils.get(guild.channels, id=os.getenv('BOT_CHANNEL_ID'))
    info_channel = discord.utils.get(guild.channels, id=os.getenv('INFO_CHANNEL_ID'))
    rw_category = discord.utils.get(guild.categories, id=os.getenv('RW_CATEGORY_ID'))
    dp_category = discord.utils.get(guild.categories, id=os.getenv('DP_CATEGORY_ID'))

    read_false_permissions = discord.PermissionOverwrite()
    read_false_permissions.read_messages = False
    
    read_true_permissions = discord.PermissionOverwrite()
    read_true_permissions.read_messages = True

    print(f'Logged in as {bot.user}')

def is_valid_origin_channel(origin: discord.TextChannel, author: discord.member, action: Action) -> bool:
    if origin is bot_channel and action != Action.UPGRADE:
        return True
    
    return (origin.category is rw_category or origin.category is dp_category) and origin.permissions_for(author).manage_messages


@bot.command()
async def start(ctx: commands.context, channel_type: str) -> None:
    if not is_valid_origin_channel(ctx.channel, ctx.author, Action.START):
        return

    guild = ctx.guild
    author = ctx.author
    channel_type = channel_type.lower()
    
    category = None
    default_scug_name = None
    match channel_type:
        case 'rw':
            category = rw_category
            default_scug_name = valid_slugcats_rw[1] # survivor
        case 'dp':
            category = dp_category
            default_scug_name = valid_slugcats_dp[0] # gourmand
        case _:
            await ctx.send('Please provide a valid channel type, either \'rw\' or \'dp\'')
            return
    
    perms = {guild.default_role : read_false_permissions}
    min_scug_role = discord.utils.get(guild.roles, name=default_scug_name.capitalize())
    perms[min_scug_role] = read_true_permissions
    perms[author] = discord.PermissionOverwrite.from_pair(allow=[('read_messages', True), ('manage_messages', True)], deny=[])

    channel = await guild.create_text_channel(f'{author.name.replace(" ", "-")}-{default_scug_name}', category=category, overwrites=perms)

    await ctx.send(f'Created {channel.mention}!')
    await channel.send(f'{author.mention} Here you go! Best of luck to you! See {info_channel.mention} for Rain World tips, tricks, and QoL improvements!')
    print(f'Created {channel.name} at {channel.created_at}.')

@bot.command()
async def finished(ctx: commands.context, slugcat: str) -> None:
    member = ctx.author
    if not is_valid_origin_channel(ctx.channel, member, Action.FINISH):
        return
    
    slugcat = slugcat.lower()

    if slugcat not in valid_slugcats_rw or slugcat not in valid_slugcats_dp:
        await ctx.send('Please enter valid slugcat name!')
        return
    
    guild = ctx.guild
    role = discord.utils.get(guild.roles, name=slugcat.capitalize())

    if member.get_role(role.id) is not None:
        await ctx.send(f'{member.name} already has that role.')
        return

    await member.add_roles(role)
    await ctx.send(f'Added {role.name} to {member.name}.')
    print(f'Given role {role.name} to {member.name}.')

@bot.command()
async def upgrade(ctx: commands.context, slugcat: str) -> None:
    channel = ctx.channel
    if not is_valid_origin_channel(channel, ctx.author, Action.UPGRADE):
        return
    
    slugcat = slugcat.lower()
    guild = ctx.guild
    upgrade_role = discord.utils.get(guild.roles, name=slugcat.capitalize())

    async def alter_perms(valid_slugcat_list: list):
        for slugcat_iter in valid_slugcat_list:
            role_iter = discord.utils.get(guild.roles, name=slugcat_iter.capitalize())
            await channel.set_permissions(role_iter, overwrite=read_false_permissions)
        await channel.set_permissions(upgrade_role, overwrite=read_true_permissions)

    if slugcat in valid_slugcats_rw and channel.category is rw_category:
        await alter_perms(valid_slugcats_rw)
    elif slugcat in valid_slugcats_dp and channel.category is dp_category:
        await alter_perms(valid_slugcats_dp)
    else:
        await ctx.send('The given slugcat is not a valid upgrade option for this category!')
        return
    
    channel.name = f'{ctx.author.replace(" ", "-")}-{slugcat}'
    await ctx.send(f'Changed this channel to {upgrade_role.name}!')
    print(f'Changed {channel.name} slugcat to {upgrade_role.name}.')

bot.run(token)