from telegram import (
	InlineKeyboardButton, InlineKeyboardMarkup,
	KeyboardButton, ReplyKeyboardMarkup
)
import buttons as btn


def makeKeyboard(buttons):
	return InlineKeyboardMarkup(
		[[InlineKeyboardButton(
			text=button_text,
			callback_data=button_data
		)] for button_data, button_text in buttons.items()]
	)


start_user = makeKeyboard(btn.start)
start_admin = makeKeyboard({**btn.start, **btn.admin_option})
admin_menu = makeKeyboard({**btn.admin_menu, **btn.back})
back = makeKeyboard(btn.back)
