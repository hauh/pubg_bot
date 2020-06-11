'''Monkey patching bot instance to catch requests locally'''

# pylint: disable=protected-access

import json

import requests

from config import debugging_server as DEBUGGING_SERVER

##############################


class TelegramRequestWrapper():
	'''Sends requests also to localhost'''

	def __init__(self, original_request_handler):
		self.saved_handler = original_request_handler

	def __getattr__(self, attr):
		return getattr(self.saved_handler, attr)

	def post(self, url, data, timeout=None):
		result = self.saved_handler.post(url, data, timeout)
		self.to_debug({'method': url.split('/')[-1], 'result': result, 'data': data})
		return result

	def get(self, url, timeout=None):
		result = self.saved_handler.get(url, timeout)
		self.to_debug({'method': url.split('/')[-1], 'result': result})
		return result

	def to_debug(self, data):
		try:
			requests.post(DEBUGGING_SERVER, data=json.dumps(data))
		except requests.exceptions.RequestException:
			pass


def turn_on(bot):
	bot._request = TelegramRequestWrapper(bot._request)


def turn_off(bot):
	bot._request = bot._request.saved_handler
