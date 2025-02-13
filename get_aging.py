import discord
import psycopg2
import uuid
import re
from datetime import datetime, timezone

DB_USER = "postgres"
DB_PASSWORD = "password"
# Discord Configuration
TOKEN = "XXXXXXXXXXXXXX"
CHANNEL_ID = "XXXXXXXXXXXXXX" #aging

# PostgreSQL Configuration
DB_NAME = "discord_db"
DB_HOST = "localhost"
DB_PORT = "5432"
TABLE_NAME = "aging_table"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

# Database Setup Function
def setup_database():
  print("🚀 Running setup_database()...")

  try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
      user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Create the database if it does not exist
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'")
    if not cur.fetchone():
      cur.execute(f"CREATE DATABASE {DB_NAME}")
      print(f"✅ Database {DB_NAME} created successfully.")

    cur.close()
    conn.close()

    # Connect to the newly created database
    conn = psycopg2.connect(
      dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    # Create the table if it does not exist
    cur.execute(f"""
      CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        message_id UUID PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        level INT NOT NULL
        )
    """)
    conn.commit()
    print(f"✅ Table {TABLE_NAME} is ready.")

    cur.close()
    conn.close()

  except Exception as e:
    print(f"❌ Error during database setup: {e}")

# Insert or update messages in the database
def upsert_message(message, username, level):
  try:
    message_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, username))  # Convert UUID to str
    timestamp = message.created_at.replace(tzinfo=timezone.utc)

    conn = psycopg2.connect(
      dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    # Insert or update the record
    cur.execute(f"""
      INSERT INTO {TABLE_NAME} (message_id, username, timestamp, level)
      VALUES (%s, %s, %s, %s)
      ON CONFLICT (message_id)
      DO UPDATE SET timestamp = EXCLUDED.timestamp, level = EXCLUDED.level;
    """, (message_id, username, timestamp, level))

    conn.commit()
    cur.close()
    conn.close()
    print(f"📊 {timestamp} | User {username} reached level {level} | Message ID: {message_id}")

  except Exception as e:
    print(f"❌ Error during upsert operation: {e}")

async def process_message(message):
  # Check if the message contains a mention
  if message.mentions:
    mentioned_user = message.mentions[0]  # Get the first mentioned user
    username = mentioned_user.display_name  # Get their display name

    # Extract the level using regex
    match = re.search(r"has reached level \*\*(\d+)\*\*", message.content)
    if match:
      level = int(match.group(1))
      upsert_message(message, username, level)


@client.event
async def on_message(message):
  if message.channel.id == CHANNEL_ID:
    await process_message(message)

@client.event
async def on_ready():
  print(f"✅ Bot is connected as {client.user}")

  try:
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
      channel = await client.fetch_channel(CHANNEL_ID)

    print(f"📩 Fetching message history from {channel.name}...")

    async for message in channel.history(limit=None, oldest_first=True):
      await process_message(message)

  except discord.errors.NotFound:
    print(f"❌ The channel with ID {CHANNEL_ID} was not found.")
  except discord.errors.Forbidden:
    print(f"❌ Access to the channel with ID {CHANNEL_ID} is denied.")
  except discord.errors.HTTPException as e:
    print(f"❌ An HTTP error occurred: {e}")

setup_database()
client.run(TOKEN)

