import texts
import utility

##############################

matches_menu = texts.menu['next']['matches']


def matches_main(update, context, menu=matches_menu):
	if (not context.user_data.get('pubg_id')
	or not context.user_data.get('pubg_username')):
		update.callback_query.answer(menu['answers']['pubg_required'])
		del context.user_data['history'][-1]
		return (None,)

	picked_slots = context.user_data.setdefault('picked_slots', set())
	all_slots = context.bot_data.get('slots')
	for expired_slot in picked_slots - set(all_slots):
		picked_slots.discard(expired_slot)
	slots_buttons = []
	for slot in picked_slots:
		slots_buttons.append(utility.create_button(
			f"{slot.time.strftime('%H:%M')} - {texts.leave_slot}",
			f'slot_{slot.slot_id}'
		))
	if len(picked_slots) < 3:
		for slot in all_slots:
			if not slot.players:
				text = f"{slot.time.strftime('%H:%M')} - {texts.free_slot}"
			elif slot.is_full:
				text = f"{slot.time.strftime('%H:%M')} - {texts.full_slot}"
			else:
				text = str(slot)
			slots_buttons.append(utility.create_button(
				text, f'slot_{slot.slot_id}'))
	return (
		menu['msg'].format(
			balance=context.user_data['balance'],
			matches='\n'.join(str(slot) for slot in picked_slots)
				if picked else menu['default']
		),
		*slots_buttons
	)


def pick_slot(update, context, menu):
	def done(answer):
		update.callback_query.answer(menu['answers'][answer], show_alert=True)
		del context.user_data['history'][-1]
		return matches_main(update, context)

	def find_slot():
		slot_id = int(context.user_data['history'][-1].lstrip('slot_'))
		for slot in context.bot_data['slots']:
			if slot.slot_id == slot_id:
				return slot
		return None

	if not (slot := find_slot()):
		return done('not_found')

	# setup slot if confirmed
	if context.user_data.pop('validated_input', None):
		settings = context.user_data.pop('slot_settings', None)
		if slot.is_set:
			return done('already_set')
		elif settings and all(settings.values()):
			slot.update_settings(settings)

	# leave if already joined
	if slot in context.user_data['picked_slots']:
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


def setup_slot(update, context, menu=matches_menu['next']['slot_']):
	settings = context.user_data.setdefault(
		'slot_settings', dict.fromkeys(['type', 'mode', 'view', 'bet'], None))
	answer = menu['msg'].format(
		balance=context.user_data['balance'],
		**{
			setting: menu['next'][setting]['next'][chosen_value]['btn']
				if chosen_value else menu['default']
				for setting, chosen_value in settings.items()
		}
	)
	if not all(settings.values()):
		return (answer,)
	return (answer, utility.confirm_button('slot_setup'))


def get_slot_setting(update, context, menu):
	history = context.user_data.get('history')
	context.user_data['slot_settings'][history[-2]] = history[-1]
	del history[-2:]
	return setup_slot(update, context)


##############################

matches_menu['callback'] = matches_main
matches_menu['next']['slot_']['callback'] = pick_slot
for setting_menu in matches_menu['next']['slot_']['next'].values():
	for setting_choice in setting_menu['next'].values():
		setting_choice['callback'] = get_slot_setting
