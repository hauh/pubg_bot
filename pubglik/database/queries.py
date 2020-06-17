"""Postgress database queries"""

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
		time		TIMESTAMPTZ NOT NULL,
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
		user_id		BIGINT NOT NULL,
		amount		INT NOT NULL,
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
	SELECT
		users.*,
		(SELECT COUNT(*)
			FROM players_in_matches WHERE user_id = users.id
		) AS games_played,
		(SELECT COALESCE(SUM(amount), 0)
			FROM transactions WHERE user_id = users.id
		) AS balance
	FROM users
	WHERE users.id = %s
	"""
find_user =\
	"""
	SELECT * FROM users
	"""
update_user =\
	"""
	UPDATE users SET {} = %s WHERE id = %s
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
	INSERT INTO matches (time) VALUES (%s) RETURNING id
	"""
update_slot =\
	"""
	UPDATE matches SET {} WHERE id = %s
	"""
delete_slot =\
	"""
	DELETE FROM matches WHERE id = %s
	"""
load_slots =\
	"""
	SELECT * FROM matches WHERE finished = false ORDER BY time
	"""
load_players =\
	"""
	SELECT * FROM users WHERE id IN
		(SELECT user_id FROM players_in_matches WHERE match_id = %s)
	"""
join_slot =\
	"""
	INSERT INTO players_in_matches (match_id, user_id) VALUES (%s, %s)
	"""
leave_slot =\
	"""
	DELETE FROM {} WHERE (match_id = %s) AND (user_id = %s)
	"""
get_players =\
	"""
	SELECT pubg_id, pubg_username, id, username FROM users
	WHERE users.id IN (SELECT user_id FROM players_in_matches WHERE match_id = %s)
	"""
set_player_result =\
	"""
	UPDATE players_in_matches SET {} = %s
		WHERE match_id = %s AND user_id = %s
	"""

# balances
change_balance =\
	"""
	INSERT INTO transactions (user_id, amount, reason, external_id, match_id, date)
	VALUES (%s, %s, %s, %s, %s, NOW())
	RETURNING id
	"""  # noqa
update_transaction_id =\
	"""
	UPDATE transactions SET external_id = %s WHERE id = %s
	"""
