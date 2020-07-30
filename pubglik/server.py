"""Classes for Cherrypy web-server setup."""

import json
import logging
from hashlib import sha256

import cherrypy
from telegram import Update
from psycopg2.errors import UniqueViolation

from pubglik import database
from pubglik.config import unitpay_secret as SECRET
from pubglik.texts import (
	settings_names as SETTINGS_NAMES,
	game_not_set as DEFAULT,
	got_money as GOT_MONEY
)

##############################

logger = logging.getLogger('webserver')


@cherrypy.expose
class GetGames():
	"""Returning list of not yet finished games at /api/games."""

	_cp_defaults = {
		'tools.response_headers.on': True,
		'tools.response_headers.headers': [
			('Access-Control-Allow-Origin', '*'),
		]
	}

	@cherrypy.tools.json_out()
	@cherrypy.tools.accept(media='application/json')
	def GET(self):
		try:
			return [
				[SETTINGS_NAMES.get(data, data) if data else DEFAULT for data in game]
					for game in database.get_games()
			]
		except Exception:
			raise cherrypy.HTTPError(500)


@cherrypy.expose
class TelegramHook:
	"""Gets Telegram updates, and puts them into bot's `UpdateQueue`."""

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


@cherrypy.expose
class UnitpayHook:
	"""Gets notifications from Unitpay and updates user's balance."""

	def __init__(self, telegram_dispatcher):
		self.tg = telegram_dispatcher

	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def GET(self, **data):
		# checking where it came from
		if cherrypy.request.remote.ip not in cherrypy.config['unitpay_ip']:
			logger.critical("Someone is pocking our secret hook! (%s)", data)
			return cherrypy.HTTPError(403)

		if data['method'] == "pay":
			# checking signature
			data.pop('params[sign]', None)
			signature = data.pop('params[signature]')
			data_string = "{up}".join([*data.values(), SECRET]).encode('utf-8')
			if signature != sha256(data_string).hexdigest():
				logger.critical("Request with a wrong signature! (%s)", data)
				return {'error': {'message': "Invalid signature"}}

			# processing payment
			user_id = int(data['params[account]'])
			amount = round(float(data['params[profit]']))
			try:
				new_balance = database.change_balance(
					user_id, amount, 'unitpay', ext_id=int(data['params[unitpayId]']))

			except UniqueViolation:
				logger.warning("Ignoring duplicate payment")
				return {'result': {'message': "Duplicate payment"}}

			except Exception as err:  # pylint: disable=broad-except
				logger.critical(
					"User's payment not saved!\n%s", data,
					exc_info=(type(err), err, None)
				)
				self.tg.bot.notify_admins("Database error!!!")
				return {'result': {'message': "Database error :("}}

			self.tg.user_data[user_id]['balance'] = new_balance
			self.tg.bot.send_message(user_id, GOT_MONEY.format(amount, new_balance))

		return {'result': {'message': "OK"}}
