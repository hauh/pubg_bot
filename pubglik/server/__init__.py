"""Cherrypy classes to communicate with Telegram, payments operators, and website"""  # noqa

from .api import GetGames
from .hook_telegram import TelegramHook
from .hook_unitpay import UnitpayHook
