from logging import getLogger

from telegram import ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu

#######################

logger = getLogger('matches')
FILTERS, SETTING = range(0, 2)


def matchesStart(update, context):
	msg_format = {}
	show_reset = False
	for filter_type in texts.matches['next'].keys():
		if filter_type in context.user_data:
			filter_value = (
				texts.matches['next'][filter_type]['next']
				[context.user_data[filter_type]]['btn']
			)
			show_reset = True
		else:
			filter_value = texts.matches['default']
		msg_format.update({filter_type: filter_value})
	menu.sendMessage(
		update, context, 'matches', texts.matches,
		extra=texts.reset if show_reset else {},
		msg_format=msg_format
	)
	return FILTERS


def resetFilters(update, context):
	for filter_type in texts.matches['next'].keys():
		if filter_type in context.user_data:
			del context.user_data[filter_type]
	return matchesStart(update, context)


def chooseFilter(update, context):
	next_state = update.callback_query.data
	menu.sendMessage(
		update, context, next_state,
		texts.matches['next'][next_state]
	)
	return SETTING


def getFilterSetting(update, context):
	filter_type = context.user_data['conv_history'].pop()
	context.user_data[filter_type] = update.callback_query.data
	return matchesStart(update, context)


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(matchesStart, pattern=r'^matches$')
	],
	states={
		FILTERS: [
			CallbackQueryHandler(resetFilters, pattern=r'^reset$'),
			CallbackQueryHandler(
				chooseFilter,
				pattern=r'^({})$'.format(')|('.join(texts.matches['next'].keys()))
			),
		],
		SETTING: [
			CallbackQueryHandler(
				getFilterSetting,
				pattern=r'^({mode_types})|({view_types})|({bet_types})$'.format(
					mode_types=')|('.join(texts.matches['next']['mode']['next'].keys()),
					view_types=')|('.join(texts.matches['next']['view']['next'].keys()),
					bet_types=')|('.join(texts.matches['next']['bet']['next'].keys())
				)
			)
		],
	},
	fallbacks=[],
	allow_reentry=True
)
