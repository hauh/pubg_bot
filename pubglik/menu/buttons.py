"""Buttons for users to pick next action."""

from pubglik import config
from telegram import InlineKeyboardButton

##############################

buttons = {
	menu_key: [InlineKeyboardButton(button_text, callback_data=menu_key)]
		for menu_key, button_text in
{  # noqa
	# ########### main ########## #
	'_main_': "В главное меню",
	'how': "Как это работает?",
	'usage': "Как пользоваться сервисом",
	'prize_structure': "Структура призов",
	'rules': "Правила",
	'contacts': "Контакты",

	# ########## admin ########## #
	'manage_tournaments': "Турниры",
	'generate_table': "Сгенерировать таблицу игроков",
	'manage_admins': "Администраторы",
	'add_admin': "Добавить администратора",
	'revoke_admin': "Удалить администратора",
	'manage_users': "Пользователи",
	'mailing': "Рассылка сообщений",
	'bot_settings': "Настройки бота",

	# ########## tournaments ########## #
	'tournaments': "График турниров",
	'type': "Выбрать тип",
	'type;survival_easy': "Выживание (лёгкий)",
	'type;survival_medium': "Выживание (средний)",
	'type;survival_hard': "Выживание (тяжёлый)",
	'type;kills': "Убийства",
	'type;mixed': "Смешанный",
	'mode': "Выбрать режим",
	'mode;solo': "SOLO",
	'mode;dual': "DUAL",
	'mode;squad': "SQUAD",
	'mode;payload': "Payload",
	'mode;zombie': "Zombie",
	'view': "Выбрать обзор",
	'view;1st': "От первого лица",
	'view;3rd': "От третьего лица",
	'bet': "Выбрать ставку",
	**{f'bet;{bet}': str(bet) for bet in config.bets},

	# ########## cabinet ########## #
	'cabinet': "Личный кабинет",
	'set_pubg_username': "Установить ник PUBG",
	'set_pubg_id': "Установить ID PUBG",
	'add_funds': "Пополнить баланс",
	'withdraw_money': "Вывести средства",
	'provider': "Выбрать способ вывода",
	'provider;card': "Банковская карта",
	'provider;mc': "Мобильный платёж",
	'provider;yandex': "Яндекс.Деньги",
	'provider;qiwi': "QIWI-кошелёк",
	'provider;webmoney': "WebMoney",
	'account': "Ввести кошелёк/карту",
	'amount': "Ввести сумму вывода",
	'balance_history': "Посмотреть историю операций",
}.items()}

optional_buttons = {
	'_back_': [InlineKeyboardButton("Назад", callback_data='_back_')],
	'_confirm_': lambda value: [InlineKeyboardButton(
		"✔ Подтвердить", callback_data=f'_confirm_;{value}')],
	'_main_': {
		'admin': [InlineKeyboardButton("Управление", callback_data='admin')],
		'chat': [InlineKeyboardButton("Боевой чат", url=config.battle_chat)]
	},
	'revoke_admin': {
		'revoke': lambda admin_id, admin_username: [InlineKeyboardButton(
			f"@{admin_username}", callback_data=f'_confirm_;{admin_id}')],
	},
	'manage_users': {
		'change_balance': [InlineKeyboardButton(
			"Изменить баланс", callback_data='change_balance')],
		'unban_user': [InlineKeyboardButton(
			"Разбанить", callback_data='unban_user')],
		'ban_user': [InlineKeyboardButton("Забанить", callback_data='ban_user')],
	},
	'manage_tournaments': {
		'set_room': lambda game: [InlineKeyboardButton(
			f"🕑 PUBG ID {game.room_id}: {str(game)}",
			callback_data=f'set_room;{game.slot_id}'
		)],
		'set_winners': lambda game: [InlineKeyboardButton(
			f"🏆 PUBG ID {game.room_id}: {str(game)}",
			callback_data=f'set_winners;{game.slot_id}'
		)],
	},
	'set_winners': {
		'generate_table': lambda game_id: [InlineKeyboardButton(
			"Сгенерировать таблицу игроков", callback_data=f'generate_table;{game_id}')]
	},
	'bot_settings': {
		'debug_on': [InlineKeyboardButton(
			"⚠️ Включить дебаг ⚠️", callback_data='debug_mode')],
		'debug_off': [InlineKeyboardButton(
			"Выключить дебаг", callback_data='debug_mode')],
	},
	'tournaments': {
		'leave_slot': lambda slot: [InlineKeyboardButton(
			f"{slot.time.strftime('%H:%M')} - Выйти",
			callback_data=f'slot;{slot.slot_id}'
		)],
		'create_slot': lambda slot: [InlineKeyboardButton(
			f"{slot.time.strftime('%H:%M')} - Создать турнир",
			callback_data=f'slot;{slot.slot_id}'
		)],
		'join_slot': lambda slot: [InlineKeyboardButton(
			f"{str(slot)}", callback_data=f'slot;{slot.slot_id}')]
	},
	'add_funds': {
		'goto_payment': lambda amount, url: [InlineKeyboardButton(
			f"Перейти в платёжную систему, сумма: {amount}", url=url)]
	}
}
