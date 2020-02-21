from telegram import (
	InlineKeyboardButton, InlineKeyboardMarkup,
	KeyboardButton, ReplyKeyboardMarkup
)
import texts

#####################


def makeButtons(buttons_dict):
	return ([InlineKeyboardButton(
		button['button_text'],
		callback_data=button_key
	)] for button_key, button in buttons_dict.items())


def makeKeyboard(buttons_dict, extra_buttons={}, back_button=texts.back):
	return InlineKeyboardMarkup(
		[
			*makeButtons(buttons_dict),
			*makeButtons(extra_buttons),
			*makeButtons(back_button)
		]
	)


# main
main_menu_user = makeKeyboard(texts.main['buttons'], back_button={})
main_menu_admin = makeKeyboard(texts.main['buttons'], texts.admin_option, {})
how = makeKeyboard(texts.main['buttons']['how']['buttons'])
about = makeKeyboard(texts.main['buttons']['about']['buttons'])

# profile
profile_keyboard = makeKeyboard(texts.profile['buttons'])

# admin
admin_menu = makeKeyboard(texts.admin['buttons'])
spam = makeKeyboard(texts.admin['buttons']['spam']['buttons'])
admins = makeKeyboard(texts.admin['buttons']['admins']['buttons'])
servers = makeKeyboard(texts.admin['buttons']['servers']['buttons'])
pubg_api = makeKeyboard(texts.admin['buttons']['pubg_api']['buttons'])
