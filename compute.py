# -*- coding: utf-8 -*-

import urllib2
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sys import argv
from pandas.tseries.offsets import BDay


op_type_hash = {'buy':1, 'sell':2, 'hold':3, 'short':4, 'cover':5, 'honggu':6, 'transfer':7}

def get_op_type(op):
	type = op_type_hash.get(op, -1)
	if type==-1:
		print 'error'
	
	return type


def format_number(number, precise):
	s = '{:,.'+str(precise)+'f}'
	return s.format(number)

def max_dd(ser):
    max2here = pd.expanding_max(ser)
    #max2here.plot()
    dd2here_pct = (ser - max2here)/max2here
    #dd2here.plot()
    return dd2here_pct.min()

def get_qq_historic_data(ticker, years=['11']):
	hist_data_list = []	
	qq_url_pattern = 'http://data.gtimg.cn/flashdata/us/daily/{year}/us{ticker}.js'
	for year in years:
		url = qq_url_pattern.format(year=year, ticker=ticker)
		#print url
		hist_data = urllib2.urlopen(url).readlines()
		for day in hist_data[1:-1]:
			#print day
			#print day.rstrip().rstrip('\\n')
			values = day.rstrip().rstrip('\\n').split(' ') # date, open, close, high, low, volumn
			float_values = (float(x) for x in values)
			hist_data_list.append(float_values)
	return pd.DataFrame(data=hist_data_list, columns=['date', 'open', 'close', 'high', 'low', 'volumn'])


def annualised_sharpe(returns, N=252):
	"""
    Calculate the annualised Sharpe ratio of a returns stream 
    based on a number of trading periods, N. N defaults to 252,
    which then assumes a stream of daily returns.

    The function assumes that the returns are the excess of 
    those compared to a benchmark.
    """
	return np.sqrt(N) * returns.mean() / returns.std()

def equity_sharpe(ticker, years=['11']):
    """
    Calculates the annualised Sharpe ratio based on the daily
    returns of an equity ticker symbol listed in Yahoo Finance.

    The dates have been hardcoded here for the QuantStart article 
    on Sharpe ratios.
    """

    # Obtain the equities daily historic data for the desired time period
    # and add to a pandas DataFrame
    pdf = get_qq_historic_data(ticker, years)
    #print pdf

    # Use the percentage change method to easily calculate daily returns
    pdf['daily_ret'] = pdf['close'].pct_change()

    # Assume an average annual risk-free rate over the period of 5%
    pdf['excess_daily_ret'] = pdf['daily_ret'] - 0.05/252

    # Return the annualised Sharpe ratio based on the excess daily returns
    return annualised_sharpe(pdf['excess_daily_ret'])

def round4(x):
	x[u'当日收益率'] = round(x[u'当日收益率'], 4)
	return x

def nv_sharpe(pdf, n=245): # 245 trading days in 2014
	pdf[u'当日收益率'] = pdf[u'净值'].pct_change()
	pdf[u'当日超额收益率'] = pdf[u'当日收益率'] - 0.035/n  # risk free interest 0.035
	anv = annualised_sharpe(pdf[u'当日超额收益率'], n)
	del pdf[u'当日超额收益率']
	#pdf.apply(round4, axis=1)
	return anv

non_trading_day = [
20140101, 
20140131,
20140203,
20140204,
20140205,
20140206,
20140407,
20140501,
20140502,
20140602,
20140908,
20141001,
20141002,
20141003,
20141006,
20141007
]

def next_bday(process_day):
	process_day = (process_day+BDay()).to_datetime()
	while int(process_day.strftime('%Y%m%d')) in non_trading_day:
		process_day = (process_day+BDay()).to_datetime()
	return process_day




if __name__ == '__main__':
	#pd1 = pd.read_excel(argv[1], encoding='gbk')
	#s = pd1[u'净值']
	#s.plot()
	#plt.show()

	#print max_dd(s)
	total_years = ['07', '08', '09', '10', '11', '12', '13', '14', '15']
	#print equity_sharpe('GOOG.OQ', total_years)
	#print equity_sharpe('GS.N', total_years)
	#print equity_sharpe('AETI.OQ')
	#print equity_sharpe('NETE.OQ')
	#print equity_sharpe('ASPS.OQ')
	#print equity_sharpe('EGAN.OQ')
	#print equity_sharpe('GLNG.OQ')

	#get_qq_historic_data(1)

	print next_bday(datetime(2014,1,1))
	print next_bday(datetime(2014,1,30))
	print next_bday(datetime(2014,1,31))
	print next_bday(datetime(2014,2,4))
