# -*- coding: utf-8 -*-

import json
import urllib2
import socket
import sys
import re
import traceback
import datetime
from pandas.tseries.offsets import BDay
import QuoteCache
import math


gc001_price = {}

def reset():
	gc001_price.clear()

def setGC001Price(stock_code, stock_number, deal_amount, actual_amount):
	#print stock_code,stock_number,deal_amount,actual_amount
	if gc001_price.get(stock_code, -1) != -1:
		return gc001_price.get(stock_code)

	price = 0
	if not math.isnan(deal_amount) and deal_amount != 0:
		price = round(deal_amount / stock_number)
	elif not math.isnan(actual_amount) and actual_amount != 0:
		price = round(actual_amount / stock_number)
	else:
		print '!!!! wrong stock_code %s both deal_amount and actual_amount is 0' % stock_code
	#print price,deal_amount,actual_amount
	gc001_price[stock_code] = abs(price)
	#print gc001_price
	return gc001_price[stock_code]

def getGC001Price(stock_code):
	#print gc001_price
	return gc001_price.get(stock_code, -1)


def getNewStockCode(shengou_code):
	row = QuoteCache.get_new_stock_code(shengou_code)
	if row != None:
		return row[0]
	else:
		return ''

def getNewStockName(stock_code):
	row = QuoteCache.get_new_stock_name(stock_code)
	if row != None:
		return row[0]
	else:
		return ''

def get_sh_sz(stock_code):
	stock_code1 = ''
	if re.search('^00|^30|^15|^16|^18|^10|^11|^125|^126|^127|^128|^200', str(stock_code), re.UNICODE):
		stock_code1 = 'sz' + stock_code
	elif re.search('^6|^50|^51|^01|^02|^12|^13|^110|^113|^202|^204|^900', str(stock_code), re.UNICODE):
		stock_code1 = 'sh' + stock_code

	if re.search('^113501|^110015|^110023|^110007', str(stock_code), re.UNICODE):
		stock_code1 = 'sh' + stock_code

	return stock_code1

def composeUrl(stock_code, stock_date):
	url_template = 'http://stock.finance.sina.com.cn/stock/api/openapi.php/StockNewsService.getFqData?symbol={code}&startdate={date}&enddate={date}'
	stock_code1 = get_sh_sz(stock_code)
	url = url_template.format(code=stock_code1, date=stock_date)
	return url

def querySina(url):
	#print url
	result = json.loads( urllib2.urlopen(url).read() )
	#print result
	status_code = result[u'result'][u'status'][u'code']
	status_str = result[u'result'][u'data'][u'status']
	return (status_code, status_str, result)


def getClosePrice(stock_code, stock_date):
	#print stock_code, stock_date
	stock_code = str(stock_code)
	has_dot = stock_code.rfind('.')
	if has_dot != -1:
		stock_code = stock_code[:has_dot]

	p = getGC001Price(stock_code)
	if p != -1:
		#print 'xx'
		return p

	p = QuoteCache.get_xianjin_fund_price(stock_code, stock_date)
	if p != -1:
		return p

	p = QuoteCache.get_new_stock_price(stock_code, stock_date)
	if p != -1:
		return p

	p = QuoteCache.get_missing_stock_price(stock_code, stock_date)
	if p != -1:
		return p

	stock_code1 = stock_code
	if stock_code.startswith('127'):
		stock_code1 = get_sh_sz(stock_code)
	key = stock_code1 + '{:.0f}'.format(int(stock_date))

	row = QuoteCache.get(key)
	if row != None:
		return row[0]

	url = composeUrl(stock_code, stock_date)
	close = 0
	(status_code, status_str, result) = querySina(url)
	if status_code == 0:
		if status_str == u'成功':
			close = float( result[u'result'][u'data'][u'data'][0][u'close'] )
		elif status_str == u'无相关数据':
			close = 0
		else:
			close = -1
	else:
		close = -1

	QuoteCache.insert(key, close)
	return close

def getLastClosePrice(stock_code, stock_date):
	#print stock_code, type(stock_code), stock_date
	try:
		close = getClosePrice(stock_code, stock_date)
		while close == 0:
			stock_date = previous_stock_date(stock_date)
			close = getClosePrice(stock_code, stock_date)
		return close
	except TypeError:
		print "SinaQuote.getLastClosePrice TypeError" 
		tb = traceback.format_exc()
		print tb
		print stock_code, type(stock_code), stock_date
		sys.exit(1)
	except socket.error:
		print "SinaQuote.getLastClosePrice socket error"
		tb = traceback.format_exc()
		print tb
		print stock_code, type(stock_code), stock_date
		sys.exit(1)


def previous_stock_date(stock_date):
	#print stock_date, type(stock_date)
	dint = int(stock_date)
	d = datetime.date(dint/10000, dint%10000/100, dint%100)
	return (d-BDay()).strftime('%Y%m%d')


def test1():
	print querySina(composeUrl('600585', 20140617))

	print previous_stock_date(20140619)

	print getLastClosePrice('600585',20141229)

	print getLastClosePrice('600585',20141229)

	print getLastClosePrice('002705',20140110)

	print getNewStockName('002736')

	print getClosePrice('002736', 20141220)
	print getClosePrice('002736', 20141229)
	print getLastClosePrice('127002', 20140101)

if __name__ == '__main__':
	print getLastClosePrice('150200', 20141212)
	#test1()

