from logging import getLogger

import config
import database
import texts

########################

logger = getLogger(__name__)


def start(update, context, menu=texts.menu):
	user_id = int(update.effective_user.id)
	user = database.getUser(user_id)
	if not user or user['username'] != update.effective_user.username:
		database.saveUser(user_id, update.effective_user.username)
		user = database.getUser(user_id)
	context.user_data.update(user)
	admin_button = 0 if user['admin'] or user_id in config.admin_id else 1
	return (menu['msg'], menu['buttons'][admin_button:])
