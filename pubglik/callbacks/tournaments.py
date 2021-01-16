"""Menu where user creates and picks game slots"""


def main(state, conversation, context):
	# pubg_id and pubg_username required
	if (not context.user_data.get('pubg_id')
	or not context.user_data.get('pubg_username')):
		return conversation.back(context, answer='pubg_required')

	text = state.texts['rules'].format(context.user_data['balance'])
	slot_buttons = []

	# buttons to leave already joined slots
	if joined_slots := context.user_data.setdefault('joined_slots', set()):
		text += state.texts['picked']
		for slot in joined_slots:
			if not slot.is_ready:
				slot_buttons.append(state.extra['leave_slot'](slot))
			text += '\n' + str(slot)

	# buttons to create or join opened slots
	if len(joined_slots) < 3:
		for slot in context.bot_data.get('slots', []):
			if slot not in joined_slots and not slot.is_full:
				slot_buttons.append(
					state.extra['join_slot' if slot.is_set else 'create_slot'](slot))

	return conversation.reply(text, extra_buttons=slot_buttons)


def pick_slot(state, conversation, context):
	def find_slot():
		picked_slot_id =\
			context.user_data.pop('slot_to_setup', None) or int(conversation.input)
		for slot in context.bot_data['slots']:
			if slot.slot_id == picked_slot_id:
				return slot
		return None

	if not (slot := find_slot()):
		return conversation.back(context, answer='not_found')

	# setup slot if confirmed
	if conversation.confirmed:
		if slot.is_set:
			return conversation.back(context, answer='already_set')

		settings = context.user_data.get('slot_settings')
		if settings and all(settings.values()):
			slot.update_settings(settings)

	# leave if already joined
	if slot in context.user_data['joined_slots']:
		if slot.is_ready:
			return conversation.back(context, answer='too_late')

		context.user_data['joined_slots'].remove(slot)
		bet = slot.bet
		slot.leave(conversation.user_id)
		context.user_data['balance'] += bet
		return conversation.back(context, answer='left')

	# maximum 3 slots
	if len(context.user_data['joined_slots']) >= 3:
		return conversation.back(context, answer='maximum')

	# try to join if slot is set
	if slot.is_set:
		if slot.is_full:
			return conversation.back(context, answer='full')

		if context.user_data['balance'] < slot.bet:
			return conversation.back(context, answer='expensive')

		context.user_data['balance'] -= slot.bet
		slot.join(conversation.user_id)
		context.user_data['joined_slots'].add(slot)
		return conversation.back(context, answer='joined')

	# else setup first
	context.user_data['slot_to_setup'] = slot.slot_id
	text = state.texts['create'].format(context.user_data['balance'])
	settings = context.user_data.setdefault(
		'slot_settings', dict.fromkeys(['type', 'mode', 'view', 'bet']))
	for setting, setting_value in settings.items():
		if setting_value:
			for button in state.next[setting].buttons:
				if button[0].callback_data == f'{setting};{setting_value}':
					text += state.texts[setting].format(button[0].text)
					break
	return conversation.reply(
		text, confirm=slot.slot_id if all(settings.values()) else None)


def get_slot_setting(state, conversation, context):
	if not conversation.input:
		return conversation.reply()

	context.user_data['slot_settings'][state.key] = conversation.input
	return conversation.back(context)
