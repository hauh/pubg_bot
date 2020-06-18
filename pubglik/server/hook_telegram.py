"""Recieving updates from Telegram servers."""

import json
from logging import getLogger

import cherrypy
from telegram import Update


##############################

logger = getLogger('telegram_hook')


@cherrypy.expose
class TelegramHook:
	"""Gets Telegram updates, and puts them into bot's UpdateQueue."""

	def __init__(self, telegram_dispatcher):
		self.tg = telegram_dispatcher

	def POST(self):
		data = json.loads(cherrypy.request.body.read())
		try:
			update = Update.de_json(data, self.tg.bot)
		except ValueError as err:
			logger.error(
				"Non-telegram update recieved:\n%s",
				data, exc_info=(type(err), err, None)
			)
		else:
			self.tg.update_queue.put(update)
