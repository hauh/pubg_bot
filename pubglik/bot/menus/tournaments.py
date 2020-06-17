"""Menu where user creates and picks game slots"""

from pubglik.bot import texts
from pubglik.bot.core import utility

##############################

tournaments_menu = texts.menu['next']['tournaments']
MATCH_SETTINGS = texts.match_settings


def tournaments_main(update, context, menu=tournaments_menu):
	if (not context.user_data.get('pubg_id')
	or not context.user_data.get('pubg_username')):
		update.callback_query.answer(menu['answers']['pubg_required'])
		context.user_data['conversation'].back()
		return (texts.menu['msg'], texts.menu['buttons'])

	picked_slots = context.user_data.setdefault('picked_slots', set())
	slots_buttons = []
	for slot in picked_slots:
		if not slot.is_ready:
			slots_buttons.append(utility.button(
				f'slot_{slot.slot_id}',
				f"{slot.time.strftime('%H:%M')} - {texts.leave_slot}"
			))
	if len(picked_slots) < 3:
		for slot in context.bot_data.get('slots', []):
			if slot not in picked_slots and not slot.is_full:
				if not slot.is_set:
					btn_text = f"{slot.time.strftime('%H:%M')} - {texts.free_slot}"
				else:
					btn_text = str(slot)
				slots_buttons.append(utility.button(f'slot_{slot.slot_id}', btn_text))
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			tournaments='\n'.join(str(slot) for slot in picked_slots)
				if picked_slots else menu['default']
		),
		slots_buttons + menu['buttons']
	)


def pick_slot(update, context, menu):
	def done(answer):
		update.callback_query.answer(menu['answers'][answer], show_alert=True)
		context.user_data['conversation'].back()
		return tournaments_main(update, context)

	def find_slot():
		slot_button = context.user_data['conversation'].repeat()
		picked_slot_id = int(slot_button.split('_')[-1])
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				return slot
		return None

	if not (slot := find_slot()):
		return done('not_found')

	# setup slot if confirmed
	if context.user_data.pop('validated_input', None):
		settings = context.user_data.pop('slot_settings', None)
		if slot.is_set:
			return done('already_set')
		if settings and all(settings.values()):
			slot.update_settings(settings)

	# leave if already joined
	if slot in context.user_data['picked_slots']:
		if slot.is_ready:
			return done('too_late')
		context.user_data['picked_slots'].remove(slot)
		bet = slot.bet
		slot.leave(update.effective_user.id)
		context.user_data['balance'] += bet
		return done('left')

	# maximum 3 slots
	if len(context.user_data['picked_slots']) >= 3:
		return done('maximum')

	# setup first
	if not slot.is_set:
		return setup_slot(update, context)

	# slot is full
	if slot.is_full:
		return done('full')

	# not enough money
	if context.user_data['balance'] < slot.bet:
		return done('expensive')

	# finally you can join
	context.user_data['balance'] -= slot.bet
	slot.join(update.effective_user.id)
	context.user_data['picked_slots'].add(slot)
	return done('joined')


def setup_slot(update, context, menu=tournaments_menu['next']['slot_']):
	settings = context.user_data.setdefault(
		'slot_settings', dict.fromkeys(['type', 'mode', 'view', 'bet'], None))
	answer = menu['msg'].format(
		balance=context.user_data['balance'],
		**{
			setting: MATCH_SETTINGS[setting][chosen_value]['full']
				if chosen_value else menu['default']
				for setting, chosen_value in settings.items()
		}
	)
	if not all(settings.values()):
		return (answer, menu['buttons'])
	return (answer, [utility.confirm_button('slot_setup')] + menu['buttons'])


def get_slot_setting(update, context, menu):
	conv = context.user_data['conversation']
	context.user_data['slot_settings'][conv.back()] = update.callback_query.data
	conv.back()
	return setup_slot(update, context)


##############################

def add_callbacks():
	tournaments_menu['callback'] = tournaments_main
	tournaments_menu['next']['slot_']['callback'] = pick_slot
	for setting_menu in tournaments_menu['next']['slot_']['next'].values():
		for setting_choice in setting_menu['next'].values():
			setting_choice['callback'] = get_slot_setting
