import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from main import PREFIX

import json

# Create a cog class that inherits from commands.Cog.
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # This creates a command group named 'embed'.
    # It is a top-level command now, so we use @commands.group.
    @commands.group(name='embed', invoke_without_command=True)
    async def embed_commands(self, ctx):
        """A collection of commands for creating embeds."""
        embed = discord.Embed(
            title="Embeds",
            description="Embed commands:"
        )
        embed.add_field(name=PREFIX+"embed source message_id old/new", value="Gets source json code of embed!", inline=False)
        embed.add_field(name=PREFIX+"embed builder (TITLE) (DESCRIPTION)", value="TITLE and DESCRIPTION is not needed there is and full embed builder with just "+PREFIX+"embed builder", inline=False)
        embed.add_field(name=PREFIX+"embed info message_id", value="Gets message embed info!", inline=False)
        await ctx.send(embed=embed)

    # This is a subcommand for the 'embed_commands' group.
    # It can now be called with `!embed info`
    @embed_commands.command(name="source")
    async def embed_source(self, ctx, message_id: int, version: str = "new"):
        """
        Fetches all embeds from a message as JSON.
        Use 'old' for the raw Discord output or 'new' for a cleaned Discohook-friendly version.
        """
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            embed = discord.Embed(
                title="❌ Error",
                description="Message not found. Please make sure the message ID is correct and in the same channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if not message.embeds:
            embed = discord.Embed(
                title="❌ Error",
                description="This message has no embeds.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Determine which version to output
        if version.lower() == "old":
            # The original, raw Discord output
            embeds_data = [embed.to_dict() for embed in message.embeds]
            
            # If there's only one embed, don't put it in a list.
            if len(embeds_data) == 1:
                output_data = embeds_data[0]
            else:
                output_data = embeds_data
        else:
            # The cleaning logic is now inside the command
            def clean_embed_data(embed_dict):
                """
                Cleans the raw embed dictionary by removing Discord's internal keys
                that are not compatible with Discohook's JSON editor.
                """
                cleaned_dict = {}
                accepted_keys = [
                    "title", "description", "color", "url",
                    "author", "footer", "image", "thumbnail", "fields"
                ]

                for key, value in embed_dict.items():
                    if key in accepted_keys:
                        if key == "author":
                            cleaned_dict[key] = {k: v for k, v in value.items() if k in ["name", "url", "icon_url"]}
                        elif key == "footer":
                            cleaned_dict[key] = {k: v for k, v in value.items() if k in ["text", "icon_url"]}
                        elif key == "image" or key == "thumbnail":
                            cleaned_dict[key] = {"url": value.get("url")}
                        elif key == "fields":
                            cleaned_dict[key] = [{"name": f.get("name"), "value": f.get("value"), "inline": f.get("inline")} for f in value]
                        else:
                            cleaned_dict[key] = value

                return cleaned_dict

            # Clean all embeds before converting to JSON
            embeds_data = [clean_embed_data(embed.to_dict()) for embed in message.embeds]
            
            # Format the output to match the full webhook payload
            output_data = {
                "content": None,
                "embeds": embeds_data,
                "attachments": []
            }
        
        # Write to file and send
        try:
            with open("src/other/embed.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=4)
            
            embed = discord.Embed(
                title="✅ Success",
                description="Embed JSON has been generated and is ready to download.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, file=discord.File("src/other/embed.json"))
        except Exception as e:
            embed = discord.Embed(
                title="❌ Internal Error",
                description=f"An unexpected error occurred while processing the command:\n```python\n{e}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @embed_source.error
    async def embed_error(self, ctx, error):
        
    
        """
        Handles errors for the embed group and subcommands.
        """
        # The group command itself does not need specific error handling,
        # but the subcommands do. Let's make sure we catch the right errors.
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Arguments",
                description=f"You need to provide all required arguments. Correct usage: `!embed info <message_id> [version]`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description="The message ID must be a number. Please provide a valid message ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            # Fallback for unhandled errors
            embed = discord.Embed(
                title="❌ Unknown Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @embed_commands.command(name="builder")
    async def embedbuilder(self, ctx, title: str = None, *, description: str = None):
        """Start the interactive embed builder."""
        if title is None and description is None:
            embed = discord.Embed(
                title="Embed Builder",
                description="Use buttons to customize me!",
                color=discord.Color.blue()
            )

            class BuilderView(View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.embed = embed

                async def update_message(self, interaction: discord.Interaction):
                    try:
                        await interaction.response.edit_message(embed=self.embed, view=self)
                    except discord.InteractionResponded:
                        await interaction.followup.edit_message(interaction.message.id, embed=self.embed, view=self)

                # Title Button
                @discord.ui.button(label="Set Title", style=discord.ButtonStyle.primary)
                async def title_button(self, interaction: discord.Interaction, button: Button):
                    class TitleModal(Modal):
                        def __init__(self, view):
                            super().__init__(title="Set Embed Title")
                            self.view = view
                            self.title_input = TextInput(label="Title", placeholder="Enter embed title", required=True)
                            self.add_item(self.title_input)

                        async def on_submit(self, modal_interaction: discord.Interaction):
                            self.view.embed.title = self.title_input.value
                            await self.view.update_message(modal_interaction)

                    await interaction.response.send_modal(TitleModal(self))

                # Description Button
                @discord.ui.button(label="Set Description", style=discord.ButtonStyle.primary)
                async def description_button(self, interaction: discord.Interaction, button: Button):
                    class DescriptionModal(Modal):
                        def __init__(self, view):
                            super().__init__(title="Set Embed Description")
                            self.view = view
                            self.desc_input = TextInput(
                                label="Description",
                                style=discord.TextStyle.paragraph,
                                placeholder="Enter description",
                                required=True
                            )
                            self.add_item(self.desc_input)

                        async def on_submit(self, modal_interaction: discord.Interaction):
                            self.view.embed.description = self.desc_input.value
                            await self.view.update_message(modal_interaction)

                    await interaction.response.send_modal(DescriptionModal(self))

                # Color Button
                @discord.ui.button(label="Set Color (Hex)", style=discord.ButtonStyle.primary)
                async def color_button(self, interaction: discord.Interaction, button: Button):
                    class ColorModal(Modal):
                        def __init__(self, view):
                            super().__init__(title="Set Embed Color")
                            self.view = view
                            self.color_input = TextInput(label="Hex Color", placeholder="#FF0000", required=True)
                            self.add_item(self.color_input)

                        async def on_submit(self, modal_interaction: discord.Interaction):
                            try:
                                self.view.embed.color = discord.Color(int(self.color_input.value.strip("#"), 16))
                            except ValueError:
                                await modal_interaction.response.send_message("Invalid hex color!", ephemeral=True)
                                return
                            await self.view.update_message(modal_interaction)

                    await interaction.response.send_modal(ColorModal(self))

                # Add Field Button
                @discord.ui.button(label="Add Field", style=discord.ButtonStyle.secondary)
                async def add_field_button(self, interaction: discord.Interaction, button: Button):
                    class FieldModal(Modal):
                        def __init__(self, view):
                            super().__init__(title="Add Embed Field")
                            self.view = view
                            self.name_input = TextInput(label="Field Name", required=True)
                            self.value_input = TextInput(label="Field Value", style=discord.TextStyle.paragraph, required=True)
                            self.inline_input = TextInput(label="Inline? (yes/no)", default="no", required=True)
                            self.add_item(self.name_input)
                            self.add_item(self.value_input)
                            self.add_item(self.inline_input)

                        async def on_submit(self, modal_interaction: discord.Interaction):
                            inline = self.inline_input.value.lower() in ["yes", "y", "true", "1"]
                            self.view.embed.add_field(name=self.name_input.value, value=self.value_input.value, inline=inline)
                            await self.view.update_message(modal_interaction)

                    await interaction.response.send_modal(FieldModal(self))

                # Remove Last Field Button
                @discord.ui.button(label="Remove Last Field", style=discord.ButtonStyle.secondary)
                async def remove_field_button(self, interaction: discord.Interaction, button: Button):
                    if self.embed.fields:
                        self.embed.remove_field(len(self.embed.fields) - 1)
                        await self.update_message(interaction)
                    else:
                        await interaction.response.send_message("No fields to remove!", ephemeral=True)

                # Send Embed Button
                @discord.ui.button(label="Send Embed", style=discord.ButtonStyle.success)
                async def send_button(self, interaction: discord.Interaction, button: Button):
                    await interaction.channel.send(embed=self.embed)
                    await interaction.message.delete()

                # Cancel Button
                @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
                async def cancel_button(self, interaction: discord.Interaction, button: Button):
                    embed = discord.Embed(description="Embed creation canceled successfully!", color=discord.Color.red())
                    try:
                        await interaction.response.edit_message(embed=embed, view=None)
                    except discord.InteractionResponded:
                        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)

            await ctx.send(embed=embed, view=BuilderView())
        else:
            embed = discord.Embed(title=title, description=description)
            await ctx.send(embed=embed)
            

    @embed_commands.command(name="info")
    async def embed_info(self, ctx, message: discord.Message = None):
        # Get the message from reply if not provided
        if message is None:
            if ctx.message.reference:
                message = ctx.message.reference.resolved
            else:
                await ctx.send("Please provide a message ID or reply to a message with an embed.")
                return

        if not message.embeds:
            await ctx.send("This message does not contain an embed.")
            return

        embed_obj = message.embeds[0]  # First embed

        # Create the info embed
        info_embed = discord.Embed(
            title="Embed Information",
            color=discord.Color.blurple(),
            timestamp=ctx.message.created_at
        )

        # Message info
        info_embed.add_field(name="Message Author", value=f"{message.author} ({message.author.id})", inline=False)
        info_embed.add_field(name="Message ID", value=message.id, inline=False)
        info_embed.add_field(name="Channel", value=f"{message.channel} ({message.channel.id})", inline=False)
        info_embed.add_field(name="Guild", value=f"{ctx.guild} ({ctx.guild.id})", inline=False)
        info_embed.add_field(name="Message Date", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        info_embed.add_field(name="Edited At", value=message.edited_at.strftime("%Y-%m-%d %H:%M:%S UTC") if message.edited_at else "Not Edited", inline=False)
        info_embed.add_field(name="Attachments", value=f"{len(message.attachments)} file(s)", inline=False)

        # Embed basic info
        info_embed.add_field(name="Embed Title", value=embed_obj.title or "None", inline=False)
        info_embed.add_field(name="Embed Description", value=embed_obj.description or "None", inline=False)
        info_embed.add_field(name="Embed Color", value=str(embed_obj.color) if embed_obj.color else "None", inline=False)
        info_embed.add_field(name="Embed URL", value=embed_obj.url or "None", inline=False)
        info_embed.add_field(name="Embed Type", value=embed_obj.type, inline=False)

        # Author
        if embed_obj.author.name:
            author_text = embed_obj.author.name
            if embed_obj.author.url:
                author_text += f" | [URL]({embed_obj.author.url})"
            info_embed.add_field(name="Embed Author", value=author_text, inline=False)

        # Footer
        if embed_obj.footer.text:
            footer_text = embed_obj.footer.text
            if embed_obj.footer.icon_url:
                footer_text += f" | [Icon URL]({embed_obj.footer.icon_url})"
            info_embed.add_field(name="Embed Footer", value=footer_text, inline=False)

        # Fields
        if embed_obj.fields:
            fields_text = ""
            for idx, field in enumerate(embed_obj.fields, start=1):
                fields_text += f"**{idx}. {field.name}**\n{field.value}\nInline: {field.inline}\n\n"
            info_embed.add_field(name=f"Fields ({len(embed_obj.fields)})", value=fields_text, inline=False)

        # Images, thumbnails, videos
        if embed_obj.image.url:
            info_embed.set_image(url=embed_obj.image.url)
        if embed_obj.thumbnail.url:
            info_embed.set_thumbnail(url=embed_obj.thumbnail.url)
        if embed_obj.video.url:
            info_embed.add_field(name="Video URL", value=embed_obj.video.url, inline=False)

        await ctx.send(embed=info_embed)

# This is a mandatory function to set up the cog.
# The bot will call this function to load the cog.
async def setup(bot):
    await bot.add_cog(Utility(bot))
