'''Testing module with server to catch requests'''

import logging
import json
from threading import Thread
from queue import Queue, Empty
from http.server import HTTPServer, BaseHTTPRequestHandler

from users import UsersCollection

##############################

SERVER_ADDRESS = ('127.0.0.1', 7777)
REQUESTS_QUEUE = Queue()

logging.basicConfig(format="", level=logging.INFO)
logger = logging.getLogger('debug')

##############################


class BotRequestHandler(BaseHTTPRequestHandler):
	'''Catches POST requests from bot and puts them to Queue for testing'''

	def log_message(self, *_):
		pass

	def do_POST(self):
		content_length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(content_length)
		REQUESTS_QUEUE.put(json.loads(post_data, strict=False))
		self.send_response(200)
		self.end_headers()


def do_test(actions):
	users_collection = UsersCollection(how_many=10, actions=actions)
	users_collection.start_actions()

	while True:
		try:
			data = REQUESTS_QUEUE.get(timeout=10)
		except Empty:
			assert users_collection.is_empty, "Test failed"
			return

		logger.info("Got data:\n%s", data)

		if data['method'] != 'sendMessage':
			continue

		user_id = data.get('chat_id')
		if not user_id or user_id not in users_collection:
			logger.warning('Who is that:\n%s', str(data))
			continue

		if not users_collection[user_id].next_action():
			del users_collection[user_id]
			logger.info('User %s made it to finish!', user_id)
		else:
			logger.info('Next action for user %s', user_id)


TEST_TEST = [
	('message', '/start'),
	('button', 'matches'),
	('button', 'profile'),
	('button', 'set_pubg_id'),
	('message', lambda self: str(self.user_id)),
	('button', lambda self: f"_confirm_{str(self.user_id)}")
]


def test():

	server = HTTPServer(SERVER_ADDRESS, BotRequestHandler)
	Thread(target=server.serve_forever).start()

	do_test(TEST_TEST)

	logger.info("Tests done")
	server.shutdown()


if __name__ == '__main__':
	test()
