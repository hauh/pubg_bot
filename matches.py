from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
import buttons

#######################

logger = getLogger(__name__)
matches_menu = texts.menu['next']['matches']
filter_types = ['mode', 'view', 'bet']


def matchesMain(update, context):
	# if 'pubg_id' not in context.user_data:
	# 	return menu.sendMessage(
	# 		update, context, 'matches',
	# 		texts.pubg_id_not_set['msg'],
	# 		texts.pubg_id_not_set['buttons']
	# 	)

	if any(filter_type in context.user_data for filter_type in filter_types)\
		or 'slot' in context.user_data:
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
	msg_format.update({'match': context.user_data.get('slot', '-')})
	return (
		matches_menu['msg'].format(**msg_format),
		matches_menu['buttons'] if show_reset else matches_menu['buttons'][1:]
	)


def reset(update, context):
	if 'slot' in context.user_data:
		del context.user_data['slot']
	for filter_type in matches_menu['next'].keys():
		if filter_type in context.user_data:
			del context.user_data[filter_type]
	return matchesMain(update, context)


def slotsList(update, context):
	current_menu = matches_menu['next']['choose_slot']

	slots_buttons = []
	slots_found = database.getMatches({
		filter_type: context.user_data[filter_type]
			if filter_type in context.user_data else None
			for filter_type in filter_types
	})
	if slots_found:
		for slot in slots_found:
			slots_buttons.append(
				[buttons.createButton(
					"{} - {} - {} - {}".format(
						slot['id'],
						matches_menu['next']['mode']['next'][slot['mode']]['btn'],
						matches_menu['next']['view']['next'][slot['view']]['btn'],
						matches_menu['next']['bet']['next'][slot['bet']]['btn']
					),
					"slot{}".format(slot['id'])
				)]
			)
		found = len(matches_found)
	else:
		found = 0

	return (
		current_menu['msg'].format(found),
		slots_buttons + current_menu['buttons']
	)


def pickSlot(update, context):
	slot_id = update.callback_query.data.lstrip('slot')
	context.user_data['slot'] = slot_id
	update.callback_query.answer(
		texts.match_is_chosen.format(slot_id), show_alert=True)
	context.chat_data['history'].pop()
	return matchesMain(update, context)


def getFilterSetting(update, context):
	context.chat_data['history'].pop()
	filter_type = context.chat_data['history'].pop()
	context.user_data[filter_type] = update.callback_query.data
	return matchesMain(update, context)


filter_values_regex = r'^({})$'.format(')|('.join(
	filter_value
		for filter_type in filter_types
			for filter_value in matches_menu['next'][filter_type]['next'].keys()
))
callbacks = {
	r'^matches$'		: matchesMain,
	r'^reset$'			: reset,
	filter_values_regex	: getFilterSetting,
	r'^choose_slot$'	: slotsList,
	r'^slot_[0-9]+$'	: pickSlot
}
