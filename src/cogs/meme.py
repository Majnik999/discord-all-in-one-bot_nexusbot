import discord
from discord.ext import commands
import requests
import asyncio

class MemeCog(commands.Cog):
    """Cog for fetching memes using D3vd Meme API"""

    def __init__(self, bot, api_base: str = None):
        self.bot = bot
        self.api_base = api_base or "https://meme-api.com/gimme"  # newer endpoint

    async def fetch_meme(self, url: str):
        """Fetch meme JSON in a thread to avoid blocking"""
        def get_data():
            r = requests.get(url, timeout=8)
            return r.json()
        return await asyncio.to_thread(get_data)

    @commands.command(name="meme", help="Fetches random meme(s).")
    async def meme(self, ctx: commands.Context, count: int = 1, *, subreddit: str = None):
        # clamp count between 1–10 to avoid spam
        count = max(1, min(count, 10))

        if subreddit:
            url = f"{self.api_base}/{subreddit}/{count}"
        else:
            url = f"{self.api_base}/{count}"

        try:
            data = await self.fetch_meme(url)
        except Exception as e:
            await ctx.send("⚠️ Error fetching meme(s)")
            return

        memes = data.get("memes") if isinstance(data, dict) and "memes" in data else [data]

        if not memes:
            await ctx.send("Couldn't get meme 😢")
            return

        for meme in memes:
            embed = discord.Embed(
                title=meme.get("title", "Meme"),
                description=f"**Subreddit**: `{meme.get('subreddit', 'Unknown')}` | "
                            f"**Author**: `{meme.get('author', 'unknown')}`",
                url=meme.get("postLink")
            )
            embed.set_image(url=meme["url"])
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemeCog(bot))
