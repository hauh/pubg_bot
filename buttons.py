from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup

import texts

##############################


def createButton(button_msg, button_key):
	return InlineKeyboardButton(
		button_msg,
		callback_data=button_key
	)


def createKeyboard(menu, depth=2):
	choices = []
	if 'next' in menu:
		for button_key, button_data in menu['next'].items():
			choices.append([createButton(button_data['btn'], button_key)])
	if depth:
		navigation = [createButton(texts.back, 'back')]
		if depth > 1:
			navigation.append(createButton(texts.main, 'main'))
		choices.append(navigation)
	return InlineKeyboardMarkup(choices)


##############################


texts.menu['keyboard'] = createKeyboard(menu, depth=0)
texts.matches['keyboard'] = createKeyboard(matches, depth=1)
texts.matches['next']['mode']['keyboard'] =\
	createKeyboard(texts.matches['next']['mode'])
texts.matches['next']['view']['keyboard'] =\
	createKeyboard(texts.matches['next']['view'])
texts.matches['next']['bet']['keyboard'] =\
	createKeyboard(texts.matches['next']['bet'])
texts.rooms['keyboard'] = createKeyboard(texts.rooms, depth=1)
# texts.profile['keyboard'] = createKeyboard(texts.profile, depth=1)
texts.admin['keyboard'] = createKeyboard(texts.admin, depth=1)
