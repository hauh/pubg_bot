from logging import getLogger
from itertools import chain

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
import buttons

#######################

logger = getLogger(__name__)
MATCHES, PICK, FILTERS = range(0, 3)
filter_types = ['mode', 'view', 'bet']
matches_menu = texts.menu['next']['matches']


def matchesMain(update, context):
	# if 'pubg_id' not in context.user_data:
	# 	return menu.sendMessage(
	# 		update, context, 'matches',
	# 		texts.pubg_id_not_set['msg'],
	# 		texts.pubg_id_not_set['buttons']
	# 	)

	if any(filter_type in context.user_data for filter_type in filter_types):
		show_reset = True
	else:
		show_reset = False

	msg_format = {
		filter_type: matches_menu['next'][filter_type]['next']
						[context.user_data[filter_type]]['btn']
				if filter_type in context.user_data
				else matches_menu['default']
			for filter_type in filter_types
	}
	msg_format.update({
		'match': context.user_data['match']
			if 'match' in context.user_data
			else matches_menu['default']
	})

	menu.sendMessage(
		update, context,
		matches_menu['msg'].format(**msg_format),
		matches_menu['buttons'] if show_reset else matches_menu['buttons'][1:],
		'matches'
	)
	return MATCHES


def reset(update, context):
	if 'match' in context.user_data:
		del context.user_data['match']
	for filter_type in matches_menu['next'].keys():
		if filter_type in context.user_data:
			del context.user_data[filter_type]
	return matchesMain(update, context)


def matchesList(update, context):
	current_menu = matches_menu['next']['choose_match']

	matches_buttons = []
	matches_found = database.getMatches({
		filter_type: context.user_data[filter_type]
			if filter_type in context.user_data else None
			for filter_type in filter_types
	})
	if matches_found:
		for match in matches_found:
			matches_buttons.append(
				[buttons.createButton(
					"{} - {} - {} - {}".format(
						match[0],
						matches_menu['next']['mode']['next'][match[1]]['btn'],
						matches_menu['next']['view']['next'][match[2]]['btn'],
						matches_menu['next']['bet']['next'][match[3]]['btn']
					),
					"match{}".format(match[0])
				)]
			)
		found = len(matches_found)
	else:
		found = 0

	menu.sendMessage(
		update, context,
		current_menu['msg'].format(found),
		matches_buttons + current_menu['buttons'],
		'choose_match'
	)
	return PICK


def pickMatch(update, context):
	match_id = update.callback_query.data.lstrip('match')
	context.user_data['match'] = match_id
	update.callback_query.answer(texts.match_is_chosen.format(match_id))
	return matchesMain(update, context)


def chooseFilter(update, context):
	next_state = update.callback_query.data
	current_menu = matches_menu['next'][next_state]
	menu.sendMessage(
		update, context,
		current_menu['msg'],
		current_menu['buttons'],
		next_state
	)
	return FILTERS


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
			CallbackQueryHandler(reset, pattern=r'^reset$'),
			CallbackQueryHandler(matchesList, pattern=r'^choose_match$'),
			CallbackQueryHandler(
				chooseFilter,
				pattern=r'^({})$'.format(')|('.join(filter_types))
			),
		],
		FILTERS: [
			CallbackQueryHandler(
				getFilterSetting,
				pattern=r'^({})$'.format(')|('.join(
					list(chain(*[list(matches_menu['next'][filter_type]['next'].keys())
										for filter_type in filter_types]))
				))
			)
		],
		PICK: [
			CallbackQueryHandler(pickMatch, pattern=r'^match[0-9]+$'),
		]
	},
	fallbacks=[],
	allow_reentry=True
)
