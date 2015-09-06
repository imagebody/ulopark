# -*- coding: utf-8 -*-

import re
import pandas as pd
import os
import normalize

match_be0100_buy = u'BE0100申购确认,总申购[\d\.]+,确认金额:[\d\.]+'
match_be0100_sell = u'BE0100现金宝退出金额入帐'
match_be0100_hongli = u'基金红利发放:BE0100'
match_interest_in = u'结息入账,积数:.*'
search_bank_in_money = u'银行转帐转入'
search_bank_out_money = u'银行转帐转出'


def get_init_cash_from_cash_flow(row):
	return float(row[u'剩余金额'])-float(row[u'发生金额'])

def get_required_rows_from_cash_flow():
	f = 'dongxing_normal_cash_flow.xls'
	if not os.path.isfile(f):
		print 'no cash flow file, skip ...'
		return (None, 0)
	flow_records = normalize.parse_file(f)
	init_cash = get_init_cash_from_cash_flow(flow_records.iloc[0])

	del flow_records[u'币种']
	
	is_be0100 = flow_records[u'摘要'].str.contains('BE0100')
	is_interest_in = flow_records[u'摘要'].str.contains(u'结息入账,积数:')
	is_bank_transfer = flow_records[u'摘要'].str.contains(u'银行转帐转')


	df = flow_records[is_be0100 | is_interest_in | is_bank_transfer].copy()
	df[u'证券代码'] = ''
	df[u'证券名称'] = ''
	df[u'成交价格'] = 0
	df[u'成交数量'] = 0
	for i, row in df.iterrows():
		zhaiyao = row[u'摘要']
		if zhaiyao.find('BE0100') != -1:
			df.loc[i, u'证券代码'] = u'BE0100'
			df.loc[i, u'证券名称'] = u'现金宝'
			actual_amount = row[u'发生金额']
			df.loc[i, u'成交价格'] = 1
			if re.match(match_be0100_buy, zhaiyao):
				df.loc[i, u'委托类别'] = u'买入'
				df.loc[i, u'成交数量'] = -actual_amount
			elif re.match(match_be0100_sell, zhaiyao):
				df.loc[i, u'委托类别'] = u'卖出'
				df.loc[i, u'成交数量'] = -actual_amount
			elif re.search(match_be0100_hongli, zhaiyao):
				df.loc[i, u'委托类别'] = u'红利'
			else:
				print '!!! error unknown zhaiyao %s ' % zhaiyao
		elif zhaiyao.find(u'结息入账,积数:') != -1:
			df.loc[i, u'委托类别'] = u'利息归本'
		elif zhaiyao.find(u'银行转帐转入') != -1:
			df.loc[i, u'委托类别'] = u'银行转入' 
		elif zhaiyao.find(u'银行转帐转出') != -1:
			df.loc[i, u'委托类别'] = u'银行转出' 
		else:
			print '!!!! unknown row %s' % row	
	return (df, init_cash)



def merge_cash_stock_flow():
	f1 = 'normal.xls'
	stock_flow_records = normalize.parse_file(f1)
	for i, row in stock_flow_records.iterrows():
		if u'成交编号' not in row.index:
			print row
		if row[u'委托类别'] == u'其他' and row[u'成交编号'] == u'股息差别税':
			stock_flow_records.loc[i, u'委托类别'] = u'股息差别税'
		if row[u'委托类别'] == u'转托' and row[u'成交编号'] == u'转托管转入':
			stock_flow_records.loc[i, u'委托类别'] = u'股份转入'
		if row[u'委托类别'] == u'ETF申购' and row[u'成交编号'] == u'现金替代差额':
			stock_flow_records.loc[i, u'委托类别'] = u'ETF申购现金替代差额'
		if row[u'委托类别'] == u'托管转入' and row[u'成交编号'] == u'上市流通':
			stock_flow_records.loc[i, u'委托类别'] = u'新股上市流通'
		if row[u'委托类别'] == u'托管转出' and row[u'成交编号'] == u'上市转出':
			stock_flow_records.loc[i, u'委托类别'] = u'新股上市转出'
		if row[u'委托类别'] == u'股票回购':
			stock_flow_records.loc[i, u'委托类别'] = u'东兴股票质押融资'
		if row[u'委托类别'] == u'股票购回':
			stock_flow_records.loc[i, u'委托类别'] = u'东兴股票质押解除'
		if row[u'委托类别'] == u'直接还款':
			stock_flow_records.loc[i, u'委托类别'] = u'申购扣款'
		if row[u'委托类别'] == u'缴款' and row[u'成交编号'] == u'配股认购':
			stock_flow_records.loc[i, u'委托类别'] = u'配股认购'	

	stock_flow_records.rename(columns={u'成交编号':u'摘要'}, inplace=True)
	
	(cash_flow_records, init_cash) = get_required_rows_from_cash_flow()
	if cash_flow_records is None:
		return ''
	
	cash_flow_records[u'成交日期'] = cash_flow_records[u'成交日期'].astype(int)
	stock_flow_records[u'成交日期'] = stock_flow_records[u'成交日期'].astype(int)
	#merge
	merged_flow_records = pd.concat([cash_flow_records, stock_flow_records])

	sm = merged_flow_records.sort([u'成交日期', u'成交时间']).reset_index()

	if pd.isnull( sm.iloc[0][u'剩余金额'] ):
		actual_amount = 0
		if not pd.isnull( sm.iloc[0][u'发生金额'] ):
			actual_amount = float(sm.iloc[0][u'发生金额']) 
		else:
			sm.loc[0, u'发生金额'] = 0	
		sm.loc[0, u'剩余金额'] = init_cash + actual_amount
	sm.rename(columns={u'摘要':u'东兴摘要'}, inplace=True)
	rtn_file = u'东兴普通账户_merged.xls'
	sm.to_excel(rtn_file, encoding='gbk')
	return rtn_file
