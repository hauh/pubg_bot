from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import config
import texts

##############################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


def generateButtons(menu, depth=0):
	menu['buttons'] = []
	if 'next' in menu:
		for button_key, button_data in menu['next'].items():
			menu['buttons'].append([createButton(button_data['btn'], button_key)])
			generateButtons(button_data, depth + 1)
	if depth:
		navigation = [createButton(texts.back, 'back')]
		if depth > 1:
			navigation.append(createButton(texts.main, 'main'))
		menu['buttons'].append(navigation)


def updateSpecialButtons():
	texts.menu['next']['rooms']['buttons'][0][0].url = config.battle_chat
