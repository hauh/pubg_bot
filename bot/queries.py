init_db = (
	"""
		SET timezone = 'Europe/Moscow'
	""",
	"""
		CREATE TABLE IF NOT EXISTS users (
			id				BIGINT PRIMARY KEY,
			username		TEXT,
			pubg_id			BIGINT UNIQUE,
			pubg_username	TEXT UNIQUE,
			admin			BOOL DEFAULT false,
			banned			BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS matches (
			id			SERIAL PRIMARY KEY,
			start_time	TIMESTAMPTZ NOT NULL,
			type		TEXT,
			mode		TEXT,
			view		TEXT,
			bet			INT,
			pubg_id		BIGINT,
			room_pass	TEXT,
			finished	BOOL DEFAULT false
		)
	""",
	"""
		CREATE TABLE IF NOT EXISTS players_in_matches (
			user_id		BIGINT,
			match_id	INT,
			place		INT,
			kills		INT,
			PRIMARY KEY (match_id, user_id),
			FOREIGN KEY (user_id) REFERENCES users (id),
			FOREIGN KEY (match_id) REFERENCES matches (id) ON DELETE CASCADE
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
		INSERT INTO users (id, username) VALUES (%s, %s) RETURNING *
	"""
get_user =\
	"""
		SELECT * FROM users
	"""
update_user =\
	"""
		UPDATE users SET {0} = %(value)s
		WHERE id = %(id)s AND {0} IS DISTINCT FROM %(value)s
	"""
get_balance =\
	"""
		SELECT COALESCE(SUM(amount), 0) AS balance
		FROM transactions WHERE user_id = %s
	"""
get_balance_history =\
	"""
		SELECT * FROM transactions WHERE user_id = %s
	"""

# games
create_slot =\
	"""
		INSERT INTO matches (start_time) VALUES (%s) RETURNING id
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
		INSERT INTO players_in_matches (match_id, user_id) VALUES (%s, %s)
	"""
leave_slot =\
	"""
		DELETE FROM {} WHERE (match_id = %s) AND (user_id = %s)
	"""
set_player_result =\
	"""
		UPDATE players_in_matches SET {} = %s
			WHERE match_id = %s AND user_id = %s
	"""

# balances
change_balance =\
	"""
		INSERT INTO transactions (user_id, amount, reason, match_id, external_id, date)
			VALUES (%s, %s, %s, %s, %s, NOW())
		RETURNING id
	"""
update_transaction_id =\
	"""
		UPDATE transactions SET external_id = %s WHERE id = %s
	"""
