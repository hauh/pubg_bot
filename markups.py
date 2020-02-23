from telegram import (
	InlineKeyboardButton, InlineKeyboardMarkup,
	KeyboardButton, ReplyKeyboardMarkup
)
import texts

#####################


def makeButtons(buttons_dict):
	return ([InlineKeyboardButton(
		button['btn'],
		callback_data=button_key
	)] for button_key, button in buttons_dict.items())


def makeKeyboard(buttons_dict, extra_buttons={}, navigation=texts.nav):
	return InlineKeyboardMarkup(
		[
			*makeButtons(buttons_dict),
			*makeButtons(extra_buttons),
			*makeButtons(navigation)
		]
	)


# main
main_menu_user = makeKeyboard(texts.main['next'], navigation={})
main_menu_admin = makeKeyboard(texts.main['next'], texts.admin_option, {})
how = makeKeyboard(texts.main['next']['how']['next'])
about = makeKeyboard(texts.main['next']['about']['next'])

# profile
profile_keyboard = makeKeyboard(texts.profile['next'])

# admin
admin_menu = makeKeyboard(texts.admin['next'])
spam = makeKeyboard(texts.admin['next']['spam']['next'])
admins = makeKeyboard(texts.admin['next']['admins']['next'])
servers = makeKeyboard(texts.admin['next']['servers']['next'])
pubg_api = makeKeyboard(texts.admin['next']['pubg_api']['next'])
