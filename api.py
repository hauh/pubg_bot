'''Webhook returning current games for website'''

import os

from flask import Flask, jsonify
import psycopg2

##############################

TEXTS = {
	'survival_easy': "Выживание (лёгкий)",
	'survival_medium': "Выживание (средний)",
	'survival_hard': "Выживание (тяжёлый)",
	'kills': "Убийства",
	"mixed": "Смешанный",
	'1st': "От первого лица",
	'3rd': "От третьего лица",
	'solo': "SOLO",
	'dual': "DUAL",
	'squad': "SQUAD",
	'payload': "Payload",
	'zombie': "Zombie",
}
DEFAULT = "Ещё не выбрано!"
GET_GAMES_QUERY =\
	"""
	SELECT TO_CHAR(time, 'HH24:MI'), bet, view, type, mode
	FROM MATCHES WHERE finished = false
	ORDER BY time
	"""

DB_URL = os.getenv('DATABASE')
SSL = (os.getenv('SSL_CERT'), os.getenv('SSL_KEY'))

##############################

app = Flask(__name__)


@app.route('/get_games', methods=['GET'])
def get_games():
	try:
		with psycopg2.connect(DB_URL, sslmode='require') as conn:
			with conn.cursor() as cursor:
				cursor.execute(GET_GAMES_QUERY)
				raw_games = cursor.fetchall()
	except Exception:  # pylint: disable=broad-except
		return ("DB Error", 500)
	games = []
	for game in raw_games:
		games.append([TEXTS.get(data, data) if data else DEFAULT for data in game])
	response = jsonify(games)
	response.headers.add("Access-Control-Allow-Origin", "*")
	return response


if __name__ == '__main__':
	app.run(
		use_reloader=True, ssl_context=SSL,
		host=os.getenv('SERVER_ADDRESS'), port="5000"
	)
