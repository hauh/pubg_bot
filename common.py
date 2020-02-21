from telegram import ParseMode


reply_args = None


def pickMenuOption(update, context):
	state, message, keyboard = reply_args[update.callback_query.data]
	update.callback_query.edit_message_text(
		message,
		parse_mode=ParseMode.MARKDOWN,
		reply_markup=keyboard
	)
	context.user_data['conv_level'] = state
	return state
