import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import random
import io
import json
import os
from settings import WORDLE_WORDS

# Example 100 words
WORDS = WORDLE_WORDS

FONT_PATH = "src/font/arial.ttf"
FONT_SIZE = 40

CELL_SIZE = 60
PADDING = 10
SAVE_FILE = "src/games/wordle_games.json"

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = self.load_games()

    # --- Save / Load ---
    def save_games(self):
        with open(SAVE_FILE, "w") as f:
            json.dump(self.active_games, f)

    def load_games(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        return {}

    @commands.group(name="wordle", invoke_without_command=True)
    async def wordle_group(self, ctx):
        await ctx.send("Use `!wordle start <length>` to start a game or `!wordle stop` to stop your game.")

    @wordle_group.command(name="start")
    async def start_wordle(self, ctx, length: int = 5):
        if length < 3 or length > 10:
            return await ctx.send("Word length must be between 3 and 10 letters.")
        if ctx.author.id in self.active_games:
            return await ctx.send("You already have an active game!")

        # filter words by length
        possible_words = [w for w in WORDS if len(w) == length]
        if not possible_words:
            return await ctx.send("No words available for that length.")
        word = random.choice(possible_words).lower()

        self.active_games[ctx.author.id] = {
            "word": word,
            "guesses": [],
            "current_guess": ""
        }
        self.save_games()

        embed = discord.Embed(
            title=f"Wordle 🟩 🟨 ⬜ ({length} letters)",
            description=f"Guess the word by typing `!<yourguess>`",
            color=discord.Color.green()
        )
        img_file = self.generate_image(ctx.author.id)
        embed.set_image(url="attachment://wordle.png")
        await ctx.send(embed=embed, file=img_file)

    @wordle_group.command(name="stop")
    async def stop_wordle(self, ctx):
        if ctx.author.id not in self.active_games:
            return await ctx.send("You have no active game.")
        del self.active_games[ctx.author.id]
        self.save_games()
        await ctx.send("Wordle game stopped.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.startswith("!") and len(message.content) > 1:
            if message.content[1:].lower() == "stop":
                del self.active_games[message.author.id]
                self.save_games()
                return await message.channel.send("Game has been terminated!")
            guess = message.content[1:].lower()
            if message.author.id not in self.active_games:
                return
            game = self.active_games[message.author.id]
            word = game["word"]

            if len(guess) != len(word):
                await message.channel.send(f"Your guess must be {len(word)} letters long.")
                return
            if len(game["guesses"]) >= 6:
                await message.channel.send("You've already used all your guesses!")
                return

            game["guesses"].append(guess)
            game["current_guess"] = ""
            self.save_games()

            if guess == word:
                embed = discord.Embed(
                    title="Wordle 🟩 🟨 ⬜",
                    description=f"🎉 Congrats {message.author.mention}! You guessed the word `{word}`!",
                    color=discord.Color.green()
                )
                img_file = self.generate_image(message.author.id)
                embed.set_image(url="attachment://wordle.png")
                await message.channel.send(embed=embed, file=img_file)
                del self.active_games[message.author.id]
                self.save_games()
                return
            elif len(game["guesses"]) == 6:
                embed = discord.Embed(
                    title="Wordle 🟩 🟨 ⬜",
                    description=f"😢 Game over! The word was `{word}`.",
                    color=discord.Color.red()
                )
                img_file = self.generate_image(message.author.id)
                embed.set_image(url="attachment://wordle.png")
                await message.channel.send(embed=embed, file=img_file)
                del self.active_games[message.author.id]
                self.save_games()
                return

            # normal update
            embed = discord.Embed(
                title=f"Wordle 🟩 🟨 ⬜ ({len(word)} letters)",
                description=f"Guess the word by typing `!<yourguess>`\nStop game with `!stop`",
                color=discord.Color.green()
            )
            img_file = self.generate_image(message.author.id)
            embed.set_image(url="attachment://wordle.png")
            await message.channel.send(embed=embed, file=img_file)

    def generate_image(self, user_id):
        game = self.active_games[user_id]
        guesses = game["guesses"]
        current = game.get("current_guess", "")
        word_length = len(game["word"])
        rows = 6

        img_width = word_length * CELL_SIZE + (word_length + 1) * PADDING
        img_height = rows * CELL_SIZE + (rows + 1) * PADDING
        image = Image.new("RGB", (img_width, img_height), color=(30,30,30))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except OSError:
            font = ImageFont.load_default()

        for row in range(rows):
            for col in range(word_length):
                x0 = PADDING + col * (CELL_SIZE + PADDING)
                y0 = PADDING + row * (CELL_SIZE + PADDING)
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                fill_color = (50,50,50)
                letter = ""

                if row < len(guesses):
                    letter = guesses[row][col]
                    if letter == game["word"][col]:
                        fill_color = (106,170,100)
                    elif letter in game["word"]:
                        fill_color = (201,180,88)
                    else:
                        fill_color = (120,124,126)
                elif row == len(guesses) and col < len(current):
                    letter = current[col]
                    fill_color = (50,50,50)

                draw.rectangle([x0,y0,x1,y1], outline=(255,255,255), width=3, fill=fill_color)
                if letter:
                    bbox = draw.textbbox((0,0), letter.upper(), font=font)
                    w = bbox[2]-bbox[0]
                    h = bbox[3]-bbox[1]
                    draw.text((x0+(CELL_SIZE-w)/2, y0+(CELL_SIZE-h)/2), letter.upper(), font=font, fill=(255,255,255))

        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        buffer.seek(0)
        return discord.File(fp=buffer, filename="wordle.png")

async def setup(bot):
    await bot.add_cog(Wordle(bot))
