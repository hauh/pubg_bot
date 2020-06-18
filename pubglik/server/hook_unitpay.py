"""Recieving payments info from Unitpay."""

from logging import getLogger
from hashlib import sha256

import cherrypy
from psycopg2.errors import Error, UniqueViolation

from pubglik import database
from pubglik.config import unitpay_secret as SECRET
from pubglik.bot.texts import got_money as GOT_MONEY

##############################

logger = getLogger('unitpay_hook')


@cherrypy.expose
class UnitpayHook:
	"""Gets notifications from Unitpay and updates user's balance."""

	def __init__(self, telegram_dispatcher):
		self.dispatcher = telegram_dispatcher

	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def GET(self, **data):
		# checking where it came from
		unitpay_ips = cherrypy.request.app.config['unitpay']['ip']
		if cherrypy.request.remote.ip not in unitpay_ips:
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
			user_id = int(data['account'])
			amount = int(data['profit'])
			try:
				new_balance = database.change_balance(
					user_id, amount, 'unitpay', ext_id=int(data['unitpayId']))

			except UniqueViolation:  # to-do: add unique constraint to ext id
				logger.warning("Ignoring duplicate payment")

			except Error as err:
				logger.critical(
					"User's payment not saved!\n%s", data,
					exc_info=(type(err), err, None)
				)
				self.dispatcher.bot.notify_admins("Database error!!!")

			else:
				self.dispatcher.user_data[user_id]['balance'] = new_balance
				self.dispatcher.bot.send_message(
					user_id, GOT_MONEY.format(amount, new_balance))

		return {'result': {'message': "OK"}}
