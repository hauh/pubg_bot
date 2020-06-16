"""Unitpay payments processing"""

from logging import getLogger
from hashlib import sha256
from urllib.parse import urlencode

import requests

from config import (
	unitpay_url as URL,
	unitpay_secret as SECRET,
	unitpay_api as API,
	unitpay_auth_params as AUTH
)

##############################

logger = getLogger('unitpay')

providers = {
	'card': r'^[1-9][0-9]{15,17}$',
	'mc': r'7[0-9]{10}$',
	'yandex': r'[1-9][0-9]{12,17}$',
	'qiwi': r'7[0-9]{10}$',
	'webmoney': r'(R|P|Z)[0-9]{12,16}$'
}


def invoice_url(user_id: str, amount: str):
	description = f"PUBGlik.ru ({user_id})"
	hash_str = "{up}".join([user_id, description, amount, SECRET]).encode('utf-8')
	params = {
		'sum': amount,
		'account': user_id,
		'desc': description,
		'signature': sha256(hash_str).hexdigest()
	}
	return f"{URL}?{urlencode(params)}"


def check_commission(provider):
	data = {'method': 'getCommissions', **AUTH}
	if not (result := requests.post(API, data=data)).ok:
		logger.error("Error checking commissiion:%s", result.status_code)
		return None
	result = result.json()['result']
	return result.get(provider, max(result.values()))


def make_payment(transaction_id, amount, account, provider):
	data = {
		'method': 'massPayment',
		'params[sum]': amount,
		'params[purse]': account,
		'params[transactionId]': transaction_id,
		'params[paymentType]': provider,
		**AUTH
	}
	if not (result := requests.post(API, data=data)).ok:
		logger.error("Error making request to Unitpay API: %s", result.status_code)
		result.raise_for_status()
	result = result.json()
	if 'error' in result:
		if result['error']['code'] <= 123:  # error on our side
			logger.error("Error making payment: %s", result['error']['message'])
			raise OSError(result['error']['message'])
		return result['error']['message'], None
	return result['result']['message'], result['result']['payoutId']
