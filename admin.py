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
ADMIN_MENU, ADMINISTRATE, GET_ADMIN, CONFIRM, REMOVE_ADMIN = range(0, 5)
admin_menu = texts.menu['next']['admin']


def adminMain(update, context):
	if update.effective_user.id not in config.admin_id:
		return menu.mainMenu(update, context)
	if 'add_to_admins' in context.chat_data:
		del context.chat_data['add_to_admins']
	menu.sendMessage(
		update, context,
		admin_menu['msg'],
		admin_menu['buttons'],
		'admin'
	)
	return ADMIN_MENU


def adminMenu(update, context):
	what_to_administrate = update.callback_query.data
	current_menu = admin_menu['next'][what_to_administrate]
	menu.sendMessage(
		update, context,
		current_menu['msg'],
		current_menu['buttons'],
		what_to_administrate
	)
	return ADMINISTRATE


def askNewAdminUsername(update, context, repeat=False):
	current_menu = admin_menu['next']['manage_admins']['next']['add_admin']
	menu.sendMessage(
		update, context,
		current_menu['msg'] if not repeat else current_menu['msg_with_error'],
		current_menu['buttons'][1:],
		'add_admin'
	)
	return GET_ADMIN


def getAdmin(update, context):
	current_menu = admin_menu['next']['manage_admins']['next']['add_admin']
	admin = database.getUser(username=update.effective_message.text)
	update.effective_message.delete()
	if not admin:
		return askNewAdminUsername(update, context, True)
	menu.sendMessage(
		update, context,
		current_menu['msg_with_value'].format(admin['username']),
		current_menu['buttons'],
	)
	context.chat_data['add_to_admins'] = admin['id']
	return CONFIRM


def addAdmin(update, context):
	if database.updateAdmin(context.chat_data['add_to_admins'], True):
		response = texts.admin_added
	else:
		response = texts.admin_failed
	update.callback_query.answer(response, show_alert=True)
	del context.chat_data['add_to_admins']
	context.chat_data['history'].pop()
	return adminMain(update, context)


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
	menu.sendMessage(
		update, context,
		current_menu['msg'].format(admins_list),
		admins_buttons + current_menu['buttons'],
		'remove_admin'
	)
	return REMOVE_ADMIN


def removeAdmin(update, context):
	admin_name = update.callback_query.data.lstrip('remove_')
	if database.updateAdmin(admin_name, False):
		response = texts.admin_removed
	else:
		response = texts.admin_failed
	update.callback_query.answer(response, show_alert=True)
	context.chat_data['history'].pop()
	return adminMain(update, context)


def back(update, context):
	last_state = context.chat_data['history'][-1]
	if last_state == 'add_admin' or last_state == 'remove_admin':
		context.chat_data['history'].pop()
		update.callback_query.data = context.chat_data['history'][-1]
		return adminMenu(update, context)
	return menu.back(update, context)


handler = ConversationHandler(
	entry_points=[
		CallbackQueryHandler(adminMain, pattern=r'^admin$')
	],
	states={
		ADMIN_MENU: [
			CallbackQueryHandler(
				adminMenu,
				pattern=r'^({})$'.format(')|('.join(admin_menu['next'].keys()))
			)
		],
		ADMINISTRATE: [
			CallbackQueryHandler(askNewAdminUsername, pattern=r'^add_admin$'),
			CallbackQueryHandler(listAdmins, pattern=r'^remove_admin$'),
		],
		GET_ADMIN: [
			MessageHandler(Filters.text, getAdmin)
		],
		CONFIRM: [
			CallbackQueryHandler(addAdmin, pattern=r'^confirm$')
		],
		REMOVE_ADMIN: [
			CallbackQueryHandler(removeAdmin, pattern=r'^remove_[0-9]+$')
		]
	},
	fallbacks=[
		CallbackQueryHandler(back, pattern=r'^back$')
	],
	allow_reentry=True
)
