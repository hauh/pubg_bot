from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import database

#######################

logger = getLogger(__name__)
slot_settings = ['mode', 'view', 'bet']


def mainMatches(update, context, menu):
	# if not context.user_data.get('pubg_id', None)
	# or not context.user_data.get('pubg_username', None):
	# 	update.callback_query.answer(texts.pubg_is_not_set)
	# 	return
	picked = context.user_data.setdefault('picked_slots', set())
	all_slots = context.bot_data.get('slots')
	for expired_slot in picked - set(all_slots):
		picked_slots.discard(expired_slot)
	buttons = [slot.createButton(leave=True) for slot in picked]
	if len(picked) < 3:
		buttons += [slot.createButton() for slot in all_slots if slot not in picked]
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			matches='\n'.join(str(slot) for slot in picked)
				if picked else menu['default']
		),
		buttons + menu['buttons']
	)


def slotMenu(update, context, menu):
	found_slot, settings = context.user_data.get('slot_to_setup', (None, None))

	if found_slot:
		if found_slot.is_set:
			update.callback_query.answer(texts.match_already_created)
			del context.user_data['history'][-1:]
			return mainMatches(update, context, texts.menu['next']['matches'])
		if all(settings.values()):
			found_slot.settings.update(settings)
			context.user_data.pop('slot_to_setup')
		else:
			return setupSlot(update, context, menu, found_slot)
	else:
		picked_slot_id = int(update.callback_query.data.lstrip('slot_'))
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				found_slot = slot
				break

	if not found_slot:
		update.callback_query.answer(texts.match_not_found)
	elif found_slot in context.user_data['picked_slots']:
		leaveSlot(update, context, slot)
	elif len(context.user_data['picked_slots']) < 3:
		if not slot.is_set:
			return setupSlot(update, context, menu, slot)
		pickSlot(update, context, found_slot)
	else:
		update.callback_query.answer(texts.maximum_matches)
	del context.user_data['history'][-1:]
	return mainMatches(update, context, texts.menu['next']['matches'])


def pickSlot(update, context, slot):
	if context.user_data['balance'] < slot.bet:
		update.callback_query.answer(texts.insufficient_funds, show_alert=True)
	elif slot.is_full:
		update.callback_query.answer(texts.is_full_slot)
	else:
		ontext.user_data['picked_slots'].add(slot)
		slot.join(update.effective_user.id)
		context.user_data['balance'] = database.updateBalance(
			update.effective_user.id, -slot.bet)
		update.callback_query.answer(texts.match_is_chosen, show_alert=True)


def leaveSlot(update, context, slot):
	context.user_data['picked_slots'].remove(slot)
	slot.leave(update.effective_user.id)
	context.user_data['balance'] =\
		database.updateBalance(update.effective_user.id, slot.bet)
	update.callback_query.answer(texts.left_from_match, show_alert=True)


def getSlotSetting(update, context, menu):
	setting = context.user_data['history'][-2]
	context.user_data['slot_to_setup'][1][setting] = update.callback_query.data
	del context.user_data['history'][-2:]
	return setupSlot(update, context, texts.main['next']['matches']['slot_'])


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
		([[InlineKeyboardButton(texts.confirm, 'confirm')]]
			if all(settings.values()) else []) + menu['buttons']
	)
