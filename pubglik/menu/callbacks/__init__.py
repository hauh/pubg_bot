"""Callbacks for conversation with user"""

from . import main
from . import admin
from . import cabinet
from . import tournaments

##############################

callbacks = {
	# ########## main ########## #
	'_main_': main.start,

	# ########## admin ########## #
	'admin': admin.main,
	'manage_tournaments': admin.manage_tournaments,
	'set_room': admin.set_room,
	'set_winners': admin.set_winners,
	'generate_table': admin.generate_table,
	'add_admin': admin.add_admin,
	'revoke_admin': admin.revoke_admin,
	'manage_users': admin.manage_users,
	'change_balance': admin.change_balance,
	'ban_user': admin.ban_user,
	'unban_user': admin.unban_user,
	'mailing': admin.mailing,
	'bot_settings': admin.bot_settings,
	'debug_mode': admin.debug_mode,

	# ########## tournaments ########## #
	'tournaments': tournaments.main,
	'slot': tournaments.pick_slot,
	'type': tournaments.get_slot_setting,
	'mode': tournaments.get_slot_setting,
	'view': tournaments.get_slot_setting,
	'bet': tournaments.get_slot_setting,

	# ########## cabinet ########## #
	'cabinet': cabinet.main,
	'set_pubg_username': cabinet.set_pubg_username,
	'set_pubg_id': cabinet.set_pubg_id,
	'add_funds': cabinet.add_funds,
	'withdraw_money': cabinet.withdraw_money,
	'provider': cabinet.set_withdrawal_provider,
	'account': cabinet.set_withdrawal_account,
	'amount': cabinet.set_withdrawal_amount,
	'balance_history': cabinet.balance_history
}
