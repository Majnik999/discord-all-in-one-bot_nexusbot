import discord
from discord.ext import commands
from settings import CLEAR_COMMAND

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clear", description="Deletes a specified number of messages.")
    @commands.bot_has_permissions(manage_messages=True)
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, messages: int):
        if not CLEAR_COMMAND: return
        if messages and messages <= 1:
            await ctx.send("⚠️ The specified number must be greater than 1!")
        
        await ctx.channel.purge(limit=messages + 1)
        
        await ctx.send(f"✅ Successfully cleared {messages} messages!", delete_after=5)
        
    @clear.error
    async def clear_error(ctx, error):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have permissions for deleting messages. Please check my permission!")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permissions for deleting messages. This is moderator only command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ Missing required argument. Please double check the command!")
        else:
            await ctx.send("❌ An Unexpected Error occurred!")


async def setup(bot):
    await bot.add_cog(Moderation(bot))