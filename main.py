import discord
from discord.ext import commands, tasks
import random
import json
import os
import asyncio
from keep_alive import keep_alive  
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# --- Define intents (very important!) ---
intents = discord.Intents.default()
intents.message_content = True  # Required to read messages
intents.guilds = True
intents.members = True

# --- Create the client with intents ---
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Example simple command
    if message.content.startswith("!hello"):
        await message.channel.send(f"Hello {message.author.display_name}! 👋")

# --- Run the bot ---
client.run(TOKEN)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = 'data.json'

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
else:
    data = {"users": {}}


def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


key_emojis = {
    "common": "🗝️",
    "uncommon": "🔑",
    "rare": "💎",
    "legendary": "🏆",
    "divine": "🌌",
    "prismatic": "✨"
}

key_drop_chance = 5  
key_rarities = {
    "common": 60,
    "uncommon": 30,
    "rare": 15,
    "legendary": 5,
    "divine": 1,
    "prismatic": 0.05
}

key_rewards = {
    "common": (10, 20),
    "uncommon": (20, 40),
    "rare": (50, 100),
    "legendary": (150, 250),
    "divine": (400, 600),
    "prismatic": (1000, 2000)
}


@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    keep_alive_task.start()
    drop_check.start()


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in data["users"]:
        data["users"][user_id] = {"kan": 0, "inventory": [], "keys": {}}

    
    if random.random() < (key_drop_chance / 100):
        rarity = random.choices(
            population=list(key_rarities.keys()),
            weights=list(key_rarities.values()),
            k=1
        )[0]

        user = message.author
        data["users"][user_id]["keys"][rarity] = data["users"][user_id]["keys"].get(rarity, 0) + 1
        save_data()

        embed = discord.Embed(
            title="🎉 Key Drop!",
            description=f"{user.mention} found a **{rarity.capitalize()} Key** {key_emojis[rarity]}!",
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed)

    await bot.process_commands(message)


@bot.command()
async def bal(ctx):
    user_id = str(ctx.author.id)
    bal = data["users"].get(user_id, {}).get("kan", 0)
    embed = discord.Embed(
        title=f"{ctx.author.name}'s Balance",
        description=f"You currently have **{bal}💰 Kan**.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command()
async def redeem(ctx, rarity: str = None, amount: str = None):
    user_id = str(ctx.author.id)
    user_keys = data["users"][user_id].get("keys", {})

    if rarity is None:
        await ctx.send("❌ Please specify which key to redeem (e.g. `!redeem common` or `!redeem all`).")
        return

    rarity = rarity.lower()

    if rarity == "all":
        total_kan = 0
        total_keys = 0
        for r, count in user_keys.items():
            if count > 0:
                for _ in range(count):
                    total_kan += random.randint(*key_rewards[r])
                    total_keys += count
                user_keys[r] = 0
        if total_kan == 0:
            await ctx.send("❌ You have no keys to redeem.")
            return

        data["users"][user_id]["kan"] += total_kan
        save_data()

        embed = discord.Embed(
            title="🔓 All Keys Redeemed!",
            description=f"You redeemed **all your keys** and earned a total of **{total_kan}💰 Kan!** 🎉",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        return

    
    if rarity not in key_rewards:
        await ctx.send("❌ Invalid key rarity.")
        return

    
    if amount == "all":
        if user_keys.get(rarity, 0) < 1:
            await ctx.send(f"❌ You don’t have any {rarity} keys.")
            return

        count = user_keys[rarity]
        total_reward = sum(random.randint(*key_rewards[rarity]) for _ in range(count))
        user_keys[rarity] = 0
        data["users"][user_id]["kan"] += total_reward
        save_data()

        embed = discord.Embed(
            title=f"🔓 Redeemed All {rarity.capitalize()} Keys!",
            description=f"You redeemed **{count}x {rarity.capitalize()} Keys** {key_emojis[rarity]} and earned **{total_reward}💰 Kan!** 🎉",
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)
        return

    
    if user_keys.get(rarity, 0) < 1:
        await ctx.send(f"❌ You don’t have a {rarity} key.")
        return

    reward = random.randint(*key_rewards[rarity])
    data["users"][user_id]["kan"] += reward
    data["users"][user_id]["keys"][rarity] -= 1
    save_data()

    embed = discord.Embed(
        title="🔓 Key Redeemed!",
        description=f"You redeemed a **{rarity.capitalize()} Key** {key_emojis[rarity]} and got **{reward}💰 Kan!**",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)


@bot.command()
async def inv(ctx):
    user_id = str(ctx.author.id)
    inv = data["users"][user_id].get("inventory", [])
    inv_text = "\n".join(inv) if inv else "Your inventory is empty!"
    embed = discord.Embed(title="🎒 Inventory", description=inv_text, color=discord.Color.teal())
    await ctx.send(embed=embed)


@bot.command()
async def keys(ctx):
    user_id = str(ctx.author.id)
    user_keys = data["users"][user_id].get("keys", {})
    desc = "\n".join([f"{key_emojis[k]} **{k.capitalize()} Key:** {v}" for k, v in user_keys.items()]) or "No keys yet!"
    embed = discord.Embed(title="🗝️ Your Keys", description=desc, color=discord.Color.purple())
    await ctx.send(embed=embed)


@bot.command()
async def shop(ctx):
    shop_items = {
        "Sword": 100,
        "Shield": 150,
        "Potion": 50
    }
    desc = "\n".join([f"**{item}** — {price}💰 Kan" for item, price in shop_items.items()])
    embed = discord.Embed(title="🛒 Shop", description=desc, color=discord.Color.orange())
    await ctx.send(embed=embed)


@bot.command()
async def buy(ctx, *, item: str):
    user_id = str(ctx.author.id)
    shop_items = {
        "sword": 100,
        "shield": 150,
        "potion": 50
    }

    item = item.lower()
    if item not in shop_items:
        await ctx.send("❌ Item not found.")
        return

    price = shop_items[item]
    if data["users"][user_id]["kan"] < price:
        await ctx.send("❌ Not enough Kan!")
        return

    data["users"][user_id]["kan"] -= price
    data["users"][user_id]["inventory"].append(item.capitalize())
    save_data()

    embed = discord.Embed(
        title="✅ Purchase Successful!",
        description=f"You bought a **{item.capitalize()}** for {price}💰 Kan.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command()
async def top(ctx):
    leaderboard = sorted(data["users"].items(), key=lambda x: x[1]["kan"], reverse=True)
    desc = "\n".join(
        [f"**{i+1}.** <@{u}> — {v['kan']}💰 Kan" for i, (u, v) in enumerate(leaderboard[:10])]
    )
    embed = discord.Embed(title="🏆 Leaderboard", description=desc or "No data yet!", color=discord.Color.gold())
    await ctx.send(embed=embed)


@tasks.loop(minutes=5)
async def keep_alive_task():
    channel_id = 1430830649480052826  # Replace with your Discord channel ID
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("🤖 Staying active!")


@tasks.loop(minutes=1)
async def drop_check():
    save_data()


keep_alive()
