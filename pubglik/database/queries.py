"""SQLite database queries."""

init_db = (
	"""
	PRAGMA foreign_keys = 1
	""",
	"""
	CREATE TABLE IF NOT EXISTS users (
		id				INTEGER PRIMARY KEY,
		username		TEXT,
		pubg_id			INT UNIQUE,
		pubg_username	TEXT UNIQUE,
		admin			BOOL DEFAULT false,
		banned			BOOL DEFAULT false
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS matches (
		id			INTEGER PRIMARY KEY,
		time		TIMESTAMPTZ NOT NULL,
		type		TEXT,
		mode		TEXT,
		view		TEXT,
		bet			INT,
		pubg_id		INT,
		room_pass	TEXT,
		finished	BOOL DEFAULT false
	)
	""",
	"""
	CREATE TABLE IF NOT EXISTS players_in_matches (
		user_id		INT,
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
		id			INT PRIMARY KEY,
		user_id		INT NOT NULL,
		amount		INT NOT NULL,
		reason		TEXT NOT NULL,
		external_id	INT UNIQUE,
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
	INSERT INTO users (id, username) VALUES (?, ?)
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
	WHERE users.id = ?
	"""
find_user =\
	"""
	SELECT * FROM users
	"""
update_user =\
	"""
	UPDATE users SET {} = ? WHERE id = ?
	"""
get_balance =\
	"""
	SELECT COALESCE(SUM(amount), 0) AS balance
	FROM transactions WHERE user_id = ?
	"""
get_balance_history =\
	"""
	SELECT * FROM transactions WHERE user_id = ? ORDER BY date
	"""

# games
create_slot =\
	"""
	INSERT INTO matches (time) VALUES (?)
	"""
update_slot =\
	"""
	UPDATE matches SET {} WHERE id = ?
	"""
delete_slot =\
	"""
	DELETE FROM matches WHERE id = ?
	"""
load_slots =\
	"""
	SELECT * FROM matches WHERE finished = false ORDER BY time
	"""
load_players =\
	"""
	SELECT * FROM users WHERE id IN
		(SELECT user_id FROM players_in_matches WHERE match_id = ?)
	"""
join_slot =\
	"""
	INSERT INTO players_in_matches (match_id, user_id) VALUES (?, ?)
	"""
leave_slot =\
	"""
	DELETE FROM {} WHERE (match_id = ?) AND (user_id = ?)
	"""
get_players =\
	"""
	SELECT pubg_id, pubg_username, id, username FROM users
	WHERE users.id IN (SELECT user_id FROM players_in_matches WHERE match_id = ?)
	"""
set_player_result =\
	"""
	UPDATE players_in_matches SET {} = ?
		WHERE match_id = ? AND user_id = ?
	"""

# balances
change_balance =\
	"""
	INSERT INTO transactions
		(user_id, amount, reason, external_id, match_id, date)
	VALUES (?, ?, ?, ?, ?, date('now'))
	"""
update_transaction_id =\
	"""
	UPDATE transactions SET external_id = ? WHERE id = ?
	"""

# api
get_games =\
	"""
	SELECT time, bet, view, type, mode
	FROM MATCHES WHERE finished = false
	ORDER BY time
	"""
