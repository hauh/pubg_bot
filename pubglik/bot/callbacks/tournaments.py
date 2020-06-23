"""Menu where user creates and picks game slots"""

GAME_SETTINGS = ['type', 'mode', 'view', 'bet']


def main(conversation, context):
	# pubg_id and pubg_username required
	if (not context.user_data.get('pubg_id')
	or not context.user_data.get('pubg_username')):
		conversation.set_answer(conversation.state.answers['pubg_required'])
		return conversation.back(context)

	conversation.context = None
	picked_slots = context.user_data.setdefault('picked_slots', set())

	# button to leave already joined slots
	for slot in picked_slots:
		if not slot.is_ready:
			conversation.add_button(conversation.state.extra['leave_slot'](
				dict(slot_time=slot.time.strftime('%H:%M')), slot.slot_id))

	# buttons to create or join opened slots
	if len(picked_slots) < 3:
		for slot in context.bot_data.get('slots', []):
			if slot not in picked_slots and not slot.is_full:
				if not slot.is_set:
					conversation.add_button(conversation.state.extra['create_slot'](
						dict(slot_time=slot.time.strftime('%H:%M')), slot.slot_id))
				else:
					conversation.add_button(conversation.state.extra['join_slot'](
						dict(slot=str(slot)), slot.slot_id))
	return conversation.reply(
		conversation.state.texts['rules'].format(context.user_data['balance'])
		+ "" if not picked_slots else conversation.state.texts['picked'].format(
			'\n'.join(str(slot) for slot in picked_slots))
	)


def pick_slot(conversation, context):
	def done(answer):
		conversation.set_answer(conversation.state.answers[answer])
		conversation.context = None
		return conversation.back(context)

	def find_slot():
		picked_slot_id = conversation.context['slot_id']
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				return slot
		return None

	if not conversation.context:
		conversation.context = {'slot_id': int(conversation.data)}

	if not (slot := find_slot()):
		return done('not_found')

	# setup slot if confirmed
	if conversation.confirmed:
		settings = conversation.context.pop('settings')
		conversation.confirmed = False
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
		slot.leave(conversation.user_id)
		context.user_data['balance'] += bet
		return done('left')

	# maximum 3 slots
	if len(context.user_data['picked_slots']) >= 3:
		return done('maximum')

	# try to join if slot is set
	if slot.is_set:

		if slot.is_full:
			return done('full')

		if context.user_data['balance'] < slot.bet:
			return done('expensive')

		context.user_data['balance'] -= slot.bet
		slot.join(conversation.user_id)
		context.user_data['picked_slots'].add(slot)
		return done('joined')

	# else setup first
	text = conversation.state.texts['create'].format(context.user_data['balance'])
	if not (settings := conversation.context.get('settings')):
		conversation.context['settings'] = dict.fromkeys(GAME_SETTINGS, None)
	else:
		for setting in GAME_SETTINGS:
			if setting_value := settings.get(setting):
				text += conversation.state.texts[setting].format(
					conversation.state.next[setting]
					.next[f'{setting};{setting_value}'].button[0].text
				)
		if all(settings.values()):
			conversation.add_button(conversation.state.confirm_button('settings'))
	return conversation.reply(text)


def get_slot_setting(conversation, context):
	if not conversation.data:
		return conversation.reply(conversation.state.texts)
	conversation.context['settings'][conversation.state.key] = conversation.data
	return conversation.back(context)
