import argparse
import asyncio
import os
import time
import traceback

import aiohttp
import discord
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(override=True)

PORT = int(os.getenv("PORT", 28800))
PROXY = os.getenv("PROXY")
PROXY_AUTH = os.getenv("PROXY_AUTH")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_ACTIVITY_CACHE_DURATION = float(
    os.getenv("DISCORD_ACTIVITY_CACHE_DURATION", 30)
)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._recipient = None
        self._queried_activities = []
        self._last_query_time = float(0)
        self._activity_cache_duration = DISCORD_ACTIVITY_CACHE_DURATION

    async def on_ready(self):
        print(f"✅ Discord client Logged in as {self.user}")

    async def on_error(self, event_method, *args, **kwargs):
        print(f"❌ An error occurred in {event_method}: ", args, kwargs)

    async def on_message(self, message: discord.Message):
        print(f"📨 Message from {message.author}: {message.content}")

        if message.author != self.user:
            return

        if message.content == "ping":
            await message.channel.send("pong")

    @property
    def queried_activities(self):
        if time.time() - self._last_query_time < self._activity_cache_duration:
            print(
                f"ℹ️ Return cached activities for user {self._recipient}: {self._queried_activities}"
            )
            return self._queried_activities

        if self.is_ready() is False:
            print("❌ Discord client is not ready.")
            return []

        if self._recipient is None:
            channel = self.get_channel(int(DISCORD_CHANNEL_ID))
            if channel is not None:
                self._recipient = channel.recipient
                print(f"✅ Set recipient to {self._recipient}.")
            else:
                print(
                    f"❌ No Discord channel found for channel ID {DISCORD_CHANNEL_ID}."
                )
                return []

        recipientId = self._recipient.id
        if recipientId is None:
            print("❌ No recipient ID found.")
            return []

        relation = self.get_relationship(recipientId)
        if relation is not None:
            self._queried_activities = [
                activity.to_dict() for activity in relation.activities
            ]
            self._last_query_time = time.time()
            print(
                f"✅ Update activities for user {self._recipient}: {self._queried_activities}"
            )
        else:
            print(f"❌ No relationship found for user {self._recipient}.")
            return []

        return self._queried_activities

    @property
    def last_query_time(self):
        return int(self._last_query_time)


proxy = None
proxy_auth = None
if PROXY:
    proxy = PROXY
if PROXY_AUTH:
    user, pwd = PROXY_AUTH.split(":", 1)
    proxy_auth = aiohttp.BasicAuth(user, pwd)

client = MyClient(proxy=proxy, proxy_auth=proxy_auth)


async def start_discord_client():
    print("🚀 Starting Discord client...")
    if proxy:
        print(f"🔀 Proxy enabled: {proxy}")
    if proxy_auth:
        print("🔐 Proxy auth enabled.")
    try:
        if not DISCORD_TOKEN or not DISCORD_CHANNEL_ID:
            raise ValueError(
                "❌ `DISCORD_TOKEN` and `DISCORD_CHANNEL_ID` must be set in environment variables."
            )
        print(f"🔑 Discord client token present, prefix: {DISCORD_TOKEN[:8]}")
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        print("❌ Discord client failed to start:", type(e), e)
        traceback.print_exc()


async def lifespan(app: FastAPI):
    task = asyncio.create_task(start_discord_client())
    yield

    print("🛑 Shutting down...")
    if not client.is_closed():
        await client.close()
        print("🌙 Discord client connection was closed.")
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Server is running!"}


@app.get("/me")
def me():
    return {
        "client": "online" if client.is_ready() else "offline",
        "user": str(client.user) if client.user else None,
    }


@app.get("/activity")
def activity():
    return {
        "activities": client.queried_activities,
        "last_updated_at": client.last_query_time,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Discord Activity Sender")
    parser.add_argument(
        "--dev",
        "--reload",
        action="store_true",
        dest="dev",
        help="Enable auto-reload (development)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=PORT, help="Port to bind")
    args = parser.parse_args()

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.dev,
        log_level="debug" if args.dev else "info",
    )
