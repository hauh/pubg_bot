from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database

#######################

logger = getLogger(__name__)
matches_menu = texts.menu['next']['matches']
filter_types = ['mode', 'view', 'bet']


def matchesMain(update, context):
	picked_slots = context.user_data.setdefault('picked_slots', [])
	message = matches_menu['msg'].format(
		'\n'.join(str(slot) for slot in picked_slots)
			if picked_slots else matches_menu['default'])
	buttons = [[slot.createButton(leave=True)] for slot in picked_slots]
	if len(picked_slots) < 3:
		buttons += [[slot.createButton()] for slot in context.bot_data['slots']
														if slot not in picked_slots]
	buttons += matches_menu['buttons']
	return (message, buttons)


def pickSlot(update, context):
	current_menu = matches_menu['next']['slot_']
	picked_slots = context.user_data['picked_slots']
	picked_slot_id = int(update.callback_query.data.lstrip('slot_'))
	found_slot = None

	for slot in context.bot_data['slots']:
		if slot.slot_id == picked_slot_id:
			found_slot = slot

	if not found_slot:
		update.callback_query.answer(texts.match_not_found)
	elif found_slot in picked_slots:
		picked_slots.remove(found_slot)
		found_slot.leave()
		update.callback_query.answer(texts.left_from_match)
	elif len(picked_slots) < 3:
		if found_slot.user_count == 0:
			return createSlot(update, context)
		picked_slots.append(found_slot)
		found_slot.user_data += 1
		update.callback_query.answer(texts.match_is_chosen.format(picked_slot_id))
	else:
		update.callback_query.answer(texts.maximum_matches)

	context.chat_data['history'].pop()
	return matchesMain(update, context)


def createSlot(update, context):
	pass


# def slotsList(update, context):
# 	current_menu = matches_menu['next']['choose_slot']

# 	slots_buttons = []
# 	slots_found = database.getMatches({
# 		filter_type: context.user_data[filter_type]
# 			if filter_type in context.user_data else None
# 			for filter_type in filter_types
# 	})
# 	if slots_found:
# 		for slot in slots_found:
# 			slots_buttons.append(
# 				[buttons.createButton(
# 					"{} - {} - {} - {}".format(
# 						slot['id'],
# 						matches_menu['next']['mode']['next'][slot['mode']]['btn'],
# 						matches_menu['next']['view']['next'][slot['view']]['btn'],
# 						matches_menu['next']['bet']['next'][slot['bet']]['btn']
# 					),
# 					"slot{}".format(slot['id'])
# 				)]
# 			)
# 		found = len(matches_found)
# 	else:
# 		found = 0

# 	return (
# 		current_menu['msg'].format(found),
# 		slots_buttons + current_menu['buttons']
# 	)


# def pickSlot(update, context):
# 	slot_id = update.callback_query.data.lstrip('slot')
# 	context.user_data['slot'] = slot_id
# 	update.callback_query.answer(
# 		texts.match_is_chosen.format(slot_id), show_alert=True)
# 	context.chat_data['history'].pop()
# 	return matchesMain(update, context)


# def getFilterSetting(update, context):
# 	context.chat_data['history'].pop()
# 	filter_type = context.chat_data['history'].pop()
# 	context.user_data[filter_type] = update.callback_query.data
# 	return matchesMain(update, context)


# filter_values_regex = r'^({})$'.format(')|('.join(
# 	filter_value
# 		for filter_type in filter_types
# 			for filter_value in matches_menu['next'][filter_type]['next'].keys()
# ))
callbacks = {
	r'^matches$'		: matchesMain,
	r'^slot_[0-9]+$'	: pickSlot,
	# filter_values_regex	: getFilterSetting,
	# r'^choose_slot$'	: slotsList,
	# r'^slot_[0-9]+$'	: pickSlot
}
