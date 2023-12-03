import time
from telethon import TelegramClient, types
from pystyle import Colorate, Colors, Col
import sys
from datetime import datetime
import random
import asyncio

# a = TelegramClient()
# a.send_message(parse_mode=)
# Constants
COLA = Col.light_blue
N4ME = "Telegram AutoPUB"
CONFIG_ACCOUNT_FILE = "config/account.txt"
CONFIG_CHANNELS_FILE = "config/channels.txt"
CONFIG_GROUPS_FILE = "config/groups.txt"
CONFIG_PUB_FILE = "config/pub.txt"
EMOJI_MAPPING = "config/emojis_mapping.txt"

# Banner display
def display_banner():
	banner = '''
		[Your ASCII Art Banner Here]
	'''
	print(Colorate.Vertical(Colors.cyan_to_blue, banner))

# Input prompt
def get_input(prompt=''):
	print(f"\n{COLA}╔{Col.reset} {Col.cyan}{N4ME}{Col.reset} {COLA}${Col.reset}")
	return input(f"{COLA}╚{Col.reset} root@root {COLA}>>{Col.reset} ")

# Configuration loading
def load_config():
	api_id, api_hash = None, None
	try:
		with open(CONFIG_ACCOUNT_FILE, "r") as file:
			lines = file.readlines()
			for line in lines:
				if '=' in line:
					splitted = line.split('=')
					if splitted[0] == 'api_id ':
						api_id = splitted[1]
					elif splitted[0] == 'api_hash ':
						api_hash = splitted[1]
					else:
						pass
		return api_id, api_hash
	except IOError:
		return None, None

# Channel retrieval
def get_channels(client):
	try:
		with open(CONFIG_CHANNELS_FILE, "a", encoding="utf8") as file:
			for dialog in client.iter_dialogs():
				if dialog.is_channel:
					link = construct_telegram_link(dialog)
					print_channel_group_info(dialog, link)
					file.write(f'{dialog.id} - {dialog.title} - {link}\n')
		return True
	except IOError:
		return False

# Group retrieval
async def get_groups(client):
	try:
		with open("config/groups.txt", "a", encoding="utf8") as file:
			async for dialog in client.iter_dialogs():
				if dialog.is_group:
					link = construct_telegram_link(dialog)
					print_channel_group_info(dialog, link)
					file.write(f'{dialog.id} - {dialog.title} - {link}\n')
		return True
	except IOError:
		return False

# Channel loading
def load_channels():
	try:
		channels = []
		with open(CONFIG_CHANNELS_FILE, "r", encoding='utf8') as file:
			lines = file.readlines()
			for line in lines:
				channels.append(line.split(' - ')[0].strip())
			return channels
	except IOError:
		return []

def load_groups():
	try:
		groups = []
		with open(CONFIG_GROUPS_FILE, "r", encoding='utf8') as file:
			lines = file.readlines()
			for line in lines:
				groups.append(line.split(' - ')[0].strip())
			return groups
	except IOError:
		return []

# Message retrieval
def get_message():
	try:
		with open(CONFIG_PUB_FILE, "r", encoding="utf8") as file:
			return file.read()
	except IOError:
		return ""

# Publication function
async def publish(message, client, entities, total_time):

	n = len(entities)
	if n == 0:
		return

	# Constants for Rate Limiting
	MAX_MESSAGES_PER_MINUTE = 10  # Adjust as needed
	RATE_LIMIT_DELAY = 60  # Delay in seconds when rate limit is hit

	# Calculate average delay based on total time and number of entities
	average_delay = total_time / n

	# Widen the delay range for more variation
	min_delay = 0.1  # Min delay is 10% of the average
	max_delay = 1.9  # Max delay is 190% of the average

	while True:
		await asyncio.sleep(5)
		start_time = time.time()
		good, bad = 0, 0
		for channel in entities:
			elapsed_time = time.time() - start_time
			remaining_time = max(total_time - elapsed_time, 0)
			entities_left = n - good - bad
			average_delay = remaining_time / entities_left
			delay = random.uniform(average_delay * min_delay, average_delay * max_delay)

			if good > 0 and (good / (elapsed_time / 60)) > MAX_MESSAGES_PER_MINUTE:
				await asyncio.sleep(RATE_LIMIT_DELAY)

			try:
				entity = await client.get_entity(int(channel))
				name = entity.username if hasattr(entity, 'username') and entity.username else f"[{getattr(entity, 'title', 'ID: ' + channel)}]"
				formatting_entities = find_emojis(message, load_emoji_mappings(EMOJI_MAPPING))
				await client.send_message(entity=entity, message=message, formatting_entities=formatting_entities)
				good += 1
			except Exception as e:
				print(e)
				bad += 1
			print_status(good, n, name)

			# Wait for a random time within the new range
			if entities_left > 1:
				await asyncio.sleep(delay)

# Print status
def print_status(good, total, channel):
	now = datetime.now().strftime("%H:%M:%S")
	print(f"[{Col.cyan}{now}{Col.reset}] {COLA}[{Col.reset}*{COLA}]{Col.reset} Sending to {channel} Sent: {Col.cyan}{good}{Col.reset}/{total}{COLA}.{Col.reset}")

# Time conversion
def convert_time(time_str):
	units = {'s': 1, 'm': 60, 'h': 3600}
	try:
		seconds = sum(int(part[:-1]) * units.get(part[-1], 0) for part in time_str.split() if part[:-1].isdigit() and part[-1] in units)
		return seconds
	except ValueError:
		raise ValueError("Time format error. Please use the format like '2h30m' or '45s'.")


# Main execution
async def main():
	display_banner()
	api_id, api_hash = load_config()

	if not api_id:
		print_error("Edit config/account.txt with your API information.")
		return

	client = TelegramClient('session_name', api_id, api_hash)
	await client.start()

	while True:
		command = get_input()

		if command == ".exit":
			break
		elif command == ".message":
			handle_message_command()
		elif command == ".account":
			handle_account_command(api_id, api_hash)
		elif command == '.channels':
			await handle_channels_command(client)
		elif command == '.groups':
			await handle_groups_command(client)
		elif command.startswith(".pub "):
			await handle_publish_command(command, client)
		elif command == ".help":
			display_help()

def print_error(message):
	print(f"\n{COLA}╔{Col.reset} {Col.cyan}{N4ME}{Col.reset} {COLA}${Col.reset}")
	print(f"{COLA}╚{Col.reset} {message}{COLA}.{Col.reset}")

def handle_message_command():
	message = get_message()
	if not message:
		print_error("Could not open config/pub.txt to get Message")
	else:
		print(f"\n{COLA}[{Col.reset}*{COLA}]{Col.reset} Saved Message: \n{message}")

def handle_account_command(api_id, api_hash):
	print(f"\n{COLA}[{Col.reset}*{COLA}]{Col.reset} Saved Account:")
	print(f"   API ID -> {api_id}")
	print(f"   API HASH -> {api_hash}")

def handle_channels_command(client):
	if not get_channels(client):
		print_error("Could not open config/channels.txt to get User Channels")

async def handle_groups_command(client):
	if not await get_groups(client):
		print_error("Could not open config/channels.txt to get User Channels")

async def handle_publish_command(command, client):
	parts = command.split(" ")
	if len(parts) != 3:
		print_error("Invalid command format. Usage: .pub [target] [total_time]")
		return

	target_type = parts[1]
	total_time = convert_time(parts[2])

	entities = load_channels() if target_type == 'channels' else load_groups()

	if not entities:
		print_error(f"Could not open config/{target_type}.txt to get IDs")
		return

	message = get_message()
	if not message:
		print_error("Could not open config/pub.txt to get Message")
		return

	print(f"\n{COLA}╔{Col.reset} {Col.cyan}{N4ME}{Col.reset} {COLA}${Col.reset}")
	print(f"{COLA}║{Col.reset} Bot is ready. Target: {target_type.capitalize()} | Entities: {len(entities)} | Total Time: {total_time}s")
	print(f"{COLA}╚{Col.reset} Press Enter to start{COLA}.{Col.reset} \n")
	input()

	await publish(message, client, entities, total_time)

# Construct Telegram link
def construct_telegram_link(dialog):
	try:
		if hasattr(dialog.entity, 'username') and dialog.entity.username:
			return f'https://t.me/{dialog.entity.username}'
		else:
			# For private groups/channels without a username, use access_hash if available
			if hasattr(dialog.entity, 'access_hash'):
				return f'https://t.me/joinchat/{dialog.entity.access_hash}'
			else:
				return "No link available"
	except AttributeError:
		return "No link available"

def print_channel_group_info(dialog, link):
	print(f"{COLA}[{Col.reset}+{COLA}]{Col.reset} ID: {Col.cyan}{dialog.id}{Col.reset} Name: {Col.light_blue}{dialog.title}{Col.reset} Link: {Col.yellow}{link}{Col.reset}")

def load_emoji_mappings(file_path):
	"""Loads emoji mappings from a file and returns a dictionary."""
	emoji_dict = {}
	with open(file_path, 'r', encoding='utf-8') as file:
		for line in file:
			parts = line.strip().replace('\t', '').split(',')
			if len(parts) == 2 and parts[1].strip().replace('\t', '').isdigit():
				emoji, doc_id = parts[0].strip(), int(parts[1].strip())
				emoji_dict[emoji] = doc_id
	return emoji_dict

def find_emojis(message, emoji_dict):
	"""Finds emojis in the message and returns a list of custom emoji entities."""
	entities = []
	for emoji, doc_id in emoji_dict.items():
		start = 0
		while start < len(message):
			pos = message.find(emoji, start)
			if pos == -1:
				break
			entity = types.MessageEntityCustomEmoji(offset=pos, length=len(emoji), document_id=doc_id)
			entities.append(entity)
			emoji_substr = message[pos:pos+len(emoji)]
			start = pos + len(emoji)
	return entities

def display_help():
	print('''
	HELP COMMANDS
	-------------

	.message    | see saved message
	.account    | see saved account
	.channels   | load channels and save them
	.groups		| load groups and save them
	.pub <time> | start the bot with a delay, example: .pub 2h
	''')


if __name__ == "__main__":
	asyncio.run(main())
