from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import texts
import config

##############################


def create_button(text, callback_data):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirm_button(callback_data):
	return [InlineKeyboardButton(texts.confirm, f'confirm_{callback_data}')]


def add_buttons_to_menu():
	def add_buttons(menu, depth=0):
		buttons = []
		if 'next' in menu:
			for button_key, button_data in menu['next'].items():
				if 'btn' in button_data:
					buttons.append(create_button(button_data['btn'], button_key))
				add_buttons(button_data, depth + 1)
		if depth:
			buttons.append(back_button + main_button if depth > 1 else [])
		menu['buttons'] = buttons

	back_button = create_button(texts.back, 'back')
	main_button = create_button(texts.main, 'main')
	add_buttons(texts.menu)
	texts.menu['buttons'][5][0].url = config.battle_chat


admin_warnings = {
	'qiwi_failed': {
		'text': texts.qiwi_error,
		'reply_markup': InlineKeyboardMarkup(
			[[InlineKeyboardButton(texts.goto_qiwi, url=config.qiwi_url)]])
	},
	'prizes': {
		'text': texts.match_has_ended
	},
}


def message_admins(bot, status, **format_kwargs):
	message = admin_warnings[status]
	bot.send_message(
		config.admin_group_id,
		message['text'].format(**format_kwargs),
		reply_markup=message.get('reply_markup')
	)
