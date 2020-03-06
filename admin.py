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
admin_menu = texts.menu['next']['admin']


def adminMain(update, context):
	if update.effective_user.id not in config.admin_id:
		return menu.mainMenu(update, context)
	return (admin_menu['msg'], admin_menu['buttons'])


def addAdmin(update, context):
	validated_input = context.chat_data.pop('validated_input', None)
	if validated_input:
		if database.updateAdmin(validated_input, True):
			response = texts.admin_added
		else:
			response = texts.admin_update_failed
		update.callback_query.answer(response, show_alert=True)
		context.chat_data['history'].pop()
		return adminMain(update, context)

	current_menu = admin_menu['next']['manage_admins']['next']['add_admin']
	user_input = context.chat_data.pop('user_input', None)
	confirm_button = []
	if not user_input:
		message = current_menu['msg']
	else:
		admin = database.getUser(username=user_input)
		if admin:
			message = current_menu['input']['msg_valid'].format(admin['username'])
			confirm_button = [buttons.createButton(
				texts.confirm, f"confirm_{admin['id']}")]
		else:
			message = current_menu['input']['msg_error']
	if not update.callback_query and update.effective_message.text:
		return validateAndConfirm(update, context, current_menu)
	return (message, [confirm_button] + current_menu['buttons'])


def listAdmins(update, context):
	current_menu = admin_menu['next']['manage_admins']['next']['remove_admin']
	admins = database.getAdmins()
	admins_buttons = []
	admins_list = ""
	for admin in admins:
		admins_buttons.append(
			[buttons.createButton(f"@{admin['username']}", f"remove_{admin['id']}")]
		)
		admins_list += f"@{admin['username']}\n"
	return (
		current_menu['msg'].format(admins_list),
		admins_buttons + current_menu['buttons'],
	)


def removeAdmin(update, context):
	admin_name = update.callback_query.data.lstrip('remove_')
	if database.updateAdmin(admin_name, False):
		response = texts.admin_removed
	else:
		response = texts.admin_update_failed
	update.callback_query.answer(response, show_alert=True)
	context.chat_data['history'].pop()
	return adminMain(update, context)


callbacks = {
	r'^admin$'			: adminMain,
	r'^add_admin$'		: addAdmin,
	r'^remove_admin$'	: listAdmins,
	r'^remove_[0-9]+$'	: removeAdmin,
}
