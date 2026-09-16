import os
import base64
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
MAX_IMAGE_BYTES = 8 * 1024 * 1024

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from the environment.")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from the environment.")

SYSTEM_PROMPT = """You are Sparxbot V2, a maths and science study assistant.
Solve the user's question accurately and clearly. If an image is supplied, read the question from the image first.
For maths, give the final answer prominently and show concise working so the user can verify it.
For science, give the answer and briefly explain the key scientific reasoning.
Preserve units, significant figures, signs, fractions, and exact forms when appropriate.
If an image is unclear, say exactly what cannot be read instead of guessing.
Never claim to have interacted with Sparx, submitted homework, changed bookwork codes, or hidden activity.
Do not provide advice for evading school detection or academic-integrity systems.
"""

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


async def ask_gemini(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
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
            "maxOutputTokens": 1400,
        },
    }

    timeout = aiohttp.ClientTimeout(total=60)
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
    """Split a response into Discord-safe chunks without exceeding the limit."""
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        cut = text.rfind("\n", 0, limit)
        if cut < 500:
            cut = text.rfind(" ", 0, limit)
        if cut < 500:
            cut = limit

        chunks.append(text[:cut])
        text = text[cut:].lstrip()

    return chunks


async def send_result(interaction: discord.Interaction, result: str) -> None:
    chunks = trim_discord(result)
    await interaction.followup.send(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


async def solve_request(
    interaction: discord.Interaction,
    question: str,
    image: Optional[discord.Attachment] = None,
) -> None:
    image_bytes = None
    mime_type = "image/png"

    if image:
        if image.size > MAX_IMAGE_BYTES:
            await interaction.followup.send("That image is over 8 MB. Please upload a smaller screenshot.")
            return

        mime_type = image.content_type or "image/png"
        if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
            await interaction.followup.send("Please attach a PNG, JPEG, or WebP image.")
            return

        image_bytes = await image.read()

    try:
        result = await ask_gemini(question, image_bytes=image_bytes, mime_type=mime_type)
        await send_result(interaction, result)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"Solver error: {type(exc).__name__}: {exc}")
        await interaction.followup.send("I couldn't solve that right now. Check the bot/API setup and try again.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash commands.")
    except Exception as exc:
        print(f"Command sync failed: {exc}")


@bot.tree.command(name="solve", description="Solve a maths or science question, optionally from a screenshot.")
@app_commands.describe(
    question="Type the question, or tell the bot what to look for in the screenshot",
    image="Optional screenshot/photo of the question",
)
async def solve(
    interaction: discord.Interaction,
    question: str,
    image: Optional[discord.Attachment] = None,
):
    await interaction.response.defer(thinking=True)
    await solve_request(interaction, question, image)


@bot.tree.command(name="solve-image", description="Solve a maths or science question from a screenshot.")
@app_commands.describe(
    image="Attach a clear PNG, JPEG, or WebP screenshot/photo",
    instructions="Optional instructions, e.g. 'give just the answer' or 'show working'",
)
async def solve_image(
    interaction: discord.Interaction,
    image: discord.Attachment,
    instructions: Optional[str] = None,
):
    await interaction.response.defer(thinking=True)
    prompt = instructions or "Read the question in the screenshot and solve it. Give the final answer and concise working."
    await solve_request(interaction, prompt, image)


@bot.tree.command(name="ping", description="Check whether Sparxbot V2 is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)} ms")


@bot.tree.command(name="about", description="Show what Sparxbot V2 can do.")
async def about(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Sparxbot V2**\n"
        "• `/solve` — typed question, with optional screenshot\n"
        "• `/solve-image` — screenshot-first solving\n"
        "• `/ping` — latency check\n\n"
        "Built as a Discord-based maths/science study assistant."
    )


bot.run(DISCORD_TOKEN)
