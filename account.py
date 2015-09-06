# -*- coding: utf-8 -*-
import datetime
import math
from position import StockPosition
import pandas as pd
import SinaQuote
from compute import format_number

class Account:
	def __init__(self, account_init_position = None):
		self.first_day = 20140101
		if account_init_position != None:
			self.stock_position = account_init_position.get_init_stock_position()
			self.rongquan_position = account_init_position.get_init_rongquan_position()
			self.stock_value = self.stock_position.getPositionValue(self.first_day)
			self.rongquan_value = self.rongquan_position.getPositionValue(self.first_day)
			self.init_position_value = self.stock_value + self.rongquan_value
			self.init_cash = account_init_position.get_init_cash()
			self.fund_units = self.init_position_value + self.init_cash
			#self.net_total = self.fund_units # 净资产规模，融资融券要减掉
			self.cash = self.init_cash
			self.total_w_rzrq = self.stock_value + abs(self.rongquan_value) + self.cash
		else:
			self.init_position_value = 0
			self.init_cash = 0
			self.fund_units = 0
			self.total_w_rzrq = 0
			#self.net_total = 0
			self.cash = 0
			self.stock_position = StockPosition()
			self.rongquan_position = StockPosition()
			self.rongquan_position.is_rongquan = True
			self.stock_value = 0
			self.rongquan_value = 0

		self.net_value = 1  # 净值初始为1
		self.stock_code_name_map = {} 
		self.old_date = ''
		self.current_date = ''
		self.negative_max_cash = 0
		self.has_remain_amount_column = True # 默认有剩余金额
		#self.account_type = u'普通账户' # or '信用账户'

		## statistics ##
		self.total_debt_interest = 0 # 融资融券产生的全部利息
		self.buy_sell_count = 0 # 股票买卖次数
		#self.cash_debt = 0 # 融资借入金额
		self.init_position_stock_code_map = {} # 用于标记是否已计算过初始持仓

	def add_init_position_stock_code(self, stock_code):
		self.init_position_stock_code_map[stock_code] =1


	def set_init_cash(self, init_cash):
		self.init_cash = init_cash

	def get_init_cash(self):
		return self.init_cash

	def calculate_init_cash_if_no_remain_amount(self, df):
		if self.has_remain_amount_column == False:
			if 'actual_amount' in df.columns:
				df['cs'] = df['actual_amount'].cumsum()
				self.init_cash = -df['cs'].min()
			else:
				self.init_cash = -self.negative_max_cash

	def set_init_date(self, date):
		self.init_date = date

	def get_init_date(self):
		return self.init_date

	def set_date(self, date):
		self.current_date = date

	def get_date(self):
		return self.current_date

	def get_datetime(self):
		d = int(self.current_date)
		return datetime.datetime(d/10000, d%10000/100, d%100)

	def calculate_init_nv(self):
		if self.fund_units == 0:
			return

	def calculate_nv(self, date=None):
		if self.fund_units == 0:
			return 
		if date == None:
			date = self.current_date

		self.stock_value = self.stock_position.getPositionValue(date)
		self.rongquan_value = self.rongquan_position.getPositionValue(date)
		self.total_w_rzrq = self.stock_value + self.cash + self.rongquan_value
		# rely on cash_debt and rongquan_value to be positive or negative number
		#self.net_total = self.stock_value + self.cash + self.cash_debt + self.rongquan_value
		if self.total_w_rzrq == 0:
			print '!!! total become 0, do not change nv, set fund_units to 0'
			self.fund_units = 0
		else:
			self.net_value = float(self.total_w_rzrq) / self.fund_units
		
	def get_profit_detail(self, date=None):
		(profit_sum_list, df_list) = self.stock_position.get_profit_detail(date)
		(profit_sum_list1, df_list1) = self.rongquan_position.get_profit_detail(date) 
		profit_sum_list += profit_sum_list1
		df_list += df_list1
		return (profit_sum_list, df_list)

	#def report(self):
	#	return "%s total %f stock value %f rongquan %f cash %f nv %f units %f" % \
	#		(self.current_date, self.total, self.stock_value, self.rongquan_value, self.cash, self.net_value, self.fund_units)

	def report_position_detail(self):
		print self.stock_position.report(self.current_date)
		print self.rongquan_position.report(self.current_date)

	def get_position_dataframe(self, date):
		df = self.stock_position.get_position_dataframe(date)
		df1 = self.rongquan_position.get_position_dataframe(date)
		return pd.concat([df, df1])

	def get_status_data(self):
		total_profit = self.stock_position.calculate_total_profit(self.current_date) +\
			self.rongquan_position.calculate_total_profit(self.current_date)
		return (self.current_date, round(self.total_w_rzrq, 2), round(self.stock_value, 2), 
				round(self.rongquan_value, 2), round(self.cash, 2), 
				round(self.net_value, 4), round(self.fund_units, 2), round(total_profit, 2), round(self.total_debt_interest, 2))

	def get_status_columns(self):
		return [u'日期', u'总资产', u'股票市值', u'融券市值', u'现金', u'净值', u'份额', u'累计赢利', u'累计利息']

	def print_position(self):
		print "stock_position:\n%s" % self.stock_position.report(self.current_date)
		print "rongquan_position:\n%s" % self.rongquan_position.report(self.current_date)

	def print_init_position(self):
		print "stock init position:\n%s" % self.stock_position.get_init_position().report(self.current_date)
		print "rongquan init position:\n%s" % self.rongquan_position.get_init_position().report(self.current_date)
		
	def calculate_init_position_value(self, date):
		return self.stock_position.get_init_position().getPositionValue(date)+\
			self.rongquan_position.get_init_position().getPositionValue(date) 

	def get_init_stock_position(self):
		return self.stock_position.get_init_position()

	def get_init_rongquan_position(self):
		return self.rongquan_position.get_init_position()

	def get_init_position_dataframe(self):
		df1 = self.stock_position.get_init_position().get_position_dataframe(self.first_day)
		df2 = self.rongquan_position.get_init_position().get_position_dataframe(self.first_day)
		return pd.concat([df1, df2])

	def save_stock_code_name(self, stock_code, stock_name):
		if self.stock_code_name_map.get(stock_code) == None:
			self.stock_code_name_map[stock_code] = stock_name

	def borrow_cash(self, amount):
		self.add_minus_cash( abs(amount) )
		self.fund_units += abs(amount) / self.net_value
		#self.cash_debt += abs(amount)
		#print 'borrow',amount,self.cash_debt

	def return_cash(self, amount):
		self.add_minus_cash( -abs(amount) )
		self.fund_units -= abs(amount) / self.net_value
		#self.cash_debt -= abs(amount)
		#print 'return',amount,self.cash_debt

	def pay_interest(self, amount):
		self.add_minus_cash( -abs(amount) )
		self.total_debt_interest += abs(amount)

	def earn_interest(self, amount):
		self.add_minus_cash( abs(amount) )

	def pay_tax(self, amount):
		self.add_minus_cash( -abs(amount) )

	def bank_transfer(self, amount):  # rely on amount to be + or -
		self.add_minus_cash( amount )
		self.fund_units += float(amount) / self.net_value

	def bank_in_money(self, amount):
		self.add_minus_cash( abs(amount) )
		self.fund_units += abs(amount) / self.net_value

	def bank_out_money(self, amount):
		self.add_minus_cash( -abs(amount) )
		self.fund_units -= abs(amount) / self.net_value

	# stock_in = bank_in_money + buy_stock
	def stock_in(self, date, stock_code, stock_name, stock_number, price, actual_amount):  # 担保划入
		#print 'stock in:', stock_name,stock_number
		if math.isnan(price) or price == 0:
			price = SinaQuote.getLastClosePrice(stock_code, date)
		if math.isnan(actual_amount) or actual_amount == 0:
			actual_amount = stock_number * price
		self.bank_in_money(actual_amount)
		self.buy_stock(date, stock_code, stock_name, stock_number, price, actual_amount)
		#print self.cash, actual_amount, self.fund_units, self.net_value
		#print date, stock_code, stock_name, stock_number, price, actual_amount
		#self.save_stock_code_name(stock_code, stock_name)
		#self.stock_position.add(date, stock_code, stock_name, stock_number, price)
		# 净值不变，份额增加
		#self.fund_units += actual_amount / self.net_value

	# stock_out = sell_stock + bank_out_money
	def stock_out(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		#print 'stock out:', stock_name,stock_number
		if price == 0:
			price = SinaQuote.getLastClosePrice(stock_code, date)
		if actual_amount == 0:
			actual_amount = stock_number * price
		self.sell_stock(date, stock_code, stock_name, stock_number, price, actual_amount)
		self.calculate_nv()  # !!! need this because after sell stock nv will change !!!
		self.bank_out_money(actual_amount)
		#print self.cash, actual_amount, self.fund_units, self.net_value

	def stock_transfer(self, date, stock_code, stock_name, stock_number):  # 协议转让
		self.save_stock_code_name(stock_code, stock_name)
		price = SinaQuote.getLastClosePrice(stock_code, date)
		self.stock_position.minus(date, stock_code, stock_name, stock_number, price, 7) # 操作类型7是转出
		# 现金不增加，份额减少
		self.fund_units -= float(stock_number * price) / self.net_value

	def earn_stock(self, date, stock_code, stock_name, stock_number):
		#print date, stock_code, stock_name, stock_number
		self.save_stock_code_name(stock_code, stock_name)
		price = 0 # 红利股票成本为0
		self.stock_position.add(date, stock_code, stock_name, stock_number, price, 6) # 操作类型6是分红

	def buy_stock(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		self.save_stock_code_name(stock_code, stock_name)
		self.stock_position.add(date, stock_code, stock_name, stock_number, price, 1) # 操作类型1是买入
		self.add_minus_cash( -abs(actual_amount) )
		self.buy_sell_count += 1

	def buy_new_stock(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		cd = SinaQuote.getNewStockCode(stock_code)
		if cd != '':
			stock_code = cd
		self.buy_stock(date, stock_code, stock_name, stock_number, price, actual_amount)
		self.buy_sell_count += 1

	def sell_stock(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		self.save_stock_code_name(stock_code, stock_name)
		self.stock_position.minus(date, stock_code, stock_name, stock_number, price, 2) # 操作类型2是卖出
		self.add_minus_cash( abs(actual_amount) )
		self.buy_sell_count += 1

	def short_stock(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		self.save_stock_code_name(stock_code, stock_name)
		self.rongquan_position.minus(date, stock_code, stock_name, stock_number, price, 4) # 操作类型4是做空
		self.add_minus_cash( abs(actual_amount) )
		self.buy_sell_count += 1
		
	def cover_stock(self, date, stock_code, stock_name, stock_number, price, actual_amount):
		self.save_stock_code_name(stock_code, stock_name)
		self.rongquan_position.add(date, stock_code, stock_name, stock_number, price, 5) # 操作类型5是平仓
		self.add_minus_cash( -abs(actual_amount) )
		self.buy_sell_count += 1

	def direct_return(self, date, stock_code, stock_name, stock_number, price):
		actual_amount = stock_number*price
		self.sell_stock(date, stock_code, stock_name, stock_number, price, actual_amount)
		self.cover_stock(date, stock_code, stock_name, stock_number, price, actual_amount)

	def add_minus_cash(self, amount):
		self.cash = self.cash + amount
		if self.cash < self.negative_max_cash:
			self.negative_max_cash = self.cash

	def add_init_position(self, stock_code, stock_name, stock_number):
		self.stock_position.add_init_position(stock_code, stock_name, stock_number)


	def add_rongquan_init_position(self, stock_code, stock_name, stock_number):
		stock_number = -abs(stock_number)
		self.rongquan_position.add_init_position(stock_code, stock_name, stock_number)



def test1():
	a = Account()
	a.buy_stock(20140101, '600000', 'pfyh', 100, 1, 100)
	a.buy_stock(20140102, '600000', 'pfyh', 200, 2, 400)
	a.sell_stock(20140103, '600000', 'pfyh', 150, 3, 450)
	
	(profit_sum_list, profit_list, pcolumns) = a.calculate_profit(20141231)
	print profit_list
	print pcolumns
	profit_pd = pd.DataFrame(data=profit_list, columns=pcolumns)
	print profit_pd

if __name__ == '__main__':

	print format_number(11111111111.111111, 2)
	print format_number(11111111111.111111, 4)
	print format_number(11111111111.111111, 1)
