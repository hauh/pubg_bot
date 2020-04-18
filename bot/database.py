from logging import getLogger

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.sql import SQL, Identifier

import queries
from config import db_url

##############################

logger = getLogger('db')


def withConnection(db_transaction):
	def executeWithConnection(*args, **kwargs):
		try:
			with psycopg2.connect(db_url, sslmode='require') as conn:
				with conn.cursor(cursor_factory=RealDictCursor) as cursor:
					return db_transaction(cursor, *args, **kwargs)
		except Exception as err:
			logger.critical(
				f"DB transaction failed with:\n{type(err).__name__} {err.args}")
			raise
		finally:
			conn.close()
	return executeWithConnection


@withConnection
def prepareDB(cursor):
	for prepare in queries.init_db:
		cursor.execute(prepare)
	logger.info("Database ready!")


# user
@withConnection
def saveUser(cursor, user_id, username):
	cursor.execute(queries.save_user, (user_id, username))
	if cursor.rowcount == 1:
		logger.info(f"New user {user_id} has been registered")


@withConnection
def getUser(cursor, **search_parameters):
	get_user_query = SQL(queries.get_user)
	if search_parameters:
		get_user_query += SQL('WHERE') + SQL('AND').join(
			[SQL('({} = %s)').format(Identifier(key))
				for key in search_parameters.keys()]
	)
	cursor.execute(get_user_query, tuple(search_parameters.values()))
	if cursor.rowcount == 1:
		return cursor.fetchone()
	return cursor.fetchall()


@withConnection
def updateUser(cursor, user_id, column, new_value):
	cursor.execute(
		SQL(queries.update_user).format(Identifier(column)),
		(new_value, user_id)
	)
	logger.info(f"User id {user_id} updated: '{column}' became {new_value}")


@withConnection
def getBalance(cursor, user_id):
	cursor.execute(queries.get_balance, (user_id,))
	return cursor.fetchone()


@withConnection
def getBalanceHistory(cursor, user_id):
	cursor.execute(queries.get_balance_history, (user_id,))
	return cursor.fetchall()


# matches
@withConnection
def createSlot(cursor, *slot_settings):
	cursor.execute(queries.create_slot, slot_settings)
	return cursor.fetchone()


@withConnection
def updateSlot(cursor, slot_id, **updated):
	cursor.execute(
		SQL(queries.update_slot).format(SQL(', ').join(
			[SQL('{} = %s').format(Identifier(key)) for key in updated.keys()])),
		tuple(updated.values())
	)


@withConnection
def deleteSlot(cursor, slot_id):
	cursor.execute(queries.delete_slot, (slot_id,))
	logger.info(f"Slot id {slot_id} was canceled")


@withConnection
def joinSlot(cursor, slot_id, user_id):
	cursor.execute(queries.join_slot, (slot_id, user_id))


@withConnection
def setPlayerResult(cursor, slot_id, user_id, result, value):
	cursor.execute(
		SQL(queries.set_player_results).format(Identifier(result)),
		(value, slot_id, user_id)
	)


# balances
@withConnection
def changeBalance(cursor, user_id, amount, reason, slot_id=None):
	cursor.execute(
		queries.change_balance,
		(user_id, amount, reason, slot_id)
	)
	cursor.execute(queries.get_balance, (user_id))
	logger.info(f"Balance of user id {user_id} changed for {amount}: {reason}")
	return cursor.fetchone()


@withConnection
def setTransactionID(cursor, user_id, amount, external_id):
	cursor.execute(
		queries.update_transaction_id,
		(external_id, user_id, amount)
	)
