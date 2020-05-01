from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import texts
import config

##############################


def create_button(text, callback_data):
	return [InlineKeyboardButton(text, callback_data=callback_data)]


def confirm_button(callback_data):
	return create_button(texts.confirm, f'confirm_{callback_data}')


def add_buttons_to_menu():
	def add_buttons(menu, depth=0):
		buttons = []
		for key, next_menu in menu.get('next', {}).items():
			if 'btn' in next_menu:
				buttons.append(create_button(next_menu['btn'], key))
			add_buttons(next_menu, depth + 1)
		if depth:
			buttons.append(back_button + main_button if depth > 1 else [])
		menu['buttons'] = buttons
		for key, text in menu.get('extra_buttons', {}).items():
			menu['extra_buttons'][key] = create_button(text, key)

	back_button = create_button(texts.back, 'back')
	main_button = create_button(texts.main, 'main')
	add_buttons(texts.menu)
	texts.menu['buttons'][4][0].url = config.battle_chat


admin_warnings = {
	'qiwi_failed': {
		'text': texts.qiwi_error,
		'reply_markup': InlineKeyboardMarkup(
			[[InlineKeyboardButton(texts.goto_qiwi, url=config.qiwi_url)]])
	},
}


def message_admins(bot, status, **format_kwargs):
	message = admin_warnings[status]
	bot.send_message(
		config.admin_group_id,
		message['text'].format(**format_kwargs),
		reply_markup=message.get('reply_markup')
	)
