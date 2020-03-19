from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import database

#######################

logger = getLogger(__name__)
matches_menu = texts.menu['next']['matches']


def mainMatches(update, context, menu=matches_menu):
	if not context.user_data.get('pubg_id')\
		or not context.user_data.get('pubg_username'):
		update.callback_query.answer(texts.pubg_is_not_set)
		return (None, None)

	picked = context.user_data.setdefault('picked_slots', set())
	all_slots = context.bot_data.get('slots')
	for expired_slot in picked - set(all_slots):
		picked.discard(expired_slot)
	buttons = [slot.create_button(leave=True) for slot in picked]
	if len(picked) < 3:
		buttons += [slot.create_button() for slot in all_slots if slot not in picked]
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			matches='\n'.join(str(slot) for slot in picked)
				if picked else menu['default']
		),
		buttons + menu['buttons']
	)


def slotMenu(update, context, menu):
	slot = findSlot(context)

	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		settings = context.user_data.pop('slot_settings')
		if all(settings.values()):
			slot.settings.update(settings)

	if not slot:
		answer = texts.match_not_found
	elif slot in context.user_data['picked_slots']:
		answer = leaveSlot(update.effective_user.id, context.user_data, slot)
	elif len(context.user_data['picked_slots']) < 3:
		if not slot.is_set:
			return setupSlot(update, context, menu)
		answer = pickSlot(update.effective_user.id, context.user_data, slot)
	else:
		answer = texts.maximum_matches

	update.callback_query.answer(answer, show_alert=True)
	del context.user_data['history'][-1:]
	return mainMatches(update, context)


def findSlot(context):
	picked_slot_id = int(context.user_data['history'][-1].lstrip('slot_'))
	for slot in context.bot_data['slots']:
		if slot.slot_id == picked_slot_id:
			return slot
	return None


def leaveSlot(user_id, user_data, slot):
	user_data['picked_slots'].remove(slot)
	user_data['balance'] = database.updateBalance(user_id, slot.bet)
	slot.leave(user_id)
	return texts.left_from_match


def pickSlot(user_id, user_data, slot):
	if user_data['balance'] < slot.bet:
		return texts.insufficient_funds
	if slot.is_full:
		return texts.is_full_slot
	user_data['picked_slots'].add(slot)
	user_data['balance'] = database.updateBalance(user_id, -slot.bet)
	slot.join(user_id)
	return texts.match_is_chosen


def setupSlot(update, context, menu):
	settings = context.user_data.setdefault(
		'slot_settings', dict.fromkeys(matches_menu['next']['slot_']['next'].keys()))
	if all(settings.values()):
		confirm_button = [InlineKeyboardButton(
			texts.confirm, callback_data='confirm_slot_setup')]
	else:
		confirm_button = []
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			**{
				setting: menu['next'][setting]['next'][chosen_value]['btn']
					if chosen_value else menu['default']
						for setting, chosen_value in settings.items()
			}
		),
		[confirm_button] + menu['buttons']
	)


def getSlotSetting(update, context, menu):
	setting = context.user_data['history'][-2]
	context.user_data['slot_settings'][setting] = update.callback_query.data
	del context.user_data['history'][-2:]
	return setupSlot(
		update, context, texts.menu['next']['matches']['next']['slot_'])
