from logging import getLogger

from telegram.ext import (
	ConversationHandler, CallbackQueryHandler,
	MessageHandler, Filters
)
import texts
import config
import menu
import database
import buttons

#######################

logger = getLogger(__name__)


def main(update, context, menu):
	if update.effective_user.id not in config.admin_id:
		return menu.mainMenu(update, context, menu)  # fix this!
	return (menu['msg'], menu['buttons'])


def switchAdmin(update, context, admin_id, switch):
	if database.updateAdmin(admin_id, switch):
		response = texts.admin_added if switch is True else texts.admin_removed
	else:
		response = texts.admin_update_failed
	update.callback_query.answer(response, show_alert=True)
	context.chat_data['history'].pop()
	return main(update, context, menu)


def addAdmin(update, context, menu):
	validated_input = context.chat_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, validated_input, True)

	user_input = context.chat_data.pop('user_input', None)
	confirm_button = []
	if not user_input:
		message = menu['msg']
	else:
		admin = database.getUser(username=user_input)
		if admin:
			message = menu['input'].format(admin['username'])
			confirm_button = [buttons.createButton(
				texts.confirm, f"confirm_{admin['id']}")]
		else:
			message = menu['input']['msg_error']
	return (message, [confirm_button] + menu['buttons'])


def delAdmin(update, context, menu):
	validated_input = context.chat_data.pop('validated_input', None)
	if validated_input:
		return switchAdmin(update, context, admin_name, False)

	admins = database.getAdmins()
	admins_buttons = []
	admins_list = ""
	for admin in admins:
		admins_buttons.append(
			[buttons.createButton(f"@{admin['username']}", f"remove_{admin['id']}")]
		)
		admins_list += f"@{admin['username']}\n"
	return (menu['msg'].format(admins_list), admins_buttons + menu['buttons'])
