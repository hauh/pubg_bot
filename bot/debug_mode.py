'''Monkey patching bot instance to redirect requests to debug chat'''

# pylint: disable=protected-access

import json

import requests

import database as db
from config import debug_server as DEBUG_SERVER, debug_chat as DEBUG_CHAT

##############################


class TelegramRequestWrapper():
	'''Redirects requests to debug chat and sends copies to debug server'''

	def __init__(self, original_request_handler, admins):
		self.saved_handler = original_request_handler
		self.admins = admins

	def __getattr__(self, attr):
		return getattr(self.saved_handler, attr)

	def post(self, url, data, timeout=None):
		copy = dict(method=url.split('/')[-1], chat_id=data['chat_id'])
		if int(data['chat_id']) not in self.admins:
			data['chat_id'] = DEBUG_CHAT
		result = self.saved_handler.post(url, data, timeout)
		copy.update(result=result)
		self.to_debug(copy)
		return result

	def get(self, url, timeout=None):
		result = self.saved_handler.get(url, timeout)
		self.to_debug(dict(method=url.split('/')[-1], result=result))
		return result

	@staticmethod
	def to_debug(data):
		try:
			requests.post(DEBUG_SERVER, data=json.dumps(data))
		except requests.exceptions.RequestException:
			pass


def turn_on(bot):
	admins = [admin['id'] for admin in db.find_user(admin=True, fetch_all=True)]
	bot._request = TelegramRequestWrapper(bot._request, admins)


def turn_off(bot):
	bot._request = bot._request.saved_handler
