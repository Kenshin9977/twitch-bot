import os

import requests
import twitchio
from dotenv import load_dotenv
from twitchio.ext import pubsub

load_dotenv()

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
TWITCH_REWARD_ID = os.getenv("TWITCH_REWARD_ID")


headers = {
    'Authorization': f'Bearer {TWITCH_TOKEN}',
    'Client-Id': TWITCH_CLIENT_ID
}

my_token = TWITCH_TOKEN
broadcaster_id = 28370428
client = twitchio.Client(token=TWITCH_TOKEN)
client.pubsub = pubsub.PubSubPool(client)


@client.event()
async def event_pubsub_channel_points(
    event: pubsub.PubSubChannelPointsMessage
):
    if event.reward.id == TWITCH_REWARD_ID:
        user_to_timeout = event.input
        print(f'Reward triggered by {event.user.name}')
        await check_and_timeout_user(user_to_timeout)


async def check_and_timeout_user(user_to_timeout):
    broadcaster = client.create_user(
        broadcaster_id,
        TWITCH_CHANNEL
    )
    moderators = await broadcaster.fetch_moderators(token=TWITCH_TOKEN)
    if user_to_timeout in [mod.name for mod in moderators]:
        print(f'{user_to_timeout} is a moderator and will not be timed out.')
    else:
        url = f'https://api.twitch.tv/helix/users?login={user_to_timeout}'
        response = requests.get(url, headers=headers)
        if not response or response.status_code != 200:
            print(response.status_code)
            return
        data = response.json().get("data")
        if not data:
            print(f"{user_to_timeout} doesn't exist")
            return
        user_to_timeout_id = data[0].get("id")
        print(f'Timing out {user_to_timeout}.')
        try:
            await broadcaster.timeout_user(
                token=TWITCH_TOKEN,
                user_id=user_to_timeout_id,
                moderator_id=broadcaster_id,
                reason="",
                duration=30
            )
        except twitchio.errors.HTTPException:
            print("Can't ban the broadcaster.")


async def main():
    topics = [
        pubsub.channel_points(TWITCH_TOKEN)[broadcaster_id],
    ]
    await client.pubsub.subscribe_topics(topics)
    await client.start()

client.loop.run_until_complete(main())
