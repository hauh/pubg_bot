from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import config
import texts

##############################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


back_button = createButton(texts.back, 'back')
main_button = createButton(texts.main, 'main')
confirm_button = createButton(texts.confirm, 'confirm')
reset_button = createButton(texts.reset, 'reset')


def generateButtons(menu, depth=0):
	buttons = []
	if 'next' in menu:
		for button_key, button_data in menu['next'].items():
			if 'btn' in button_data:
				buttons.append([createButton(button_data['btn'], button_key)])
			generateButtons(button_data, depth + 1)
	if depth > 1:
		buttons.append([back_button, main_button])
	elif depth:
		buttons.append([back_button])
	menu['buttons'] = buttons


def updateMenuWithButtons():
	generateButtons(texts.menu)
	texts.menu['buttons'][5][0].url = config.battle_chat
