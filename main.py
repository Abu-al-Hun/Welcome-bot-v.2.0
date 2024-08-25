import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
from art import text2art
from colorama import Fore, Style

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
Exit_channel = int(os.getenv('Exit_channel'))
EMBED_IMAGE_URL = os.getenv('EMBED_IMAGE_URL')
BUTTON_URL = os.getenv('BUTTON_URL')
BUTTON_NAME = os.getenv('BUTTON_NAME')
member_ROLE_ID = int(os.getenv('member_ROLE_ID'))
BOT_ROLE_ID = int(os.getenv('BOT_ROLE_ID'))
RULES_CHANNEL_URL = os.getenv('RULES_CHANNEL_URL')
WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE')

if not DISCORD_TOKEN or not WELCOME_CHANNEL_ID or not Exit_channel or not EMBED_IMAGE_URL or not BUTTON_URL or not BUTTON_NAME or not member_ROLE_ID or not BOT_ROLE_ID or not RULES_CHANNEL_URL or not WELCOME_MESSAGE:
    raise ValueError("Please make sure to set DISCORD_TOKEN, WELCOME_CHANNEL_ID, Exit_channel, EMBED_IMAGE_URL, BUTTON_URL, BUTTON_NAME, member_ROLE_ID, BOT_ROLE_ID, RULES_CHANNEL_URL, WELCOME_MESSAGE, From file.env")

link_data = {
    "wick": {
        "role_id": 12345678910
    },
    "WickStudio": {
        "role_id": 12345678910
    }
}

def create_link_json():
    if not os.path.exists('link.json'):
        with open('link.json', 'w') as f:
            json.dump(link_data, f, indent=4)
        print("Created link.json with initial data.")

def load_invite_links():
    global invite_links
    if os.path.exists('link.json'):
        with open('link.json', 'r') as f:
            invite_links = json.load(f)
    else:
        invite_links = {}
        print("link.json file does not exist. Ensure it's created.")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    try:
        ascii_art_text = text2art("Wick® Studio")

        print(Fore.LIGHTCYAN_EX + ascii_art_text + Style.RESET_ALL)
        print(Fore.LIGHTGREEN_EX + f"Logged in as {bot.user}" + Style.RESET_ALL)

        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.listening, name="Wick® Studio"))

        create_link_json()
        load_invite_links()

        bot.invites = {}
        for guild in bot.guilds:
            bot.invites[guild.id] = {}
            invites = await guild.invites()
            for invite in invites:
                bot.invites[guild.id][invite.code] = invite.uses
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Error in on_ready event: {e}" + Style.RESET_ALL)

@bot.event
async def on_member_join(member):
    if member.bot:
        role = discord.utils.get(member.guild.roles, id=BOT_ROLE_ID)
        if role:
            await member.add_roles(role)
        return

    role = discord.utils.get(member.guild.roles, id=member_ROLE_ID)
    if role:
        await member.add_roles(role)

    invites_after = await member.guild.invites()

    used_invite = None
    for invite in invites_after:
        if invite.uses > bot.invites[member.guild.id].get(invite.code, 0):
            used_invite = invite
            break

    bot.invites[member.guild.id] = {invite.code: invite.uses for invite in invites_after}

    welcome_message = WELCOME_MESSAGE.format(mention=member.mention)

    embed = discord.Embed(
        title=f"Welcome to {member.guild.name}",
        description=welcome_message,
        color=0xea0d0d
    )
    embed.set_thumbnail(url=member.avatar.url)
    
    embed.add_field(name="Username", value=member.name, inline=True)
    if used_invite:
        inviter = used_invite.inviter
        if inviter:
            embed.add_field(name="Invited By", value=inviter.mention, inline=True)
        embed.add_field(name="Invite Used", value=f"||{used_invite.code}||", inline=True)
    embed.add_field(name="You're Member", value=f"{member.guild.member_count}", inline=True)
    embed.add_field(name="Server Rules", value=f"[📜・rules]({RULES_CHANNEL_URL})", inline=True)
    
    embed.set_image(url=EMBED_IMAGE_URL)

    button = discord.ui.Button(label=BUTTON_NAME, url=BUTTON_URL)
    view = discord.ui.View()
    view.add_item(button)

    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed, view=view)

    try:
        dm_channel = await member.create_dm()
        await dm_channel.send(embed=embed)
    except discord.Forbidden:
        print(f"Unable to send DM to {member.name}.")
    except discord.HTTPException as e:
        print(f"Failed to send DM to {member.name}: {e}")

    if used_invite and used_invite.code in invite_links:
        additional_role_id = invite_links[used_invite.code]['role_id']
        additional_role = discord.utils.get(member.guild.roles, id=additional_role_id)
        if additional_role:
            await member.add_roles(additional_role)

@bot.event
async def on_member_remove(member):
    leave_channel = bot.get_channel(Exit_channel)
    if leave_channel:
        embed = discord.Embed(
            title="👋 Member Left",
            description=f"{member.name} has left the server.",
            color=0xf30d0d
        )
        embed.set_footer(text="We're sorry to see you go.")
        await leave_channel.send(embed=embed)

bot.run(DISCORD_TOKEN)
