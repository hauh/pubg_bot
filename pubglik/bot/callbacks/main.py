"""Conversation starts here"""

from pubglik import config, database

##############################


def start(state, conversation, context):
	# checking who's there
	username = conversation.update.effective_user.username
	if not (user := database.get_user(conversation.user_id)):
		user = database.save_user(conversation.user_id, username)
		user['balance'] = 0
		user['games_played'] = 0
	if user['banned']:
		conversation.banned = True
		return conversation.reply(state.texts['banned'])

	# updating data if changed
	if user['username'] != username:
		database.update_user(conversation.user_id, username=username)
		user['username'] = username
	if not user['admin'] and conversation.user_id in config.admin_id:
		database.update_user(conversation.user_id, admin=True)
		user['admin'] = True
	context.user_data.update(user)

	# building appropriate reply
	buttons = [state.extra['chat']]
	if user['admin']:
		buttons.append(state.extra['admin'])
	if user['pubg_username']:
		text = state.texts['registered'].format(
			user['pubg_username'], user['balance'], user['games_played'])
	else:
		text = state.texts['unregistered']
	return conversation.reply(text, extra_buttons=buttons)
