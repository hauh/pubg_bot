from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import texts
import config

##############################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


def generateButtons(menu):
	menu['buttons'] = []
	if 'next' in menu:
		for button_key, button_data in menu['next'].items():
			menu['buttons'].append([createButton(button_data['btn'], button_key)])
			generateButtons(button_data)
	depth = menu['depth'] if 'depth' in menu else 2
	if depth:
		navigation = [createButton(texts.back, 'back')]
		if depth > 1:
			navigation.append(createButton(texts.main, 'main'))
		menu['buttons'].append(navigation)
	if 'extra' in menu:
		for button_key, button_data in menu['extra'].items():
			if 'next' in button_data:
				generateButtons(button_data)
			menu['extra'][button_key]['button'] =\
				[createButton(button_data['btn'], button_key)]


def prepareMenu():
	for menu_name in dir(texts):
		if not menu_name.startswith('_'):
			menu = getattr(texts, menu_name)
			if type(menu) is dict:
				generateButtons(menu)
	texts.rooms['buttons'][0][0].url = config.battle_chat
