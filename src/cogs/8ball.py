import discord
from discord.ext import commands

import random

class Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['8ball'])
    async def _8ball(self, ctx, *, question):
        responses = [
            'It is certain.', 
            'It is decidedly so.',
            'Without a doubt.',
            'Yes - definitely.', 
            'You may rely on it.', 
            'Most likely.',
            'Outlook good.', 
            'Yes.', 
            'Signs point to yes.',
            'Reply hazy, try again.', 
            'Ask again later.',
            'Better not tell you now.', 
            'Cannot predict now.',
            'Concentrate and ask again.', 
            "Don't count on it.", 
            'My reply is no.',
            'My sources say no.', 
            'Outlook not very good.', 
            'Very doubtful.'
            ]
        
        await ctx.send(embed=discord.Embed(
            title="8Ball",
            description=f"`{random.choice(responses)}`"
        ))


async def setup(bot):
    await bot.add_cog(Ball(bot))
    