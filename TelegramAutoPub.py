import json
import re
import time
import random
import asyncio
from telethon import TelegramClient, types
from telethon.tl.functions.channels import JoinChannelRequest

class Spammer:
	MAX_MESSAGES_PER_MINUTE = 30
	LOOP_DELAY = 720
	RATE_LIMIT_DELAY = 60

	MIN_DELAY = 0.1 # Min delay is 10% of the average
	MAX_DELAY = 1.9 # Max delay is 190% of the average

	HELP_MESSAGE = '''
	HELP COMMANDS
	_____________
	.channels	| load channels and save them
	.groups		| load groups and save them
	.pub		| start the bot
	.reload		| reload the config
	.help		| show this message 
	.exit		| exit the program		
	'''

	
	@classmethod
	async def init(self, config_path):
		instance = self()
		await instance._async_init(config_path)
		return instance
	
	async def _async_init(self, config_path):
		self.config_path = config_path
		await self._load_config(config_path)
		print(self.config)
		self.client = TelegramClient(self.config['phone'], api_id=self.config['api_id'], api_hash=self.config['api_hash'])
		await self.client.start()
		await self._load_messages()

		# await self.client.connect()
		# if not await self.client.is_user_authorized():
		# 	await self.client.send_code_request(self.config['phone'])
		# 	await self.client.sign_in(self.config['phone'], code=input('Enter  veryfication code: '), password=input('Enter password : '))

	async def _load_config(self, config_path):
		self.config = []
		with open(config_path, 'r') as f:
			self.config = json.load(f)

	
	async def _load_groups(self):
		try:
			groups = []
			with open(self.config['groups_path'], 'r', encoding='utf8') as f:
				lines = f.readlines()
				for line in lines:
					line = line.split(' - ')[0].strip()
					try:
						entity = await self.client.get_entity(int(line))
					except Exception as e:
						self._logger(f"Could not load {line} : {e}")
					groups.append(entity)
				return groups
		except:
			return []
		
	async def _load_channels(self):
		try:
			channels = []
			with open(self.config['groups_path'], 'r', encoding='utf8') as f:
				lines = f.readlines()
				for line in lines:
					channels.append(line.split(' - ')[0].strip())
				return channels
		except:
			return []
		
	
	async def _get_groups(self):
		try:
			with open(self.config['groups_path'], 'a', encoding='utf8') as f:
				async for dialog in self.client.iter_dialogs():
					if dialog.is_group:
						link = self.construct_telegram_link(dialog)
						f.write(f'{dialog.id} - {dialog.title} - {link}\n')
						self._logger(f"Found Group : {dialog.id} - {dialog.title} - {link}")
			return True
		except:
			return False

	async def _get_channels(self):
		try:
			with open(self.config['channels_path'], 'a', encoding='utf8') as f:
				async for dialog in self.client.iter_dialogs():
					if dialog.is_channel:
						link = self.construct_telegram_link(dialog)
						f.write(f"{dialog.id} - {dialog.title} - {link}\n")
						self._logger(f"Found Channel : {dialog.id} - {dialog.title} - {link}")
			return True
		except Exception as e:
			print(e)
			return False


	async def _load_messages(self):
		self.messages = []
		with open(self.config['messages_path'], 'r', encoding='utf8') as f:
			links = f.readlines()
			for link in links:
				chat_id, message_id = await self._extract_from_url(link.strip())
				message = await self.client.get_messages(chat_id, ids=message_id)
				self.messages.append(message)
	
	async def _get_message(self):
		return random.choice(self.messages)
		
	async def _publish(self, entities):
		self._load_messages()
		if not entities:
			return False
		n = len(entities)
		total_time = n / self.MAX_MESSAGES_PER_MINUTE 
		average_delay = total_time / n
		good, bad = 0, 0
		start_time = time.time()
		for entity in entities:
			message = await self._get_message()
			elapsed_time = time.time() - start_time
			remaining_time = total_time - elapsed_time
			entities_left = n - good - bad
			average_delay = remaining_time / entities_left
			delay = random.uniform(average_delay * self.MIN_DELAY, average_delay * self.MAX_DELAY)
			if good > 0 and (good / (elapsed_time / 60)) > self.MAX_MESSAGES_PER_MINUTE:
				await asyncio.sleep(self.RATE_LIMIT_DELAY)
				remaining_time += self.RATE_LIMIT_DELAY
			try:
				if self.config['forward_header']:
					await self.client.forward_messages(entity, message)
				else:
					await self.client.send_message(entity, message)
				good += 1
				self._logger(f"{remaining_time:.2f}s - Message sent to {entity.id} - [{good}:{bad}]")
			except Exception as e:
				bad += 1
				print(e)
				self._logger(f"{elapsed_time:.2f} - Failed to send message to {entity.id} - [{good}:{bad}]")


			if entities_left > 1:
				await asyncio.sleep(delay)
		return good, bad
	
	async def _handle_publish_command(self, command):
		parts = command.split(" ")
		if len(parts) != 2:
			print(f"Usage : .pub <groups/channels>")
			return
		try:
			target_type = parts[1]
		except:
			print(f"Unknown command. Usage : .pub <groups/channels>")
			return

		entities = await self._load_channels() if target_type == 'channels' else await self._load_groups()
		self._logger(f"Starting the bot.\nSending {len(self.messages)} messages to {len(entities)} {target_type}.")
		input("Press Enter to start.")
		while True:
			try:
				await self._publish(entities)
				await asyncio.sleep(self.LOOP_DELAY)
			except:
				break

	
	def _logger(self, command):
		print(command)


	async def run(self):
		while True:
			command = input(f">> ")
			if command == ".exit":
				break
			elif command == ".channels":
				await self._get_channels()
			elif command == ".groups":
				await self._get_groups()
			elif ".pub" in command:
				await self._handle_publish_command(command)
			elif command == ".reload":
				self._logger(f"Reloading config.")
				await self._load_config(self.config_path)
				await self._load_messages()
			elif command == ".help" or command == "help":
				print(self.HELP_MESSAGE)

	

	async def _extract_from_url(self, url):
		match = re.match(r'https://t\.me/(?:c/)?(\d+|[a-zA-Z0-9_]+)/(\d+)', url)
		
		if match:
			chat_id = match.group(1)
			message_id = int(match.group(2))
			return chat_id, message_id
		else:
			print("URL does not match the expected Telegram message pattern.")
			return None, None
	
	@staticmethod
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
		


async def main():
	spammer = await Spammer.init('./config/config.json')
	await spammer.run()

if __name__ == '__main__':
	asyncio.run(main())