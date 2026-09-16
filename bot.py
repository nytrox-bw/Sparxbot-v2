import os
import base64
import io
import asyncio
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from the environment.")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from the environment.")

SYSTEM_PROMPT = """You are Sparxbot V2, a maths and science study assistant.
Solve the user's question accurately and clearly. If an image is supplied, read the question from the image first.
For maths, give the final answer prominently and show concise working so the user can verify it.
For science, identify the answer and explain the key reasoning briefly.
If the image is unclear, say exactly what part cannot be read instead of guessing.
Do not claim to have interacted with Sparx, submitted homework, changed bookwork codes, bypassed school controls, or hidden activity.
Do not provide advice for evading school detection or academic-integrity systems.
"""

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def ask_gemini(prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/png") -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    parts = [{"text": f"{SYSTEM_PROMPT}\n\nUser request:\n{prompt}"}]
    if image_bytes:
        parts.append(
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(image_bytes).decode("ascii"),
                }
            }
        )

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0.15,
            "maxOutputTokens": 1200,
        },
    }

    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            if response.status >= 400:
                message = data.get("error", {}).get("message", "Gemini API request failed")
                raise RuntimeError(message)

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("The AI returned an empty or unexpected response.")


def trim_discord(text: str, limit: int = 1900) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def send_result(interaction: discord.Interaction, result: str):
    chunks = trim_discord(result)
    await interaction.followup.send(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash commands.")
    except Exception as exc:
        print(f"Command sync failed: {exc}")


@bot.tree.command(name="solve", description="Solve a maths or science question.")
@app_commands.describe(question="Type the question you want solved")
async def solve(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    try:
        result = await ask_gemini(question)
        await send_result(interaction, result)
    except Exception as exc:
        await interaction.followup.send(f"I couldn't solve that right now: `{exc}`")


@bot.tree.command(name="solve-image", description="Solve a maths or science question from an image.")
@app_commands.describe(image="Attach a clear screenshot/photo of the question", instructions="Optional extra instructions")
async def solve_image(
    interaction: discord.Interaction,
    image: discord.Attachment,
    instructions: Optional[str] = None,
):
    await interaction.response.defer(thinking=True)

    allowed = {"image/png", "image/jpeg", "image/webp"}
    if image.content_type not in allowed:
        await interaction.followup.send("Please attach a PNG, JPEG, or WebP image.")
        return
    if image.size > 8 * 1024 * 1024:
        await interaction.followup.send("That image is over 8 MB. Please upload a smaller screenshot.")
        return

    try:
        image_bytes = await image.read()
        prompt = instructions or "Solve the question shown in the image. Give the final answer and concise working."
        result = await ask_gemini(prompt, image_bytes=image_bytes, mime_type=image.content_type)
        await send_result(interaction, result)
    except Exception as exc:
        await interaction.followup.send(f"I couldn't read/solve that image: `{exc}`")


@bot.tree.command(name="ping", description="Check whether Sparxbot V2 is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)} ms")


bot.run(DISCORD_TOKEN)
