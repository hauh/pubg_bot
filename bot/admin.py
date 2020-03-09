from logging import getLogger

from telegram import InlineKeyboardButton

import texts
import config
import database
import main_menu

#######################

logger = getLogger(__name__)


def mainAdmin(update, context, menu):
	if not context.user_data['admin']\
		or update.effective_user.id not in config.admin_id:
		return main_menu.start(update, context)
	return (menu['msg'], menu['buttons'])


def switchAdmin(update, context, admin_id, switch):
	if database.updateAdmin(admin_id, switch):
		answer = texts.admin_added if switch is True else texts.admin_removed
	else:
		answer = texts.admin_update_failed
	update.callback_query.answer(answer, show_alert=True)
	del context.user_data['history'][-2:]
	return mainAdmin(update, context, texts.menu['next']['admin'])


def addAdmin(update, context, menu):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, validated_input, True)

	user_input = context.user_data.pop('user_input', None)
	confirm_button = []
	if not user_input:
		message = menu['msg']
	else:
		admin = database.getUser(username=user_input)
		if admin:
			message = menu['input']['msg_valid'].format(admin['username'])
			confirm_button = [InlineKeyboardButton(
				texts.confirm, callback_data=f"confirm_{admin['id']}")]
		else:
			message = menu['input']['msg_error']
	return (message, [confirm_button] + menu['buttons'])


def delAdmin(update, context, menu):
	validated_input = context.user_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, validated_input, False)

	admins = database.getAdmins()
	admins_buttons = []
	admins_list = ""
	for admin in admins:
		admins_buttons.append([InlineKeyboardButton(
			f"@{admin['username']}", callback_data=f"confirm_{admin['id']}")])
		admins_list += f"@{admin['username']}\n"
	return (menu['msg'].format(admins_list), admins_buttons + menu['buttons'])
