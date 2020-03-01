from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu

#######################

logger = getLogger(__name__)
ROOMS, HOT = range(0, 2)
rooms_menu = texts.menu['next']['rooms']


def roomsMain(update, context):
	menu.sendMessage(
		update, context,
		rooms_menu['msg'],
		rooms_menu['buttons'],
		'rooms'
	)
	return ROOMS


def hotRooms(update, context):
	current_menu = rooms_menu['next']['hot_rooms']
	menu.sendMessage(
		update, context,
		current_menu['msg'],
		current_menu['buttons'],
		'hot_rooms'
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
