from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import config
import texts
import menu

#######################

logger = getLogger(__name__)
ROOMS = 0
HOT = 1


def roomsMain(update, context):
	menu.sendMessage(
		update, context, 'rooms',
		texts.rooms['msg'], texts.rooms['buttons']
	)
	return ROOMS


def hotRooms(update, context):
	menu.sendMessage(
		update, context, 'hot_rooms',
		texts.rooms['next']['hot_rooms']['msg'],
		texts.rooms['next']['hot_rooms']['buttons']
	)
	return HOT


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(roomsMain, pattern=r'^rooms$')
	],
	states={
		ROOMS: [
			CallbackQueryHandler(hotRooms, pattern=r'^hot_rooms$')
		],
		HOT: []
	},
	fallbacks=[],
	allow_reentry=True
)
