# -*- coding: utf-8 -*-

import re
import math
import pandas as pd
import SinaQuote


def get_row_date(row):
	deal_date = row['deal_date']
	if type(deal_date) is str or type(deal_date) is unicode:
		deal_date = re.sub(u'-', '', deal_date)
	#print type(deal_date),deal_date
	return int(deal_date)

def norm_stock_code(stock_code):
	if type(stock_code) is float or type(stock_code) is int:
		stock_code = '{:.0f}'.format(stock_code)
		if len(stock_code)<6:
			stock_code = '0'*(6-len(stock_code))+stock_code
	elif type(stock_code) is unicode:
		if len(stock_code)<6:
			stock_code = '0'*(6-len(stock_code))+stock_code
	return stock_code

def process_init_position(account, remain_stock, stock_number, stock_code, stock_name, operation):

	if type(stock_name) is unicode and not math.isnan(remain_stock) and \
	not math.isnan(stock_number) and \
	operation in ['buy', 'earn stock', 'stock in', 'sell', 'stock out'] and \
	not stock_name.endswith((u'A',u'B')):
		init_number = None
		if operation in ['buy', 'earn stock', 'stock in']:
			init_number = remain_stock-stock_number
		elif operation in ['sell', 'stock out']:
			init_number = remain_stock+stock_number

		if init_number==0:
			account.add_init_position_stock_code(stock_code)
			
		elif init_number!=0 and stock_code not in account.init_position_stock_code_map:
			print '******', remain_stock, stock_number, stock_code, stock_name, operation, init_number
			account.add_init_position_stock_code(stock_code)
			account.add_init_position(stock_code, stock_name, init_number)
			#print 'map:\n',account.init_position_stock_code_map
			#print 'init p:\n',account.stock_position.init_position
			#account.print_init_position()



def handle_row(row, account, is_first_row):
	#print row
	deal_date = get_row_date(row)
	deal_time = row[u'deal_time']
	stock_code = norm_stock_code(row[u'stock_code'])
	if stock_code == '000nan' and row['operation'] in ['buy','sell','earn stock']:
		print row
	stock_name = row[u'stock_name']
	operation = row[u'operation']
	stock_price = row[u'stock_price']
	if stock_price != u'---':
		stock_price = float(stock_price)
	else:
		stock_price = 0
	stock_number = row[u'stock_number']  # number should always be positive
	if stock_number != u'---':
		#print stock_number, type(stock_number)
		stock_number = abs(float(stock_number))
	else:
		stock_number = 0

	deal_amount = 0
	if 'deal_amount' in row.index:
		deal_amount = float(row[u'deal_amount']) # optional
	elif operation not in ['buy (bond repurchase)', 'sell (bond repurchase)']:
		deal_amount = stock_number * stock_price

	actual_amount = 0
	if 'actual_amount' in row.index:
		if not math.isnan(row[u'actual_amount']):
			actual_amount = float(row[u'actual_amount'])
	else:
		actual_amount = deal_amount

	remain_amount = 0
	if 'remain_amount' in row.index:
		remain_amount = float(row[u'remain_amount'])
	else:
		account.has_remain_amount_column = False


	#print deal_date, deal_time, stock_code, stock_name, operation, stock_price, stock_number, actual_amount, remain_amount

	if is_first_row:
		init_cash = remain_amount-actual_amount
		if row['operation'] == 'stock in':  # 如果第一笔操作是担保转入，直接用剩余金额，不能减去发生金额
			init_cash = remain_amount
		account.set_init_cash(init_cash)
		account.set_init_date(deal_date)
		print 'first row, init_cash %f, init_date %s' % (init_cash, deal_date)

	account.set_date(deal_date)

	if 'remain_stock' in row.index:
		remain_stock = row[u'remain_stock']  # number should always be positive
		if remain_stock != u'---':
			#print stock_number, type(stock_number)
			remain_stock = abs(float(remain_stock))
		else:
			remain_stock = 0
		process_init_position(account, remain_stock, stock_number, stock_code, stock_name, operation)

	if operation == 'buy':
		account.buy_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation == 'buy (new stock)':
		account.buy_new_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation == 'buy (bond repurchase)':
		#print '===========',row
		SinaQuote.setGC001Price(stock_code, stock_number, deal_amount, actual_amount)
		stock_price = SinaQuote.getGC001Price(stock_code)
		#print stock_code,stock_number,stock_price
		account.buy_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)		
	elif operation == 'sell':
		account.sell_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation == 'sell (bond repurchase)':
		#print '===========',row
		SinaQuote.setGC001Price(stock_code, stock_number, deal_amount, actual_amount)
		stock_price = SinaQuote.getGC001Price(stock_code)
		#print stock_code,stock_number,stock_price
		account.sell_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	
	elif operation == 'short':
		account.short_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation == 'cover':
		account.cover_stock(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	
	elif operation == 'direct return':
		account.direct_return(deal_date, stock_code, stock_name, stock_number, stock_price)
	elif operation == 'stock in':
		account.stock_in(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation == 'stock out':
		account.stock_out(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)

	elif operation == 'fenji fund split':
		stock_price = SinaQuote.getLastClosePrice(stock_code, deal_date)
		actual_amount = float(stock_price * stock_number)
		account.stock_in(deal_date, stock_code, stock_name, stock_number, stock_price, actual_amount)
	elif operation in ['bank in money', 'bank out money', 'bank transfer']:
		account.bank_transfer(actual_amount)
	elif operation == 'borrow cash':
		account.borrow_cash(actual_amount)
	elif operation == 'return cash':
		account.return_cash(actual_amount)
	elif operation == 'pay interest':
		account.pay_interest(actual_amount)
	elif operation == 'pay tax':
		account.pay_tax(actual_amount)	
	elif operation == 'earn interest':
		account.earn_interest(actual_amount)
	elif operation == 'earn stock':
		account.earn_stock(deal_date, stock_code, stock_name, stock_number)
	elif operation == 'earn stock interest':
		if stock_number != 0 and actual_amount == 0:
			account.earn_stock(deal_date, stock_code, stock_name, stock_number)
		elif actual_amount != 0 and stock_number == 0:
			account.earn_interest(actual_amount)
		else:
			print '!!!! error earn stock interest, stock_number %f deal_amount %f' % (stock_number, actual_amount)
	elif operation == 'init position':
		account.add_init_position(stock_code, stock_name, stock_number)
	elif operation == 'init rongquan position':
		account.add_init_rongquan_position(stock_code, stock_name, stock_number)
	elif operation.startswith('todo:'):
		print '==== todo: row %s' % row
	elif operation.startswith('pass:'):
		pass
	else:
		print '!!!! unknown operation %s row %s' % (operation, row)		


def report():
	inops = pd.Series(in_operation)
	print inops.value_counts()
	print "==========="
	outops = pd.Series(out_operation)
	print outops.value_counts()
	print "==========="

	outbiz = pd.Series(out_business)
	print outbiz.value_counts()




