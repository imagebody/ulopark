# -*- coding: utf-8 -*-

import re
import os.path
import pandas as pd
import normalize
import SinaQuote

match_borrow_cash = u'融资买入借款'
match_interest_in = u'结息入账,积数:.*'
search_bank_in_money = u'银行转帐转入'
search_bank_out_money = u'银行转帐转出'
match_rzrq_in = u'([a-zA-Z\d]+)([\u4e00-\u9fa5]{4})([\u4e00-\u9fa50-9A-Z\uff21 ]+)\(([\d]+)\)([\d]+)\u80a1\*([\d\.]+)'
match_new_stock = u'([a-zA-Z\d]*)(申购(扣款|还款|中签款))\(([\d]+)\)[ ]*([\d]+)[\u80a1]?\*([\d\.]+)'
match_rzrq_out = u'([\u4e00-\u9fa5]+):([a-zA-Z\d]+)([\u4e00-\u9fa5]{4})([\u4e00-\u9fa5\uff21\sXDR]+)\(([\d]+)\)([\d]+)\u80a1\*([\d\.]+),[\u4e00-\u9fa5]+:[\d]*'
match_rzrq_return = u'([\u4e00-\u9fa5]+):信用还款日终入账,委托号:[\d]+'
match_rzrq_pay_interest = u'([\u4e00-\u9fa5]+):偿还融资利息,合约流水号:[\d]+'
match_hongli = u'([\d]+)红利到帐'
match_hongli1 = u'[a-zA-Z\d]+领[\d]+红利[\d]+股*.+'
search_tax = u'股息差别税'
search_shenshu = u'申赎.+替代现金退款'
match_stock_in = u'([\d]+) ([\u4e00-\u9fa5]+) ([\d]+) ([\d]+)'


def get_init_cash_from_cash_flow(row):
	return float(row[u'剩余金额'])-float(row[u'发生金额'])


def pre_process_cash_flow():
	f = 'dongxing_rzrq_cash_flow.xls'
	df = normalize.parse_file(f)
	init_cash = get_init_cash_from_cash_flow(df.iloc[0])

	df[u'证券代码'] = ''
	df[u'证券名称'] = ''
	df[u'成交价格'] = 0
	df[u'成交数量'] = 0

	for i, row in df.iterrows():
		parse_operation(i, row, df)


	return (df, init_cash)

def parse_operation(i, row, df):
	deal_date = row[u'成交日期']
	deal_time = row[u'成交时间']
	deal_mark = row[u'买卖标志']
	actual_amount = row[u'发生金额']
	remain_amount = row[u'剩余金额']
	zhaiyao = row[u'摘要']

	if re.match(match_borrow_cash, zhaiyao):
		df.loc[i, u'买卖标志'] = u'融资借款'
	elif re.match(match_interest_in, zhaiyao):
		df.loc[i, u'买卖标志'] = u'结息入账'
	elif re.search(search_bank_in_money, zhaiyao):
		df.loc[i, u'买卖标志'] = u'银行转入'
	elif re.search(search_bank_out_money, zhaiyao):
		df.loc[i, u'买卖标志'] = u'银行转出'
	elif re.match(match_hongli, zhaiyao) or re.match(match_hongli1, zhaiyao) or re.search(search_shenshu, zhaiyao):
		df.loc[i, u'买卖标志'] = u'红利'
	elif re.search(search_tax, zhaiyao):
		df.loc[i, u'买卖标志'] = u'股息差别税'
	elif re.match(match_rzrq_in, zhaiyao):
		result = re.match(match_rzrq_in, zhaiyao)
		operation = result.group(2)
		stock_name = result.group(3)
		stock_code = result.group(4)
		stock_number = float(result.group(5))
		stock_price = float(result.group(6))
		df.loc[i, u'买卖标志'] = operation
		df.loc[i, u'证券代码'] = stock_code
		df.loc[i, u'证券名称'] = stock_name
		df.loc[i, u'成交价格'] = stock_price
		df.loc[i, u'成交数量'] = stock_number
		if operation not in [u'融资买入', u'信用买入', u'卖券还款', u'信用卖出', u'融券卖出', u'买券还券']:
			print '!!!error operation %s row:\n%s' % (operation, row)

	elif re.match(match_new_stock, zhaiyao):
		result = re.match(match_new_stock, zhaiyao)
		#print result.groups()
		operation = result.group(2)
		stock_code = result.group(4)
		stock_number = float(result.group(5))
		stock_price = float(result.group(6))
		stock_name = SinaQuote.getNewStockName(stock_code)
		df.loc[i, u'买卖标志'] = operation
		df.loc[i, u'证券代码'] = stock_code
		df.loc[i, u'证券名称'] = stock_name
		df.loc[i, u'成交价格'] = stock_price
		df.loc[i, u'成交数量'] = stock_number		
		if operation not in [u'申购扣款', u'申购还款', u'申购中签款']:
			print '!!!error operation %s row:\n%s' % (operation, row)

	elif re.match(match_rzrq_out, zhaiyao):
		result = re.match(match_rzrq_out, zhaiyao)
		operation = result.group(1)
		operation1 = result.group(3)
		stock_name = result.group(4)
		stock_code = result.group(5)
		stock_number = float(result.group(6))
		stock_price = float(result.group(7))
		df.loc[i, u'买卖标志'] = operation
		df.loc[i, u'证券代码'] = stock_code
		df.loc[i, u'证券名称'] = stock_name
		df.loc[i, u'成交价格'] = stock_price
		df.loc[i, u'成交数量'] = stock_number		
		#print 'ou' + operation + stock_name + stock_code + stock_number + stock_price
		if operation not in [u'卖券偿还本金', u'卖出偿还本金', u'卖券偿还融资利息', u'卖券偿还融券费用', u'卖出偿还利息', u'偿还融资其它费用']:
			print '!!!error operation %s row:\n%s' % (operation, row)
	elif re.match(match_rzrq_return, zhaiyao):
		result = re.match(match_rzrq_return, zhaiyao)
		operation = result.group(1)
		df.loc[i, u'买卖标志'] = operation
		if operation not in [u'偿还本金', u'偿还融资利息', u'偿还融券费用']:
			print '!!!error operation %s row:\n%s' % (operation, row)	
	elif re.match(match_rzrq_pay_interest, zhaiyao):
		df.loc[i, u'买卖标志'] = u'偿还融资利息'
	else:
		print '!!!! unknown row %s' % row



def merge_rzrq_cash_and_stock_flow():
	stock_flow_df = get_required_rows_from_stock_flow()
	#print stock_flow_df
	if stock_flow_df is None:
		return ''
	(cash_flow_df, init_cash) = pre_process_cash_flow()

	cash_flow_df[u'成交日期'] = cash_flow_df[u'成交日期'].astype(int)
	stock_flow_df[u'成交日期'] = stock_flow_df[u'成交日期'].astype(int)

	merged_flow_records = pd.concat([cash_flow_df, stock_flow_df])
	sm = merged_flow_records.sort([u'成交日期', u'成交时间']).reset_index()
	sm.rename(columns={u'摘要':u'东兴摘要'}, inplace=True)
	if pd.isnull( sm.iloc[0][u'剩余金额'] ):
		sm.loc[0, u'剩余金额'] = init_cash + float(sm.iloc[0][u'发生金额']) 

	rtn_file = '东兴融资融券账户_merged.xls'
	sm.to_excel(rtn_file, encoding='gbk')
	return rtn_file



def get_required_rows_from_stock_flow():
	f = 'rzrq.xls'
	f1 = 'other_rzrq.xls'
	if os.path.isfile(f) and not os.path.isfile(f1):	
		df = normalize.parse_file(f)
		is_stock_in = df[u'买卖标志'] == u'担保划入'
		df[u'成交编号'] = df[u'成交编号'].astype(unicode)
		is_stock_in1 = df[u'成交编号'] == u'担保品提交'
		is_stock_in11 = df[u'成交编号'] == u'担保物提交'
		is_1 = is_stock_in & (is_stock_in1 | is_stock_in11)
		is_2 = df[u'买卖标志'] == u'红股入账'
		df[u'成交日期'] = df[u'成交日期'].astype(unicode)
		return df[is_1 | is_2]
	elif os.path.isfile(f1):
		print f1
		df = normalize.parse_file(f1)
		is_stock_in = df[u'交易类别'] == u'担保划入'
		is_stock_in1 = df[u'交易类别'] == u'送股'
		is_stock_in2 = df[u'交易类别'] == u'托管转入'
		df1 = df[is_stock_in | is_stock_in1 | is_stock_in2].copy()
		df1.rename(columns={u'交易类别':u'买卖标志'}, inplace=True)
		return df1

	else:
		print 'no stock flow file, skip...'
		return None

