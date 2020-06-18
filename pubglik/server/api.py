"""Webhook returning list of games for website"""

import cherrypy
import psycopg2 as postgres

from pubglik.config import database_url as DB_URL

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

##############################


@cherrypy.expose
class GetGames():
	"""Returning list of not yet finished games at /games"""

	_cp_defaults = {
		'tools.response_headers.on': True,
		'tools.response_headers.headers': [
			('Access-Control-Allow-Origin', '*'),
		]
	}

	@cherrypy.tools.json_out()
	@cherrypy.tools.accept(media='application/json')
	def GET(self):
		try:
			with postgres.connect(DB_URL, sslmode='require') as conn:
				with conn.cursor() as cursor:
					cursor.execute(GET_GAMES_QUERY)
					raw_games = cursor.fetchall()
		except postgres.Error as err:
			cherrypy.log.error(
				err.args[0], context=f"DB Error - {type(err).__name__}:\n")
			raise cherrypy.HTTPError(500)
		return [
			[TEXTS.get(data, data) if data else DEFAULT for data in game]
				for game in raw_games
		]
