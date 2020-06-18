"""Starting HTTPS server, database connections pool, and bot iteslf"""

import sys
from queue import Queue
from logging import getLogger
from threading import Thread
from time import sleep

import cherrypy
from telegram.ext import Dispatcher
from telegram.utils.request import Request
from telegram.ext.messagequeue import MessageQueue

from . import config, bot, database
from .bot.core import Bot
from .server import GetGames, TelegramHook, UnitpayHook

####################################

logger = getLogger('main')

messages_queue = MessageQueue(
	all_burst_limit=29,
	all_time_limit_ms=1017,
	autostart=False
)
pubglik_bot = Bot(
	config.bot_token,
	admin_chat=config.admin_chat,
	msg_queue=messages_queue,
	request=Request(
		con_pool_size=10,
		proxy_url=config.proxy if config.proxy else None
	)
)
dispatcher = Dispatcher(pubglik_bot, Queue(), use_context=True)


def run():
	# run database connections
	logger.info('Connecting to database...')
	try:
		database.prepare_DB()
	except Exception as err:  # pylint: disable=broad-except
		logger.critical(
			"Database connection failed with:",
			exc_info=(type(err), err, None)
		)
		sys.exit(-1)
	logger.info('Database ready!')

	# run sever
	logger.info('Starting server...')
	cherrypy.config.update('server.conf')
	app_config = {'/':
		{'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
	}
	cherrypy.tree.mount(GetGames(), '/api/games', app_config)
	cherrypy.tree.mount(
		UnitpayHook(dispatcher), f'/unitpay/{config.unitpay_key}', app_config)
	cherrypy.tree.mount(
		TelegramHook(dispatcher), f'/telegram/{config.bot_token}', app_config)
	cherrypy.engine.start()
	logger.info('Server started!')

	# run bot
	logger.info('Starting bot...')
	pubglik_bot.set_webhook(**config.webhook_kwargs)
	bot.setup(dispatcher)
	messages_queue.start()
	bot_thread = Thread(target=dispatcher.start, name='dispatcher')
	bot_thread.start()
	logger.info('Bot started!')

	# idle
	try:
		while True:
			sleep(1)
	except KeyboardInterrupt:
		logger.info('Stopping bot...')
		messages_queue.stop()
		dispatcher.job_queue.stop()
		dispatcher.stop()
		logger.info('Stopping server...')
		cherrypy.engine.exit()

	logger.info('Bye!')
