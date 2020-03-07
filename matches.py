from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
from buttons import confirm_button

#######################

logger = getLogger(__name__)
matches_menu = texts.menu['next']['matches']
slot_settings = ['mode', 'view', 'bet']


def matchesMain(update, context):
	picked_slots = context.user_data.setdefault('picked_slots', set())
	all_slots = context.bot_data.get('slots')
	for expired_slot in picked_slots - set(all_slots):
		picked_slots.discard(expired_slot)
	buttons = [[slot.createButton(leave=True)] for slot in picked_slots]
	if len(picked_slots) < 3:
		buttons += [[slot.createButton()] for slot in all_slots
														if slot not in picked_slots]
	buttons += matches_menu['buttons']
	return (
		matches_menu['msg'].format(
			matches_menu['default'] if not picked_slots
				else '\n'.join(str(slot) for slot in picked_slots)
		),
		buttons
	)


def pickSlot(update, context):
	picked_slots = context.user_data['picked_slots']

	slot_to_setup, settings = context.user_data.get('slot_to_setup', (None, None))
	if slot_to_setup and all(settings.values()):
		found_slot = createSlot(update, context)
	else:
		found_slot = None
		picked_slot_id = int(update.callback_query.data.lstrip('slot_'))
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				found_slot = slot
				break

	if not found_slot:
		update.callback_query.answer(texts.match_not_found)
	elif found_slot in picked_slots:
		picked_slots.remove(found_slot)
		found_slot.leave(update.effective_user.id)
		update.callback_query.answer(texts.left_from_match)
	elif len(picked_slots) < 3:
		if not found_slot.isSet():
			return setupSlot(update, context, found_slot)
		picked_slots.add(found_slot)
		found_slot.join(update.effective_user.id)
		update.callback_query.answer(texts.match_is_chosen)
	else:
		update.callback_query.answer(texts.maximum_matches)

	context.chat_data['history'].pop()
	return matchesMain(update, context)


def setupSlot(update, context, slot=None):
	chosen_settings = context.user_data.setdefault(
		'slot_to_setup', (slot, dict.fromkeys(slot_settings)))[1]
	current_menu = matches_menu['next']['slot_']
	return (
		current_menu['msg'].format(**{
			setting: current_menu['next'][setting]['next'][chosen_value]['btn']
				if chosen_value else current_menu['default']
					for setting, chosen_value in chosen_settings.items()
		}),
		([[confirm_button]] if all(chosen_settings.values())
			else []) + current_menu['buttons']
	)


def getSlotSetting(update, context):
	context.chat_data['history'].pop()
	setting = context.chat_data['history'].pop()
	context.user_data['slot_to_setup'][1][setting] = update.callback_query.data
	return setupSlot(update, context)


def createSlot(update, context):
	slot, settings = context.user_data.pop('slot_to_setup', (None, None))
	if slot:
		if slot.isSet():
			update.callback_query.answer(texts.match_already_created)
		elif settings and all(settings.values()):
			slot.settings.update(settings)
	return slot


slot_settings_regex = r'^({})$'.format(')|('.join(
	slot_setting for setting_type in slot_settings for slot_setting
		in matches_menu['next']['slot_']['next'][setting_type]['next'].keys()
))
callbacks = {
	r'^matches$'		: matchesMain,
	r'^slot_[0-9]+$'	: pickSlot,
	slot_settings_regex	: getSlotSetting,
}
