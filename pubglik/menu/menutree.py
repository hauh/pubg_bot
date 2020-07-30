"""Structure of all menus."""

from pubglik import config

##############################

menu_tree = {
	'admin': {
		'manage_tournaments': {
			'set_room': {},
			'set_winners': {
				'generate_table': {}
			},
		},
		'manage_admins': {
			'add_admin': {},
			'revoke_admin': {}
		},
		'manage_users': {
			'change_balance': {},
			'ban_user': {},
			'unban_user': {},
		},
		'mailing': {},
		'bot_settings': {
			'debug_mode': {}
		},
	},
	'tournaments': {
		'slot': {
			'type': {
				'type;survival_easy': {},
				'type;survival_medium': {},
				'type;survival_hard': {},
				'type;kills': {},
				'type;mixed': {},
			},
			'mode': {
				'mode;solo': {},
				'mode;dual': {},
				'mode;squad': {},
				'mode;payload': {},
				'mode;zombie': {},
			},
			'view': {
				'view;1st': {},
				'view;3rd': {},
			},
			'bet': {
				f'bet;{bet}': {} for bet in config.bets
			}
		}
	},
	'cabinet': {
		'set_pubg_username': {},
		'set_pubg_id': {},
		'add_funds': {},
		'withdraw_money': {
			'provider': {
				'provider;card': {},
				'provider;mc': {},
				'provider;yandex': {},
				'provider;qiwi': {},
				'provider;webmoney': {},
			},
			'account': {},
			'amount': {}
		},
		'balance_history': {}
	},
	'how': {
		'usage': {},
		'prize_structure': {},
		'rules': {}
	},
	'contacts': {},
}
