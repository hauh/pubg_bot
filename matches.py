from logging import getLogger

from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
import buttons

#######################

logger = getLogger(__name__)
MATCHES, SETTING = range(0, 2)
filter_types = ['mode', 'view', 'bet']


def matchesMain(update, context):
	filters = {
		f_type: context.user_data[f_type]
			if f_type in context.user_data else None
		for f_type in filter_types
	}

	matches_buttons = []
	if 'match' in context.user_data:
		chosen_match = context.user_data['match']
		matches_buttons.append(texts.matches['extra']['clear_choice']['button'])
	else:
		chosen_match = texts.matches['default']
	matches_found = database.getMatches(filters)
	if matches_found:
		for match in matches_found:
			matches_buttons.append(
				[buttons.createButton(
					"{} - {} - {} - {}".format(
						match[0],
						texts.matches['next']['mode']['next'][match[1]]['btn'],
						texts.matches['next']['view']['next'][match[2]]['btn'],
						texts.matches['next']['bet']['next'][match[3]]['btn']
					),
					"match{}".format(match[0])
				)]
			)
		found = len(matches_found)
	else:
		found = 0
	if any(filters.values()):
		matches_buttons.append(texts.matches['extra']['reset']['button'])

	menu.sendMessage(
		update, context, 'matches',
		texts.matches['msg'].format(
			**{f_type: texts.matches['next'][f_type]['next'][filters[f_type]]['btn']
						if filters[f_type] else texts.matches['default']
						for f_type in filter_types},
			found=found,
			chosen_match=chosen_match
		),
		matches_buttons, texts.matches['buttons'],
	)
	return MATCHES


def chooseMatch(update, context):
	match_id = update.callback_query.data.lstrip('match')
	context.user_data['match'] = match_id
	update.callback_query.answer(texts.match_is_chosen.format(match_id))
	return matchesMain(update, context)


def clearMatchChoice(update, context):
	if 'match' in context.user_data:
		del context.user_data['match']
	return matchesMain(update, context)


def resetFilters(update, context):
	for filter_type in texts.matches['next'].keys():
		if filter_type in context.user_data:
			del context.user_data[filter_type]
	return matchesMain(update, context)


def chooseFilter(update, context):
	next_state = update.callback_query.data
	menu.sendMessage(
		update, context, next_state,
		texts.matches['next'][next_state]['msg'],
		texts.matches['next'][next_state]['buttons']
	)
	return SETTING


def getFilterSetting(update, context):
	filter_type = context.user_data['conv_history'].pop()
	context.user_data[filter_type] = update.callback_query.data
	return matchesMain(update, context)


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(matchesMain, pattern=r'^matches$')
	],
	states={
		MATCHES: [
			CallbackQueryHandler(chooseMatch, pattern=r'^match[0-9]+$'),
			CallbackQueryHandler(clearMatchChoice, pattern=r'^clear_choice$'),
			CallbackQueryHandler(resetFilters, pattern=r'^reset$'),
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
