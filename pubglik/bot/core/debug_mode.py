"""Monkey patching bot instance to redirect requests to debug chat"""

# pylint: disable=protected-access

import json
import logging

import requests

from pubglik import database as db
from pubglik.config import debug_server as DBG_SERVER, debug_chat as DBG_CHAT

##############################

logger = logging.getLogger('debug_mode')


class TelegramRequestWrapper():
	"""Redirects requests to debug chat and sends copies to debug server"""

	def __init__(self, original_request_handler, admins):
		self.saved_handler = original_request_handler
		self.admins = admins

	def __getattr__(self, attr):
		return getattr(self.saved_handler, attr)

	def post(self, url, data, timeout=None):
		method = url.split('/')[-1]
		copy = dict(method=method)
		if 'chat_id' in data:
			copy.update(chat_id=data['chat_id'])
			if int(data['chat_id']) not in self.admins:
				data['chat_id'] = DBG_CHAT
		if method != 'answerCallbackQuery':
			result = self.saved_handler.post(url, data, timeout)
			copy.update(result=result)
		else:
			result = None
			copy.update(answer=data['text'])
		self.to_debug(copy)
		return result

	def get(self, url, timeout=None):
		result = self.saved_handler.get(url, timeout)
		self.to_debug(dict(method=url.split('/')[-1], result=result))
		return result

	@staticmethod
	def to_debug(data):
		try:
			requests.post(DBG_SERVER, data=json.dumps(data))
		except requests.exceptions.RequestException:
			pass


def turn_on(bot):
	admins = [admin['id'] for admin in db.find_user(admin=True, fetch_all=True)]
	bot._request = TelegramRequestWrapper(bot._request, admins)
	logger.warning('Debug mode turned on')


def turn_off(bot):
	bot._request = bot._request.saved_handler
	logger.info('Debug mode turned off')
