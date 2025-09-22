import os
import json
import random
import discord
from discord.ext import commands
from discord.ui import View, Button
from main import logger, PREFIX
from settings import MAZE_HEIGHT, MAZE_WIDTH

SAVE_FILE = "src/games/maze_games.json"

# --- Maze Constants ---
PLAYER = "@"
GOAL = "F"
WALL = "▓"
PATH = "░"

# --- Game Logic ---
def create_maze(width: int, height: int):
    """Generate a random maze using DFS backtracking."""
    maze = [[WALL for _ in range(width)] for _ in range(height)]

    def carve(x, y):
        maze[y][x] = PATH
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < width - 1 and 1 <= ny < height - 1 and maze[ny][nx] == WALL:
                maze[y + dy // 2][x + dx // 2] = PATH
                carve(nx, ny)

    start_x, start_y = random.randrange(1, width, 2), random.randrange(1, height, 2)
    carve(start_x, start_y)

    # Place player
    maze[start_y][start_x] = PLAYER

    # Place goal
    gx, gy = start_x, start_y
    while (gx, gy) == (start_x, start_y) or maze[gy][gx] == WALL:
        gx, gy = random.randrange(1, width - 1), random.randrange(1, height - 1)
    maze[gy][gx] = GOAL

    return maze

def locate_player(maze):
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == PLAYER:
                return y, x
    return None, None

def render_board(maze, level, moves):
    rows = [" ".join(r) for r in maze]
    return f"Level: {level} | Moves: {moves}\n```\n" + "\n".join(rows) + "\n```"

def save_games(games):
    with open(SAVE_FILE, "w") as f:
        json.dump(games, f)

def load_games():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {}

# --- UI View ---
class MazeView(View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = str(user_id)

        # Direction buttons
        self.add_item(Button(label="↑", style=discord.ButtonStyle.secondary, custom_id="up"))
        self.add_item(Button(label="←", style=discord.ButtonStyle.secondary, custom_id="left"))
        self.add_item(Button(label="→", style=discord.ButtonStyle.secondary, custom_id="right"))
        self.add_item(Button(label="↓", style=discord.ButtonStyle.secondary, custom_id="down"))
        self.add_item(Button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # all interactions allowed; ownership checked below

    async def on_timeout(self):
        # auto disable buttons on timeout (not required since we use timeout=None)
        for item in self.children:
            item.disabled = True

    async def on_button_click(self, interaction: discord.Interaction, button_id: str):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Not your game.", ephemeral=True)

        if button_id == "stop":
            if self.user_id in self.cog.games:
                game = self.cog.games[self.user_id]
                del self.cog.games[self.user_id]
                save_games(self.cog.games)
                embed = discord.Embed(title="🛑 Game Ended")
                embed.add_field(
                    name="Board",
                    value=render_board(game["maze"], game["level"], game["moves"]),
                    inline=False
                )
                embed.set_footer(text="This is just a memory of the game not an actual game!")
                return await interaction.response.edit_message(embed=embed, view=None)
            return await interaction.response.send_message("⚠️ No active game.", ephemeral=True)

        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        dr, dc = moves[button_id]

        game = self.cog.games.get(self.user_id)
        if not game:
            return await interaction.response.send_message(f"⚠️ No active game. Start one with `{PREFIX}maze start`.", ephemeral=True)

        maze, level, move_count = game["maze"], game["level"], game["moves"]
        r, c = locate_player(maze)
        nr, nc = r + dr, c + dc

        if not (0 <= nr < len(maze) and 0 <= nc < len(maze[0])):
            return await interaction.response.send_message("🚧 Outside bounds!", ephemeral=True)
        if maze[nr][nc] == WALL:
            return await interaction.response.send_message("❌ You hit a wall!", ephemeral=True)

        if maze[nr][nc] == GOAL:
            game["level"] += 1
            game["moves"] = 0
            game["width"] += 2
            game["height"] += 2
            game["maze"] = create_maze(game["width"], game["height"])
            save_games(self.cog.games)

            embed = discord.Embed(
                title="🎉 Level Complete!",
                description=f"You finished **Level {level}** in {move_count + 1} moves!",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Next Level",
                value=render_board(game["maze"], game["level"], 0),
                inline=False
            )
            return await interaction.response.edit_message(embed=embed, view=self)

        # regular move
        maze[r][c] = PATH
        maze[nr][nc] = PLAYER
        game["moves"] += 1
        save_games(self.cog.games)

        embed = discord.Embed(title="Maze Game")
        embed.add_field(
            name="Board",
            value=render_board(maze, game["level"], game["moves"]),
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data and "custom_id" in interaction.data:
            await self.on_button_click(interaction, interaction.data["custom_id"])
            return False
        return True

# --- Cog ---
class MazeGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = load_games()

    @commands.group(name="maze", invoke_without_command=True)
    async def maze(self, ctx):
        embed = discord.Embed(
            title="Maze Game 🌀 - Help",
            description=f"How to play:\n* Start game with commands (down in section commands)\n* Navigate maze to `{GOAL}` to reach end of level with buttons\n\nSome Commands to help you start a maze game:"
        )
        
        embed.add_field(name=PREFIX+"maze", value="Shows this message!", inline=False)
        embed.add_field(name=PREFIX+"maze start", value="Starts a maze game!", inline=False)
        embed.add_field(name=PREFIX+"maze here", value="Calls maze game to channel where you entered command!", inline=False)
        embed.add_field(name=PREFIX+"maze board", value="Shows board of maze game", inline=False)
        embed.add_field(name=PREFIX+"maze status", value="Shows status of maze game", inline=False)
        
        embed.set_footer(text="Help command for maze game!")
        
        await ctx.send(embed=embed)
        
    @maze.command(name="start")
    async def start_maze(self, ctx):
        user_id = str(ctx.author.id)
        
        if user_id in self.games:
            return await ctx.send(f"⚠️ You have an active game. See game with `{PREFIX}maze board` play game here with `{PREFIX}maze here`")
        
        width, height = MAZE_WIDTH, MAZE_HEIGHT
        maze = create_maze(width, height)
        self.games[user_id] = {
            "maze": maze,
            "level": 1,
            "moves": 0,
            "width": width,
            "height": height
        }
        save_games(self.games)

        embed = discord.Embed(
            title="Maze Game 🌀",
            description=f"Use the buttons to move and reach **{GOAL}**!\n\nSome Info:\n* {PLAYER} stands for Player\n* {GOAL} stands for Finish/Goal"
        )
        embed.add_field(name="Board", value=render_board(maze, 1, 0), inline=False)

        await ctx.send(embed=embed, view=MazeView(self, user_id))

    @maze.command(name="here")
    async def show_status(self, ctx):
        user_id = str(ctx.author.id)
        
        if user_id not in self.games:
            return await ctx.send(f"⚠️ No active game. Start one with `{PREFIX}maze start`.")

        game = self.games[user_id]
        embed = discord.Embed(title="🌀 Maze Here")
        embed.add_field(
            name="Board",
            value=render_board(game["maze"], game["level"], game["moves"]),
            inline=False
        )
        await ctx.send(embed=embed, view=MazeView(self, user_id))
    
    @maze.command(name="board")
    async def maze_board(self, ctx):
        user_id = str(ctx.author.id)
        
        if user_id not in self.games:
            return await ctx.send(f"⚠️ No active game. Start one with `{PREFIX}maze start`.")

        game = self.games[user_id]
        embed = discord.Embed(title="🌀 Maze Board")
        embed.add_field(
            name="Board",
            value=render_board(game["maze"], game["level"], game["moves"]),
            inline=False
        )
        await ctx.send(embed=embed)
    
    @maze.command(name="status")
    async def maze_status(self, ctx):
        user_id = str(ctx.author.id)
        
        if user_id not in self.games:
            return await ctx.send(f"⚠️ No active game. Start one with `{PREFIX}maze start`.")
        
        game = self.games[user_id]
        embed = discord.Embed(title="🌀 Maze Status")
        embed.add_field(
            name="Status of board:",
            value=f"Level: {game['level']} | Moves: {game['moves']}",
            inline=False
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MazeGame(bot))
