import discord
from discord.ext import commands
import requests
import random
from settings import PREFIX

class JokeCog(commands.Cog):
    """Cog for fetching jokes from the Official Joke API"""

    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://official-joke-api.appspot.com"
        self.categories = ["general", "programming", "knock-knock", "dad"]

    def fetch(self, endpoint: str):
        try:
            r = requests.get(f"{self.api_base}/{endpoint}", timeout=5)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception as e:
            print(f"Error fetching jokes: {e}")
            return None

    def format_joke(self, joke):
        return f"**{joke['setup']}**\n{joke['punchline']}"

    # --- Main group ---
    @commands.group(name="joke", invoke_without_command=True)
    async def joke(self, ctx):
        """!joke → Get one random joke"""
        joke = self.fetch("random_joke")
        if joke:
            await ctx.send(self.format_joke(joke))
        else:
            await ctx.send("⚠️ Couldn't fetch a joke right now.")

    # --- Help ---
    @joke.command(name="help")
    async def joke_help(self, ctx):
        """!joke help → Show command usage"""
        embed = discord.Embed(
            title="📖 Joke Command Help",
            description="Here are all available joke commands:",
            color=discord.Color.green()
        )
        embed.add_field(name=PREFIX+"joke", value="Get one random joke.", inline=False)
        embed.add_field(name=PREFIX+"joke categories", value="Show available categories.", inline=False)
        embed.add_field(name=PREFIX+"joke joke <number>", value="Get `<number>` random jokes.", inline=False)
        embed.add_field(name=PREFIX+"joke category <category>", value="Get one random joke from that category.", inline=False)
        embed.add_field(name=PREFIX+"joke jokes <number> <category>", value="Get `<number>` random jokes from that category.", inline=False)
        embed.add_field(name="Available Categories", value=", ".join(self.categories), inline=False)

        await ctx.send(embed=embed)

    # --- Subcommands ---
    @joke.command(name="categories")
    async def categories(self, ctx):
        """!joke categories → Show available categories"""
        await ctx.send("📂 Available categories:\n" + ", ".join(self.categories))

    @joke.command(name="joke")
    async def single_jokes(self, ctx, number: int):
        """!joke joke <number> → Get <number> random jokes"""
        number = min(number, 10)  # API only provides 10 random at once
        jokes = self.fetch("random_ten")
        if jokes:
            selected = random.sample(jokes, min(number, len(jokes)))
            await ctx.send("\n\n".join(self.format_joke(j) for j in selected))
        else:
            await ctx.send("⚠️ Couldn't fetch jokes right now.")

    @joke.command(name="category")
    async def category(self, ctx, category: str):
        """!joke category <category> → Get one random joke from that category"""
        category = category.lower()
        if category not in self.categories:
            await ctx.send(f"❌ Invalid category. Try: {', '.join(self.categories)}")
            return

        jokes = self.fetch(f"jokes/{category}/random")
        if jokes:
            await ctx.send(self.format_joke(jokes[0]))
        else:
            await ctx.send("⚠️ Couldn't fetch a joke from that category.")

    @joke.command(name="jokes")
    async def multiple_category_jokes(self, ctx, number: int, category: str):
        """!joke jokes <number> <category> → Get <number> random jokes from that category"""
        category = category.lower()
        if category not in self.categories:
            await ctx.send(f"❌ Invalid category. Try: {', '.join(self.categories)}")
            return

        jokes = self.fetch(f"jokes/{category}/ten")
        if jokes:
            selected = random.sample(jokes, min(number, len(jokes)))
            await ctx.send("\n\n".join(self.format_joke(j) for j in selected))
        else:
            await ctx.send("⚠️ Couldn't fetch jokes from that category.")


async def setup(bot):
    await bot.add_cog(JokeCog(bot))
