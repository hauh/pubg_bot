from logging import getLogger

from telegram import ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler

import config
import texts
import menu

#######################

logger = getLogger(__name__)
ROOMS = 0


def roomsStart(update, context):
	menu.sendMessage(
		update, context, 'rooms', texts.rooms
	)
	return ROOMS


def battleChat(update, context):
	keyboard = menu.createKeyboard(texts.rooms, {})
	keyboard.inline_keyboard[0][0].url = config.battle_chat
	update.effective_chat.send_message(
		"HELLO",
		reply_markup=keyboard
	)
	return -1


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(roomsStart, pattern=r'^rooms$')
	],
	states={
		ROOMS: [
			CallbackQueryHandler(battleChat, pattern=r'^battle_chat$')
		]
	},
	fallbacks=[],
	allow_reentry=True
)
