# -*- coding: utf-8 -*-

import SinaQuote
import types
import pandas as pd
import compute

class Stock:
	def __init__(self, date, code, name, number, price, op_type):
		self.stock_code = code
		self.stock_name = name
		self.stock_number = float(number)
		if price == 0:
			price = SinaQuote.getLastClosePrice(code, date)
		self.position_flow = [ (date, number, price, op_type) ]

	def output(self):
		print "stock_code %s stock_name %s stock_number %d" % (self.stock_code, self.stock_name, self.stock_number)

	def report(self):
		return "stock_code %s stock_name %s stock_number %d" % (self.stock_code, self.stock_name, self.stock_number)

	def reportValue(self, date):
		return "stock_code %s stock_name %s stock_number %d stock_value %f" % (self.stock_code, self.stock_name, self.stock_number, self.getValue(date))

	def add(self, date, stock_number, price, op_type):
		self.position_flow.append( (date, stock_number, price, op_type) )
		self.stock_number += stock_number

	def minus(self, date, stock_number, price, op_type):
		self.position_flow.append( (date, -stock_number, price, op_type) )
		self.stock_number -= stock_number

	def getValue(self, date):
		closePrice = SinaQuote.getLastClosePrice(self.stock_code, date)
		value = 0;
		if closePrice == -1:
			print "!!!error: getClosePrice %s %s error" % (self.stock_code, date)
		else:
			value = closePrice * self.stock_number
		return value

	def get_position(self):
		return (self.stock_code, self.stock_name, self.stock_number)

	def get_init_position(self, is_rongquan=False):
		#if self.stock_code == u'000402' and is_rongquan:
		#	print self.position_flow
		max_number = 0   # 买卖股票过程中产生的最大持仓值才是初始股票持仓
		total_number = 0
		for (date, number, price, op_type) in self.position_flow:
			total_number += number
			if total_number<0 and total_number<max_number and is_rongquan==False:
				max_number = total_number
			if total_number>0 and total_number>max_number and is_rongquan==True:
				max_number = total_number
		return max_number

	def calculate_profit(self, last_date, is_rongquan=False):

		stock_count = 0
		stock_cost = 0
		profit_total = 0
		profit_list = []
		for (date, number, price, op_type) in self.position_flow:
			profit = 0
			if (number>0 and is_rongquan==False) or (number<0 and is_rongquan==True):
				if stock_cost == 0:
					stock_cost = price
				else:
					total = stock_count + number
					if total == 0:
						print is_rongquan
						for p in self.position_flow:
							print p
						print '!!! total stock number is 0, date %s stock_code %s stock_name %s number %d' % (date, self.stock_code, self.stock_name, number)
					stock_cost = float(stock_count*stock_cost + number*price) / (stock_count + number)
				stock_count += number
			elif (number<0 and is_rongquan==False) or (number>0 and is_rongquan==True):
				profit = (price - stock_cost)*(-number)
				profit_total += profit
				stock_count += number
			profit_list.append( (date, self.stock_code, self.stock_name, number, price, stock_count, stock_cost, profit, profit_total, op_type) )
		if stock_count != 0:
			last_price = SinaQuote.getLastClosePrice(self.stock_code, last_date)
			profit = stock_count * ( last_price - stock_cost)
			profit_total += profit
			profit_list.append( (last_date, self.stock_code, self.stock_name, 0, last_price, stock_count, stock_cost, profit, profit_total, 3) ) # 操作类型3是持仓
		columns = [u'日期', u'代码', u'名称', u'数量', u'价格', u'当前总持仓', u'当前成本', u'本次盈亏', u'总盈亏', u'操作类型']
		return (profit_total, profit_list, columns)

class StockPosition:
	def __init__(self):
		self.stock_code_name_map = {}
		self.stock = {}
		self.is_rongquan = False
		self.init_date = 20140101
		self.init_position = {}  # manually set init position

	def output(self):
		for stock_code, s in self.stock.items():
			s.output()

	def report(self, date):
		rtn = ''
		for stock_code, s in self.stock.items():
			if s.stock_number != 0:
				rtn += s.reportValue(date) + '\n'
		return rtn

	def get_profit_detail(self, date):
		profit_list = []
		profit_sum_list = []
		pcolumns = []
		df_list = []
		for stock_code, s in self.stock.items():
			(ptotal, plist, pcolumns) = s.calculate_profit(date, self.is_rongquan)
			df = pd.DataFrame(data=plist, columns=pcolumns)
			df_list.append(df)
			profit_sum_list.append( (s.stock_code, s.stock_name, ptotal ) )
		return (profit_sum_list, df_list)

	def calculate_total_profit(self, date):
		total_profit = 0
		for stock_code, s in self.stock.items():
			(ptotal, plist, pcolumns) = s.calculate_profit(date, self.is_rongquan)
			total_profit += ptotal
		return total_profit


	def add(self, date, stock_code, stock_name, stock_number, price, op_type):
		s = self.stock.get(stock_code, None)
		if s != None:
			self.stock[stock_code].add(date, stock_number, price, op_type)
		else:
			s1 = Stock(date, stock_code, stock_name, stock_number, price, op_type)
			self.stock[stock_code] = s1
		
	def minus(self, date, stock_code, stock_name, stock_number, price, op_type):
		s = self.stock.get(stock_code, None)
		if s != None:
			self.stock[stock_code].minus(date, stock_number, price, op_type)
		else:
			s1 = Stock(date, stock_code, stock_name, -stock_number, price, op_type)
			self.stock[stock_code] = s1
		
	def getPositionValue(self, date):
		value = 0
		for stock_code, s in self.stock.items():
			v = s.getValue(date)
			#print stock_code + ': ' + '{:.2f}'.format(v)
			value += v
		return value

	def add_init_position(self, stock_code, stock_name, stock_number):
		s = Stock(self.init_date, stock_code, stock_name, stock_number, price=0, op_type=compute.get_op_type('hold'))
		if stock_code not in self.init_position:
			self.init_position[stock_code] = s


	def get_init_position(self):
		init_p = StockPosition()
		if len(self.init_position)>0:
			for stock_code, s in self.init_position.items():
				init_p.add(self.init_date, stock_code, s.stock_name, s.stock_number, price=0, op_type=compute.get_op_type('hold'))
		else:
			if self.is_rongquan:
				init_p.is_rongquan = True
			for stock_code, s in self.stock.items():
				max_number = s.get_init_position(self.is_rongquan)
				if (max_number<0 and self.is_rongquan==False) or (max_number>0 and self.is_rongquan==True) :
					init_p.add(self.init_date, stock_code, s.stock_name, -max_number, price=0, op_type=compute.get_op_type('hold'))
		return init_p

	def get_position_dataframe(self, date):
		position_list = []
		for stock_code, s in self.stock.items():
			if s.stock_number != 0:
				price = SinaQuote.getLastClosePrice(stock_code, date)
				position_list.append([date, s.stock_code, s.stock_name, s.stock_number, price, s.stock_number*price])
		df = pd.DataFrame()
		if len(position_list) > 0:
			df = pd.DataFrame(data=position_list, columns=[u'日期', u'代码', u'名称', u'数量', u'价格', u'市值'])
		return df
			

if __name__ == '__main__':
	s = Stock(20140101, '600000', 'pfyh', 100, 1, u'买入');
	s.add(20140102, 200, 1, 'buy')
	#s.output()
	s.add(20140103, 100, 2, 'buy')
	s.minus(20140105, 55, 3, 'sell')
	print s.calculate_profit(20141231)
	#print s.getValue('20150205')

	a = StockPosition()
	#a.add('888888', 500, 3)
	a.add(20140101, '600000', 'pfyh', 400, 1, u'buy')
	a.add(20140102, '600000', 'pfyh', 200, 3, u'buy')
	a.minus(20140103, '600000', 'pfyh', 400, 2, u'sell')
	a.add(20140201, '600010', 'xxxx', 100, 1, u'buy')
	#a.output()
	print a.getPositionValue('20150205')
	print a.report(20150205)

	



