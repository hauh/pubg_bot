from logging import getLogger

from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
import buttons

#######################

logger = getLogger(__name__)
FILTERS, SETTING = range(0, 2)
filter_types = ['mode', 'view', 'bet']


def matchesStart(update, context):
	filters = {
		filter_type: context.user_data[filter_type]
			if filter_type in context.user_data else None
		for filter_type in filter_types
	}
	matches_buttons = []
	matches_found = database.getMatches(filters)
	if matches_found:
		for match in matches_found:
			matches_buttons.append(
				[buttons.createButton(
					"{} - {} - {}".format(
						texts.matches['next']['mode']['next'][match[1]]['btn'],
						texts.matches['next']['view']['next'][match[2]]['btn'],
						texts.matches['next']['bet']['next'][match[3]]['btn']
					),
					"match{}".format(match[0])
				)]
			)

	show_reset = False
	for filter_type, filter_value in filters.items():
		if filter_value:
			filters[filter_type] = (
				texts.matches['next'][filter_type]['next']
				[context.user_data[filter_type]]['btn']
			)
			show_reset = True
		else:
			filters[filter_type] = texts.matches['default']
	filters.update({'found': len(matches_found) if matches_found else 0})

	menu.sendMessage(
		update, context, 'matches', texts.matches,
		extra=matches_buttons + texts.matches['extra_buttons'],
		msg_format=filters
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
			# CallbackQueryHandler(matchesList, pattern=r'^matches_list$'),
			CallbackQueryHandler(
				chooseFilter,
				pattern=r'^({})$'.format(')|('.join(filter_types))
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
