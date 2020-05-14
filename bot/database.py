'''Postgress database operations'''

from logging import getLogger

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.sql import SQL, Identifier

import queries
import qiwi
from config import db_url

##############################

logger = getLogger('db')


def with_connection(db_transaction):
	def execute_with_connection(*args, **kwargs):
		try:
			with psycopg2.connect(db_url, sslmode='require') as conn:
				with conn.cursor(cursor_factory=RealDictCursor) as cursor:
					return db_transaction(cursor, *args, **kwargs)
		except Exception as err:
			err.args = (
				(db_transaction.__name__,)
				+ tuple(args) + tuple(kwargs.items())
				+ err.args if err.args else ()
			)
			raise
	return execute_with_connection

##############################


@with_connection
def prepare_DB(cursor):
	for prepare in queries.init_db:
		cursor.execute(prepare)
	logger.info("Database ready!")


# user
@with_connection
def save_user(cursor, user_id, username):
	cursor.execute(queries.save_user, (user_id, username))
	logger.info("New user '%s' (%s) has been registered", username, user_id)
	return cursor.fetchone()


@with_connection
def get_user(cursor, *, fetch_all=False, **search_parameters):
	get_user_query = SQL(queries.get_user)
	if search_parameters:
		get_user_query += SQL('WHERE') + SQL('AND').join(
			[SQL('({} = %s)').format(Identifier(key))
				for key in search_parameters]
		)
	cursor.execute(get_user_query, tuple(search_parameters.values()))
	if fetch_all:
		return cursor.fetchall()
	return cursor.fetchone()


@with_connection
def update_user(cursor, user_id, **new_values):
	updated_rows = 0
	for column, value in new_values.items():
		cursor.execute(
			SQL(queries.update_user).format(Identifier(column)),
			{'value': value, 'id': user_id}
		)
		if cursor.rowcount:
			updated_rows += 1
			logger.info("User id %s updated: %s = %s", user_id, column, value)
	return updated_rows == len(new_values)


@with_connection
def get_balance(cursor, user_id):
	cursor.execute(queries.get_balance, (user_id,))
	return cursor.fetchone()['balance']


@with_connection
def get_balance_history(cursor, user_id):
	cursor.execute(queries.get_balance_history, (user_id,))
	return cursor.fetchall()


# matches
@with_connection
def create_slot(cursor, start_time):
	cursor.execute(queries.create_slot, (start_time,))
	return cursor.fetchone()['id']


@with_connection
def update_slot(cursor, slot_id, **updated):
	cursor.execute(
		SQL(queries.update_slot).format(SQL(', ').join(
			[SQL('{} = %s').format(Identifier(key)) for key in updated.keys()])),
		tuple(updated.values()) + (slot_id,)
	)


@with_connection
def delete_slot(cursor, slot_id):
	cursor.execute(queries.delete_slot, (slot_id,))
	# since deleting is cascading we can check if there were users
	if cursor.rowcount > 1:
		logger.info(
			"Slot id %s with %s players was canceled",
			slot_id, cursor.rowcount // 2
		)


@with_connection
def restore_slots(cursor):
	cursor.execute(queries.load_slots)
	slots = cursor.fetchall()
	for slot in slots:
		cursor.execute(queries.load_players, (slot['id'],))
		slot['players'] = cursor.fetchall()
	return slots


@with_connection
def join_slot(cursor, slot_id, user_id, bet):
	cursor.execute(
		queries.change_balance,
		(user_id, -bet, 'buy-in', None, slot_id)
	)
	cursor.execute(queries.join_slot, (slot_id, user_id))


@with_connection
def leave_slot(cursor, slot_id, user_id):
	cursor.execute(
		SQL(queries.leave_slot).format(Identifier('players_in_matches')),
		(slot_id, user_id)
	)
	cursor.execute(
		SQL(queries.leave_slot).format(Identifier('transactions')),
		(slot_id, user_id)
	)


@with_connection
def get_players(cursor, game_id):
	cursor.execute(queries.get_players, (game_id,))
	return cursor.fetchall()


@with_connection
def set_player_result(cursor, slot_id, user_id, result, value):
	cursor.execute(
		SQL(queries.set_player_result).format(Identifier(result)),
		(value, slot_id, user_id)
	)


# balances
@with_connection
def change_balance(cursor, user_id, amount, reason, slot_id=None, ext_id=None):
	cursor.execute(
		queries.change_balance,
		(user_id, amount, reason, ext_id, slot_id)
	)
	cursor.execute(queries.get_balance, (user_id,))
	logger.info("Balance change for user id %s: %s %s", user_id, reason, amount)
	return cursor.fetchone()['balance']


@with_connection
def withdraw_money(cursor, user_id, **details):
	cursor.execute(
		queries.change_balance,
		(user_id, details['amount'], 'withdraw', None, None)
	)
	if not (qiwi_id := qiwi.make_payment(**details)):
		cursor.connection.rollback()
		logger.error("Withdraw for user id %s (%s) failed", user_id, details)
		return None
	transaction_id = cursor.fetchone()['id']
	cursor.execute(
		queries.update_transaction_id,
		(qiwi_id, transaction_id)
	)
	cursor.execute(queries.get_balance, (user_id,))
	logger.info("User id %s withdrew %s", user_id, details['amount'])
	return cursor.fetchone()['balance']
