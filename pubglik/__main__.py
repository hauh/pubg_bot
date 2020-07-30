"""Starting HTTPS server, database connections, and bot iteslf."""

import sys
from queue import Queue
from logging import getLogger
from threading import Thread
from time import sleep
from functools import partial

import cherrypy
from telegram.ext import Dispatcher, JobQueue
from telegram.ext.messagequeue import MessageQueue
from telegram.utils.request import Request

from . import database
from . import games
from . import config
from .error import error
from .menu import menu_tree, menu_data
from .core import Bot, PrivateConversationHandler
from .server import GetGames, TelegramHook, UnitpayHook

####################################

logger = getLogger('main')

dispatcher = Dispatcher(
	Bot(
		config.bot_token,
		admin_chat=config.admin_chat,
		msg_queue=MessageQueue(
			all_burst_limit=29,
			all_time_limit_ms=1017,
			autostart=False
		),
		request=Request(
			con_pool_size=10,
			proxy_url=config.proxy if config.proxy else None
		)
	),
	update_queue=Queue(),
	job_queue=JobQueue(),
	use_context=True
)


def connect_database():
	try:
		database.prepare_DB()
	except Exception as err:  # pylint: disable=broad-except
		logger.critical(
			"Database connection failed with:",
			exc_info=(type(err), err, None)
		)
		sys.exit(-1)


def start_server():
	cherrypy.config.update('server.conf')
	mount = partial(
		cherrypy.tree.mount,
		config={'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
	)
	mount(GetGames(), '/api/games')
	mount(UnitpayHook(dispatcher), f'/unitpay/{config.unitpay_key}')
	mount(TelegramHook(dispatcher), f'/telegram/{config.bot_token}')
	cherrypy.engine.start()


def activate_bot():
	dispatcher.bot.set_webhook(**config.webhook_kwargs)

	dispatcher.add_handler(PrivateConversationHandler(menu_tree, menu_data))
	dispatcher.add_error_handler(error)

	dispatcher.job_queue.set_dispatcher(dispatcher)
	dispatcher.job_queue.run_once(games.restore_state, 0)
	dispatcher.job_queue.run_repeating(games.check_slots_and_games, 300, first=60)

	dispatcher.job_queue.start()
	dispatcher.bot.msg_queue.start()
	dispatcher.start()


logger.info('Connecting to database...')
connect_database()

logger.info('Starting server...')
start_server()

logger.info('Activating bot...')
Thread(target=activate_bot, name='dispatcher').start()

logger.info('All good!')
try:
	while True:
		sleep(1)
except KeyboardInterrupt:
	logger.info('Deactivating bot...')
	dispatcher.stop()
	dispatcher.bot.msg_queue.stop()
	dispatcher.job_queue.stop()
	logger.info('Stopping server...')
	cherrypy.engine.exit()

logger.info('Bye!')
