# -*- coding: utf-8 -*-


import os
from sys import argv
import SinaQuote

total_value = 0
total_value_1 = 0

def get_value(date):
	total_value = 0
	for line in open(argv[1]):
		r = line.split(',')
		#print r[1][4:-1]
		stock_number = int(r[6])
		stock_cd = r[1][4:-1]
		last_price = SinaQuote.getLastClosePrice(stock_cd, date)
		print stock_cd, stock_number, last_price
		value = stock_number * last_price 
		total_value += value
	return total_value

day1 = get_value(20150302)+37266.45
day2 = get_value(20150303)+37266.45

print day1, day2, day2-day1, (day2-day1)/day1

#if __name__ == '__main__':


