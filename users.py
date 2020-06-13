'''Fake user'''

import os
import random
import json
from string import ascii_letters as LETTERS

import requests

##############################

HEADERS = {
	'Content-Type': "application/json",
	'Cache-Control': "no-cache"
}
BOT_HOOK = os.getenv('BOT_HOOK')

requests.packages.urllib3.disable_warnings()

##############################


class User():
	'''Randomly generated user-like requests'''

	def __init__(self, user_id, actions_iter):
		self.user_id = user_id
		self.username = ''.join(random.choice(LETTERS) for _ in range(8))
		self.actions = actions_iter

	def message(self, text):
		return {
			'update_id': 0,
			'message': {
				'date': 0,
				'chat': {
					'id': self.user_id,
					'type': "private"
				},
				'message_id': 0,
				'from': {
					'id': self.user_id,
					'username': self.username,
					'first_name': "test_user",
					'is_bot': False
				},
				'text': text
			}
		}

	def button(self, text):
		return {
			'update_id': 0,
			'callback_query': {
				'id': 0,
				'from': {
					'id': self.user_id,
					'username': self.username,
					'first_name': "test_user",
					'is_bot': False
				},
				'chat_instance': "test",
				'inline_message_id': 0,
				'message': {
					'message_id': 0,
					'date': 0,
					'chat': {
						'id': self.user_id,
						'type': "private"
					}
				},
				'data': text
			}
		}

	def next_action(self):
		try:
			method, data = next(self.actions)
		except StopIteration:
			return False
		if callable(data):
			data = data(self)
		payload = getattr(self, method)(data)
		requests.post(
			BOT_HOOK, headers=HEADERS,
			verify=False, data=json.dumps(payload)
		)
		return True


class UsersCollection():
	'''Generates and holds random users'''

	def __init__(self, *, how_many, actions):
		self.users = {}
		for _ in range(how_many):
			user_id = random.randint(10000000, 99999999)
			self.users[user_id] = User(user_id, iter(actions))

	def __contains__(self, user_id):
		return user_id in self.users

	def __getitem__(self, user_id):
		return self.users.get(user_id, None)

	def __delitem__(self, user_id):
		del self.users[user_id]

	@property
	def is_empty(self):
		return not self.users

	def start_actions(self):
		for user in self.users.values():
			user.next_action()
