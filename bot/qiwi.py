'''Handling requests to QIWI API'''

from time import time
from logging import getLogger

import requests

import config

##############################

logger = getLogger('qiwi')
headers = {
	'Accept': 'application/json',
	'Content-type': 'application/json',
	'Authorization': f'Bearer {config.qiwi_token}'
}
providers = {
	'qiwi': 99,
	'visa': 1963,
	'mastercard': 21013,
	'mir': 31652
}


def check_balance():
	response = requests.get(
		f'https://edge.qiwi.com/funding-sources/v2/persons/{config.qiwi_phone}/accounts',  # noqa
		headers=headers
	)
	if not response.ok:
		logger.error(
			"Balance check: %s (%s)", response.status_code, response.json())
		return 0
	return response.json()['accounts'][0]['balance']['amount']


def check_commission(provider, account, amount):
	com = requests.post(
		f'https://edge.qiwi.com/sinap/providers/{providers[provider]}/onlineCommission',  # noqa
		json={
			'account': account,
			'paymentMethod': {
				'type': 'Account',
				'accountId': '643',
			},
			'purchaseTotals': {
				'total': {
					'amount': amount,
					'currency': '643',
				}
			}
		},
		headers=headers
	)
	if not com.ok:
		logger.error("Commission check: %s (%s)", com.status_code, com.json())
		return None
	return int(-(-com.json()['qwCommission']['amount'] // 1))


def make_payment(provider, account, amount):
	payment = requests.post(
		f'https://edge.qiwi.com/sinap/api/v2/terms/{providers[provider]}/payments',  # noqa
		json={
			'id': str(int(time() * 1000)),
			'sum': {
				'amount': amount,
				'currency': "643"
			},
			'paymentMethod': {
				'type': "Account",
				'accountId': "643"
			},
			'fields': {
				'account': account,
			},
			'comment': "PUBG",
		},
		headers=headers
	)
	if not payment.ok:
		logger.error("Payment: %s (%s)", payment.status_code, payment.json())
		return None
	return payment.json()['id']


def find_income(code):
	history = requests.get(
		f"https://edge.qiwi.com/payment-history/v2/persons/{config.qiwi_phone}/payments",  # noqa
		params={
			'rows': 50,
			'operation': 'IN',
		},
		headers=headers
	)
	if not history.ok:
		logger.error(
			"Income check: %s (%s)", history.status_code, history.json())
	else:
		for payment in history.json()['data']:
			if payment['comment'] == code and payment['status'] == 'SUCCESS':
				return int(payment['sum']['amount']), int(payment['txnId'])
	return None
