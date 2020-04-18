init_db = (
	"""
		SET timezone = 'Europe/Moscow'
	""",
	"""
		CREATE TABLE IF NOT EXISTS users (
			id				BIGINT PRIMARY KEY,
			username		TEXT,
			pubg_id			BIGINT,
			pubg_username	TEXT,
			admin			BOOL DEFAULT false,
			banned			BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS matches (
			id			SERIAL PRIMARY KEY,
			start_time	TIMESTAMPTZ,
			type		TEXT NOT NULL,
			mode		TEXT NOT NULL,
			view		TEXT NOT NULL,
			bet			INT NOT NULL,
			pubg_id		BIGINT,
			room_pass	TEXT,
			finished	BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS players_in_matches (
			match_id	INT,
			player_id	BIGINT,
			place		INT,
			kills		INT,
			PRIMARY KEY (match_id, player_id),
			FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
			FOREIGN KEY (player_id) REFERENCES users (id),
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS transactions (
			id			SERIAL,
			amount		INT NOT NULL,
			user_id		BIGINT NOT NULL,
			reason		TEXT NOT NULL,
			external_id	BIGINT,
			match_id	INT,
			date		TIMESTAMPTZ,
			FOREIGN KEY (user_id) REFERENCES users (id),
			FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
		)
	""",
)


# users
save_user =\
	"""
		INSERT INTO users (id, username) VALUES (%s, %s)
			ON CONFLICT (id) DO UPDATE SET
				username = EXCLUDED.username
	"""
get_user =\
	"""
		SELECT * FROM users
	"""
update_user =\
	"""
		UPDATE users SET {} = %s WHERE id = %s
	"""
get_balance =\
	"""
		SELECT SUM(amount) FROM transactions WHERE user_id = %s
	"""
get_balance_history =\
	"""
		SELECT * FROM transactions WHERE user_id = %s
	"""

# games
create_slot =\
	"""
		INSERT INTO matches (start_time, type, mode, view, bet)
			VALUES (%s, %s, %s, %s, %s) RETURNING id
	"""
update_slot =\
	"""
		UPDATE matches SET {} WHERE id = %s
	"""
delete_slot =\
	"""
		DELETE FROM matches WHERE id = %s
	"""
join_slot =\
	"""
		INSERT INTO players_in_mathes (match_id, player_id) VALUES (%s, %s)
	"""
set_player_result =\
	"""
		UPDATE players_in_matches SET {} = %s
			WHERE match_id = %s AND player_id = %s
	"""

# balances
change_balance =\
	"""
		INSERT INTO transactions (user_id, amount, reason, match_id, date)
			VALUES (%s, %s, %s, %s, NOW())
	"""
update_transaction_id =\
	"""
		UPDATE transactions SET external_id = %s
			WHERE (user_id = %s) AND (amount = %s)
			ORDER BY date DESC LIMIT 1
	"""
