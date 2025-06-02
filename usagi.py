# -*- coding: utf-8 -*-

import os
import discord
from discord.ext import commands
from discord import ui
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- VC名変更モーダル ---
class VCNameModal(ui.Modal, title="VC名の変更"):
    new_name = ui.TextInput(label="新しいVC名", max_length=30, placeholder="ここに新しいVC名を入力してね")

    def __init__(self, voice_channel):
        super().__init__()
        self.voice_channel = voice_channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.voice_channel.edit(name=self.new_name.value)
            await interaction.response.send_message(f"VC名を「{self.new_name.value}」にしたよ！", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"VC名変更に失敗しちゃった、ごめんね: {e}", ephemeral=True)

# --- VC参加者切断セレクト＆ビュー ---
class KickMemberSelect(ui.Select):
    def __init__(self, voice_channel, author):
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in voice_channel.members if member.id != author.id
        ]
        super().__init__(
            placeholder="誰とばいばいする？",
            options=options,
            min_values=1, max_values=1
        )
        self.voice_channel = voice_channel

    async def callback(self, interaction: discord.Interaction):
        member_id = int(self.values[0])
        member = self.voice_channel.guild.get_member(member_id)
        try:
            await member.move_to(None)
            await interaction.response.send_message(f"{member.display_name}さん、またね！", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"しっぱいしちゃった、ごめんね: {e}", ephemeral=True)

class KickMemberView(ui.View):
    def __init__(self, voice_channel, author):
        super().__init__(timeout=60)
        # 切断可能なユーザーがいなければセレクト追加しない
        if any(member.id != author.id for member in voice_channel.members):
            self.add_item(KickMemberSelect(voice_channel, author))

# --- 参加上限変更モーダル ---
class UserLimitModal(ui.Modal, title="VC参加上限の変更"):
    user_limit = ui.TextInput(
        label="上限人数 (0で無制限)",
        style=discord.TextStyle.short,
        placeholder="0～99",
        required=True,
        max_length=2,
    )
    def __init__(self, voice_channel):
        super().__init__()
        self.voice_channel = voice_channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(self.user_limit.value)
            user_limit = None if value == 0 else min(max(value, 0), 99)
            await self.voice_channel.edit(user_limit=user_limit)
            await interaction.response.send_message(f"VC上限を{'無制限' if user_limit is None else str(user_limit)+'人'}にしたよ", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"人数変更にしっぱいしちゃった: {e}", ephemeral=True)

# --- チャンネルステータス（トピック）変更モーダル ---
class ChannelTopicModal(ui.Modal, title="チャンネルステータス変更"):
    topic = ui.TextInput(
        label="新しいチャンネルステータス",
        style=discord.TextStyle.short,
        placeholder="げむざつ",
        required=True,
        max_length=100,
    )
    def __init__(self, voice_channel):
        super().__init__()
        self.voice_channel = voice_channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.voice_channel.edit(topic=self.topic.value)
            await interaction.response.send_message("チャンネルステータスを変更したよ", ephemeral=True)
        except Exception as e:
            if "50035" in str(e):
                await interaction.response.send_message(
                    "禁止ワードが含まれているかも！内容を変えて試してみてね",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(f"変更に失敗しちゃった: {e}", ephemeral=True)

# --- すべての機能ボタンをまとめたView ---
class MultiActionView(ui.View):
    def __init__(self, vc_channel, member):
        super().__init__(timeout=60)
        self.vc_channel = vc_channel
        self.member = member

    @ui.button(label="VC名を変更", style=discord.ButtonStyle.primary)
    async def change_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("呼んでくれた人だけ使えるよ！", ephemeral=True)
            return
        await interaction.response.send_modal(VCNameModal(self.vc_channel))

    @ui.button(label="誰かをVCから切断", style=discord.ButtonStyle.danger)
    async def kick_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("呼んでくれた人だけ使えるよ！", ephemeral=True)
            return
        view = KickMemberView(self.vc_channel, self.member)
        if len(view.children) == 0:
            await interaction.response.send_message("ばいばいできる他のユーザーがいないよ。", ephemeral=True)
        else:
            await interaction.response.send_message("ばいばいするユーザーを選んでね", view=view, ephemeral=True)

    @ui.button(label="参加上限を変更", style=discord.ButtonStyle.secondary)
    async def change_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("呼んでくれた人だけ使えるよ！", ephemeral=True)
            return
        await interaction.response.send_modal(UserLimitModal(self.vc_channel))

    @ui.button(label="チャンネルステータス変更", style=discord.ButtonStyle.success)
    async def change_topic(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.member.id:
            await interaction.response.send_message("呼んでくれた人だけ使えるよ！", ephemeral=True)
            return
        await interaction.response.send_modal(ChannelTopicModal(self.vc_channel))

# --- on_messageで「うさぎちゃん」検知&VCチェック ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if "うさぎちゃん" in message.content:
        member = message.author

        # VC参加状況確認
        if not isinstance(member, discord.Member):
            member = await message.guild.fetch_member(member.id)
        voice_state = member.voice

        if not voice_state or not voice_state.channel:
            await message.channel.send("VCに参加しているときだけ使えるよ")
            return

        vc_channel = voice_state.channel

        view = MultiActionView(vc_channel, member)
        await message.channel.send(
            f"{member.mention} はーい！したいことを教えて！",
            view=view
        )
    await bot.process_commands(message)

bot.run(TOKEN)
