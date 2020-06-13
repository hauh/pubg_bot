'''Fake user'''

import random
import string
import json

import requests

from config import debug_chat_id, bot_hook as BOT_HOOK

##############################

HEADERS = {
	'Content-Type': "application/json",
	'Cache-Control': "no-cache"
}
DEBUG_CHAT = {'id': debug_chat_id, 'type': "private"}

requests.packages.urllib3.disable_warnings()

##############################


class User():
	'''Randomly generated user-like requests'''

	def __init__(self):
		self.user = {
			'id': random.randint(1000000, 9999999),
			'username': ''.join(random.choice(string.ascii_letters) for _ in range(8)),
			'first_name': "test_user",
			'is_bot': False
		}
		self.answer = {
			'update_id': 0,
			'callback_query': {
				'id': 0,
				'from': self.user,
				'chat_instance': "test",
				'inline_message_id': 0,
				'message': {
					'message_id': 0,
					'date': 0,
					'chat': DEBUG_CHAT
				}
			}
		}
		self.message = {
			'update_id': 0,
			'message': {
				'date': 0,
				'chat': DEBUG_CHAT,
				'message_id': 0,
				'from': self.user,
			}
		}

	def send_message(self, text):
		self.message['message']['text'] = text
		requests.post(
			BOT_HOOK, headers=HEADERS, verify=False,
			data=json.dumps(self.message)
		)

	def answer_callback_query(self, text):
		self.answer['callback_query']['data'] = text
		requests.post(
			BOT_HOOK, headers=HEADERS, verify=False,
			data=json.dumps(self.answer)
		)

	def back(self):
		self.answer_callback_query("_back_")

	def start(self):
		self.send_message("/start")

	def profile(self):
		self.answer_callback_query("profile")

	def set_pubg_id(self):
		self.answer_callback_query("set_pubg_id")
		self.send_message(str(self.user['id']))
		self.answer_callback_query(f"_confirm_{self.user['id']}")

	def set_pubg_username(self):
		self.answer_callback_query("set_pubg_username")
		self.send_message(self.user['username'])
		self.answer_callback_query(f"_confirm_{self.user['username']}")
