"""Monkey patching bot instance to redirect requests to debug chat"""

import json

import requests

from pubglik.config import debug_server as DEBUG_SERVER

##############################


class TelegramRequestWrapper():
	"""Redirects requests to debug chat and sends copies to debug server"""

	def __init__(self, original_request_handler):
		self.saved_handler = original_request_handler

	def __getattr__(self, attr):
		return getattr(self.saved_handler, attr)

	def post(self, url, data, timeout=None):
		try:
			return self.saved_handler.post(url, data, timeout)
		except OSError:
			data.update(method=url.split('/')[-1])
			try:
				requests.post(DEBUG_SERVER, data=json.dumps(data))
			except requests.exceptions.RequestException:
				pass
			return None
