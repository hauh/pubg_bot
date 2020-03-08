from logging import getLogger

from telegram.ext import ConversationHandler, CallbackQueryHandler

import texts
import menu
import database
from buttons import confirm_button

#######################

logger = getLogger(__name__)
slot_settings = ['mode', 'view', 'bet']


def main(update, context, menu):
	# if not context.user_data.get('pubg_id', None)
	# or not context.user_data.get('pubg_username', None):
	# 	update.callback_query.answer(texts.pubg_is_not_set)
	# 	return
	picked_slots = context.user_data.setdefault('picked_slots', set())
	all_slots = context.bot_data.get('slots')
	for expired_slot in picked_slots - set(all_slots):
		picked_slots.discard(expired_slot)
	buttons = [[slot.createButton(leave=True)] for slot in picked_slots]
	if len(picked_slots) < 3:
		buttons += [[slot.createButton()] for slot in all_slots
														if slot not in picked_slots]
	buttons += menu['buttons']
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			matches='\n'.join(str(slot) for slot in picked_slots)
				if picked_slots else menu['default']
		),
		buttons
	)


def pickSlot(update, context, menu):
	slot_to_setup, settings = context.user_data.get('slot_to_setup', (None, None))
	if slot_to_setup and all(settings.values()):
		found_slot = createSlot(update, context, menu)
	else:
		found_slot = None
		picked_slot_id = int(update.callback_query.data.lstrip('slot_'))
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				found_slot = slot
				break

	picked_slots = context.user_data['picked_slots']
	if not found_slot:
		update.callback_query.answer(texts.match_not_found)
	elif found_slot in picked_slots:  # leave game
		picked_slots.remove(found_slot)
		found_slot.leave(update.effective_user.id)
		context.user_data['balance'] = database.updateBalance(
			update.effective_user.id, found_slot.bet)
		update.callback_query.answer(texts.left_from_match, show_alert=True)
	elif len(picked_slots) < 3:  # join game
		if not found_slot.is_set:
			return setupSlot(update, context, menu, found_slot)
		if context.user_data['balance'] < found_slot.bet:
			update.callback_query.answer(texts.insufficient_funds, show_alert=True)
		elif found_slot.is_full:
			update.callback_query.answer(texts.is_full_slot)
		else:
			picked_slots.add(found_slot)
			found_slot.join(update.effective_user.id)
			context.user_data['balance'] = database.updateBalance(
				update.effective_user.id, -found_slot.bet)
			update.callback_query.answer(texts.match_is_chosen, show_alert=True)
	else:
		update.callback_query.answer(texts.maximum_matches)

	context.chat_data['history'].pop()
	return main(update, context, menu)


def setupSlot(update, context, menu, slot=None):
	_, settings = context.user_data.setdefault(
		'slot_to_setup', (slot, dict.fromkeys(slot_settings)))
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			**{
				setting: menu['next'][setting]['next'][chosen_value]['btn']
					if chosen_value else menu['default']
						for setting, chosen_value in settings.items()
			}
		),
		([[confirm_button]] if all(settings.values()) else []) + menu['buttons']
	)


def getSlotSetting(update, context, menu):
	context.chat_data['history'].pop()
	setting = context.chat_data['history'].pop()
	context.user_data['slot_to_setup'][1][setting] = update.callback_query.data
	update.callback_query.data = context.chat_data['history'][-1]
	context.dispatcher.process_update(update)
	return (None, None)


def createSlot(update, context, menu):
	slot, settings = context.user_data.pop('slot_to_setup', (None, None))
	if slot:
		if slot.is_set:
			update.callback_query.answer(texts.match_already_created)
		elif settings and all(settings.values()):
			slot.settings.update(settings)
	return slot
