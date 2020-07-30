"""All bot's texts located here in dict with specific structure"""

from pubglik import config
from telegram import InlineKeyboardButton

##############################

settings_names = {
	'type': {
		'survival_easy': "Выживание (лёгкий)",
		'survival_medium': "Выживание (средний)",
		'survival_hard': "Выживание (тяжёлый)",
		'kills': "Убийства",
		'mixed': "Смешанный",
	},
	'mode': {
		'solo': "SOLO",
		'dual': "DUAL",
		'squad': "SQUAD",
		'payload': "Payload",
		'zombie': "Zombie",
	},
	'_short_': {
		'survival_easy': "Выж(лёгк)",
		'survival_medium': "Выж(ср)",
		'survival_hard': "Выж(тяж)",
	},
}

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
	**{f'type;{key}': name for key, name in settings_names['type'].items()},
	'mode': "Выбрать режим",
	**{f'mode;{key}': name for key, name in settings_names['mode'].items()},
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

texts = {
	# ########## main ########## #
	'_main_': {
		'registered': (
			"Приветствуем тебя, *{}*, в нашей команде!\n"
			"Текущий баланс: {}\nСыграно турниров: {}."
		),
		'unregistered': (
			"Приветствуем, победитель!\n"
			"PUBG.Lik - турниры на реальные деньги круглосуточно!\n"
			"1. Пройди регистрацию - вкладка «Личный кабинет».\n"
			"2. Пополни баланс на любую сумму от 10 руб.\n"
			"3. Выбери или создай свой турнир с любым режимом.\n"
			"4. Играй и выигрывай!"
		),
		'banned': "Вы забанены :(",
	},
	'how': "Правила пользования сервисом.",
	'usage': (
		"1) Зарегистрируйте ваш PUBG ID и PUBG ник в профиле. Убедитесь в "
		"верности ваших данных, чтобы вы смогли попасть в игровое лобби.\n"
		"2) В своём профиле у бота пополните ваш счёт.\n"
		"3) Заходите в слот с удобным для вас временем и режимом (если вы зашли "
		"первым, то режим и стаку выбираете вы), вы можете участовать в одиночку "
		"или со своими друзьями.\n"
		f"4) За {config.times['close_slot']} мин. до начала турнира, если набралось "
		"достаточное количество игроков, бот пришлёт вам уведомление с напоминанием "
		"о турнире. До этого момента вы можете выйти и забрать ставку.\n"
		f"5) За {config.times['send_room']} мин. до начала турнира бот пришлёт вам "
		"логин и пароль от лобби, а также номер команды, в которую вам необходимо "
		"будет вступить, аналогичные данные для входа появятся в вашем кабинете у "
		"бота. Входить в лобби настоятельно рекомендуем сразу, как только вы "
		"получили соответствующие данные, если вы опоздаете к началу, игра пройдёт "
		"без вас. Если в вашей ячейке находится посторонний игрок, сообщите нам об "
		"этом в поддержку в телеграмме (раздел контакты), и мы кикнем его из лобби, "
		"чтобы вы смогли занять свое место. Крайний срок обращения в поддержку с "
		"этим вопросом - за 2 минуты до начала турнира.\n"
		"6) После окончания турнира, если вы выиграли призы, бот пришлёт вам "
		"результаты, и на ваш баланс будут начислена соответсвующая сумма .\n"
		"7) Вы можете вывести ваши средства любым удобным способом у себя в профиле."
	),
	'prize_structure': (
		"В зависимости от режима, призовой фонд будет "
		"распределён следующим образом:\n\n"
		"*Выживание*:\n"
		"Лёгкий: +70% к стоимости участия получают игроки, попавшие в топ 50.\n"
		"Средний: +180% к стоимости участия получают игроки, попавшие в топ 25.\n"
		"Тяжёлый: +600% к стоимости участия получают игроки, попавшие в топ 10.\n"
		"*Убийства*:\n"
		"За каждый килл игрок получает 70% от суммы участия.\n"
		"*Смешанный*:\n"
		"Топ 10 игроков получают +150% к сумме участия.\n"
		"Тор 25 — +50% к сумме участия.\n"
		"За каждый килл вы получите 22% от суммы участия."
	),
	'rules': (
		"*Запрещено*:\n"
		"• Участие в турнирах с эмуляторов;\n"
		"• Вставать не в свою ячейку в лобби (режимы Дуо и Сквад);\n"
		"• Отправлять логин и пароль для входа в лобби третьим лицам;\n"
		"• Участие в турнире с аккаунта, на котором уровень ниже 20;\n"
		"• Использовать чит-коды;\n"
		"Каждое из нарушений влечет за собой удаление из Турнира! "
		"В некоторых случаях возможен бан аккаунта без возврата "
		"денежных средств."
	),
	'contacts': (
		"*Телеграм*:\n"
		"https://t.me/PUBGLIK\\_support\n"
		"*Инстаграм*:\n"
		"https://instagram.com/pubg.lik.ru\n"
		"*ВКонтакте*:\n"
		"https://vk.com/pubg\\_lik\n"
		"*Почта*:\n"
		"pubglik@mail.ru"
	),

	# ########## admin ########## #
	'admin': "Управление.",
	'manage_tournaments': (
		"🕑: турниры, ожидающие начала (нужен ID комнаты и пароль).\n"
		"🏆: турниры, ожидающие результатов."
	),
	'set_room': {
		'input': (
			"Турнир: [{}]\n"
			"Введите через запятую числовой PUBG ID комнаты и пароль.\n"
			"Текущий PUBG ID комнаты: *{}*\nТекущий пароль: *{}*"
		),
		'invalid': "\n\n*Неправильный ввод*. \n**(числовой ID,пароль)**",
		'confirm': "\n\nНовый ID: *{}*\nНовый пароль: *{}*\n*Подтвердить?*",
	},
	'set_winners': {
		'input': (
			"Турнир: [{}], PUBG ID: {}.\n"
			"Отправьте сюда заполненный Excel-файл с победителями в турнире."
		),
		'bad_file': "Ошибка чтения файла. Проверьте, что это Excel.",
		'unknown_player': "В файле обнаружен неизвестный игрок (строка {}).",
		'invalid_value': "Недопустимое или повторное значение (строка {}).",
		'not_enough': "В таблице указаны не все призовые места.",
		'wrong_kills': "Неверное количество убийств, должно быть {}.",
		'missing_something': "Чего-то ещё не хватает.",
		'confirm': (
			"Победители введены успешно. Всего ставок сделано: {}. "
			"*Призовых будет выплачено: {}*\n*Подтвердить?*"
		),
	},
	'manage_admins': "Управление администраторами.",
	'add_admin': {
		'input': "Введите телеграм-ник нового администратора. Бот должен его знать.",
		'found': "Найден пользователь: @{}",
		'not_found': "Такой пользователь не найден. Проверьте ввод.",
	},
	'revoke_admin': "Выберите, какого администратора удалить.",
	'manage_users': {
		'input': (
			"Управление пользователями.\n"
			"Введите telegram-ник пользователя с символом @ в начале, ник PUBG "
			"без символа, telegram ID или PUBG ID."
		),
		'found': (
			"Пользователь найден!\n\n"
			"Telegram ID: *{id}*\n"
			"Telegram username: *{username}*\n"
			"PUBG ID: *{pubg_id}*\n"
			"PUBG username: *{pubg_username}*\n"
			"Баланс: *{balance}*\n"
			"Забанен: *{banned}*\n\n"
			"Выберите действие или введите другого пользователя."
		),
		'not_found': "Такой пользователь не найден.",
	},
	'change_balance': {
		'input': (
			"Telegram ID: *{id}*\n"
			"Telegram username: *{username}*\n"
			"PUBG ID: *{pubg_id}*\n"
			"PUBG username: *{pubg_username}*\n"
			"Текущий баланс: *{balance}*\n\n"
			"Введите сумму (можно отрицательную)."
		),
		'invalid': "Введите число в диапазоне 1-999999.",
		'confirm': "Изменить баланс на *{}*?",
	},
	'ban_user': (
		"Забанить пользователя? Он будет удалён изо всех турниров, "
		"кроме начавшихся, и не сможет больше пользоваться ботом."
	),
	'mailing': {
		'input': "Введите сообщение для отправки *ВСЕМ* пользователям.",
		'confirm': "Подвердите рассылку сообщения:\n\n{}\n\nИли введите другое.",
	},
	'bot_settings': (
		"Настройки бота\n\n"
		"*Внимание!*\nЕсли дебаг включен, бот не будет отвечать пользователям."
	),

	# ########## tournaments ########## #
	'tournaments': {
		'rules': (
			"Выберите не более трёх турниров, в которых хотите участвовать. "
			"Cтавка будет заморожена на вашем балансе пока турнир не начнётся, "
			"или вы из него не выйдете (не позднее, чем за "
			f"{config.times['close_slot']} мин. до начала).\n"
			"*Ваш баланс*: {}\n"
		),
		'picked': "*Выбранные турниры*:"
	},
	'slot': {
		'create': (
			"Cоздание турнира.\nВыбранная ставка будет заморожена на вашем счету "
			"после подтверждения. Ваш баланс: *{}*."
		),
		'type': "\n*Тип*: {}",
		'mode': "\n*Режим*: {}",
		'view': "\n*Обзор*: {}",
		'bet': "\n*Ставка*: {}"
	},
	'type': "Выберите *ТИП* игры.",
	'mode': "Выберите *РЕЖИМ* игры.",
	'view': "Выберите *ОБЗОР* игры.",
	'bet': "Выберите *СТАВКУ*.",

	# ########## cabinet ##########
	'cabinet': (
		"*ЛИЧНЫЙ КАБИНЕТ*\n\n"
		"*Telegram ID*: {user_id}\n"
		"*PUBG ник*: {pubg_id}\n"
		"*PUBG ID*: {pubg_username}\n"
		"*Баланс*: {balance}\n"
	),
	'set_pubg_username': {
		'input': "Введите ваш игровой ник.",
		'confirm': "Новый ник: *{}*",
		'invalid': "Слишком длинный ник.",
	},
	'set_pubg_id': {
		'input': "Введите ваш игровой ID.",
		'confirm': "Новый PUBG ID: *{}*.",
		'invalid': "ID должен состоять только из 8-10 цифр.",
	},
	'add_funds': {
		'input': (
			"*ПОПОЛНЕНИЕ БАЛАНСА*\n\n"
			"Введите сумму платежа и подтвердите, после чего вы будете "
			"перенаправлены на сайт платёжной системы. Комиссия зависит от "
			"способа оплаты, итоговая сумма будет указана у оператора платежа.\n"
			"В случае возникновения проблемы, свяжитесь с администрацией.\n\n"
			"*Введите сумму.*"
		),
		'confirm': "Сумма *пополнения*: {}. Создать ссылку для оплаты?",
		'invalid': "Введите число в диапазоне 10 - 99999.",
	},
	'withdraw_money': {
		'money': "Вывод средств с вашего счёта. Ваш баланc: *{}*.",
		'provider': "\nСпособ вывода: *{}*.",
		'account': "\nНомер кошелька/карты: *{}*.",
		'amount': "\nСумма вывода: *{}*.",
		'commission': "\n*Итоговая сумма* с комиссией оператора перевода: *{}*.",
		'payment_error': "Пользователь @*{}* ({}) не смог вывести деньги, ошибка: {}"
	},
	'provider': "Выберите способ вывода.",
	'account': {
		'input': "Введите кошелёк/карту в формате выбранного способа вывода.",
		'confirm': "Введённый кошелёк/карта: *{}*.",
		'invalid': "Неправильный формат кошелька/карты.",
	},
	'amount': {
		'input': "Введите сумму *вывода*.",
		'confirm': "Сумма вывода: *{}*.",
		'invalid': "Введите число в диапазоне 10 - 99999.",
	},
	'balance_history': {
		'template': "{arrow} \\[{id}: {date}] *{amount}*",
		'not_found': "Операций не найдено.",
	},
}

answers = {
	# ########## admin ########## #
	'set_room': {
		'success': {
			'text': "ID комнаты и пароль сохранены.",
			'show_alert': False,
		}
	},
	'set_winners': {
		'success': {
			'text': "Начато распределение призов.",
			'show_alert': False
		}
	},
	'add_admin': {
		'success': {
			'text': "Администратор добавлен!",
			'show_alert': False
		}
	},
	'revoke_admin': {
		'success': {
			'text': "Администратор удалён!",
			'show_alert': False,
		}
	},
	'change_balance': {
		'success': {
			'text': "Баланс изменён.",
			'show_alert': False
		}
	},
	'ban_user': {
		'success': {
			'text': "Забанен!",
			'show_alert': False
		}
	},
	'unban_user': {
		'success': {
			'text': "Разбанен!",
			'show_alert': False
		}
	},
	'mailing': {
		'success': {
			'text': "Начата рассылка сообщений.",
			'show_alert': True,
		}
	},
	'debug_mode': {
		'debug_off': {
			'text': "Режим дебага теперь выключен.",
			'show_alert': False
		},
		'debug_on': {
			'text': "Режим дебага теперь ВКЛЮЧЕН!",
			'show_alert': True
		},
	},

	# ########## tournaments ########## #
	'tournaments': {
		'pubg_required': {
			'text': (
				"Привет, Игрок! "
				"Для начала пройди регистрацию - вкладка «Личный Кабинет».",
			),
			'show_alert': True
		}
	},
	'slot': {
		'not_found': {
			'text': "Турнир не найден. Вероятно, он уже начался или завершился.",
			'show_alert': False,
		},
		'maximum': {
			'text': "Вы уже записаны на три турнира.",
			'show_alert': True,
		},
		'expensive': {
			'text': "У вас не хватает средств для участия в этом турнире.",
			'show_alert': True,
		},
		'full': {
			'text': "Турнир заполнен.",
			'show_alert': True,
		},
		'already_set': {
			'text': "Турнир уже был кем-то создан.",
			'show_alert': True,
		},
		'too_late': {
			'text': "Нельзя выйти: турнир уже готовится к началу.",
			'show_alert': True,
		},
		'left': {
			'text': "Вы вышли из турнира. Ставка возвращена на ваш счёт.",
			'show_alert': True,
		},
		'joined': {
			'text': (
				f"Турнир выбран. За {config.times['send_room']} мин. "
				"до начала придёт пароль от комнаты."
			),
			'show_alert': True
		},
	},

	# ########## cabinet ########## #
	'set_pubg_username': {
		'success': {
			'text': "Новый ник PUBG установлен.",
			'show_alert': False
		},
		'duplicate': {
			'text': "Такой ник уже зарегистрирован.",
			'show_alert': True
		},
	},
	'set_pubg_id': {
		'success': {
			'text': "Новый PUBG ID установлен.",
			'show_alert': False
		},
		'duplicate': {
			'text': "Такой PUBG ID уже зарегистрирован.",
			'show_alert': True
		},
	},
	'withdraw_money': {
		'too_much': {
			'text': "На вашем счету недостаточно средств.",
			'show_alert': True
		},
		'error': {
			'text': "Произошла ошибка, попробуйте позже или обратитесь в поддержку.",
			'show_alert': True
		},
	},
	'amount': {
		'too_much': {
			'text': "На вашем счету недостаточно средств.",
			'show_alert': True
		},
	}
}

# notifications
slot_is_ready = {
	'admins': "Турнир [{}] собрался. Введите ID комнаты и пароль в админке.",
	'users': (
		"Турнир [{}] собрался! "
		f"*За {config.times['send_room']} мин.* "
		"до начала вы получите сообщение с именем комнаты и паролем."
	)
}
game_is_starting = {
	'admins': "Турнир [{}] (PUBG ID {}) начался!",
	'users': (
		"Ваш турнир [{}] "
		f"*начнётся в течение {config.times['send_room']} мин*.\n"
		"Имя комнаты: *{}*, пароль: *{}*"
	)
}
game_ended = {
	'admins': (
		"Турнир [{game}] ({pubg_id}) завершён.\n"
		"Всего *ставок: {total_bets}*, призовых *выплачено: {prizes}*"
	),
	'users': (
		"Турнир [{game}] завершён, ваш результат:\n{place}{kills}\n"
		"Ваш счёт пополнен на *{prize}*. Поздравляем!"
	)
}
winner_place = "Вы заняли *место: {}*\n"
kills_count = "Вы совершили *убийств: {}*\n"
game_didnt_happen = "Турнир [{}] не состоялся. Ставка возвращена на ваш счёт."
game_failed = "Турнир [{}] отменён - не создана комната!"

# misc
error = "Ошибка. Попробуйте заново"
got_money = "Поступил платёж на сумму {}. Ваш баланс: {}."
