from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
import buttons

#######################

logger = getLogger(__name__)
FILTERS, SETTING, PICK = range(0, 3)
filter_types = ['mode', 'view', 'bet']


def matchesList(update, context):
	current_menu = texts.matches['extra']['choose_match']

	matches_buttons = []
	if 'match' in context.user_data:
		chosen_match = context.user_data['match']
		matches_buttons.append(current_menu['extra']['unset']['button'])
	else:
		chosen_match = current_menu['default']
		show_unset_button = False

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

	menu.sendMessage(
		update, context, 'matches',
		current_menu['msg'].format(found, chosen_match),
		current_menu['buttons'],
		matches_buttons
	)
	return PICK


def unsetMatch(update, context):
	if 'match' in context.user_data:
		del context.user_data['match']
	return matchesMain(update, context)


def pickMatch(update, context):
	match_id = update.callback_query.data.lstrip('match')
	context.user_data['match'] = match_id
	update.callback_query.answer(texts.match_is_chosen.format(match_id))
	return matchesMain(update, context)


def matchesMain(update, context):
	# if 'pubg_id' not in context.user_data:
	# 	return menu.sendMessage(
	# 		update, context, 'matches',
	# 		texts.pubg_id_not_set['msg'],
	# 		texts.pubg_id_not_set['buttons']
	# 	)

	filters_set = 0
	msg_format = {}
	for filter_type in filter_types:
		if filter_type in context.user_data:
			filters_set += 1
			msg_format.update({
				filter_type: texts.matches['next'][filter_type]['next']
								[context.user_data[filter_type]]['btn']
			})
		else:
			msg_format.update({filter_type: texts.matches['default']})
	if filters_set > 0:
		if filters_set == 3:
			return matchesList(update, context)
		show_reset = True
	else:
		show_reset = False
	menu.sendMessage(
		update, context, 'matches',
		texts.matches['msg'].format(**msg_format),
		texts.matches['buttons'],
		[texts.matches['extra']['reset']['button']] if show_reset else []
	)
	return FILTERS


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
		FILTERS: [
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
		PICK: [
			CallbackQueryHandler(unsetMatch, pattern=r'^unset$'),
			CallbackQueryHandler(pickMatch, pattern=r'^match[0-9]+$'),
		]
	},
	fallbacks=[],
	allow_reentry=True
)
