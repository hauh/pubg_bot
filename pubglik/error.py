"""Handling error and returning to main if it was from user"""

import logging

from pubglik.interface.texts import error as ERROR

##############################

logger = logging.getLogger('error')


def error(update, context):
	err = (type(context.error), context.error, None)

	if not update or not context.user_data:
		logger.error("Bot broke down!", exc_info=err)
		return

	if update.callback_query:
		update.callback_query.answer(ERROR, show_alert=True)
		failed_message = update.callback_query.data
	else:
		failed_message = update.message.text
	conversation = context.user_data.get('conversation')
	logger.error(
		"User %s broke down bot in menu %s, failed message: %s",
		update.effective_user.id, str(conversation), failed_message, exc_info=err
	)

	# returning to main menu
	if conversation:
		while conversation.state.back:
			conversation.state = conversation.state.back
		context.dispatcher.handlers[0][0].handle_update(
			update, context.dispatcher, conversation, context)
