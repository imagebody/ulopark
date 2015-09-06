# -*- coding: utf-8 -*-

import re
import pandas as pd
import os
import math
import normalize

match_stock = u'([\u4e00-\u9fa5]{4,5})([0-9]{6})([\u4e00-\u9fa50-9A-Z\uff21 ]+)'
match_bank = u'(银行转(取|存))\[[\u4e00-\u9fa5]+\]'


stock_name_code_map = {} 

def save_stock_name_code(stock_name, stock_code):
	if stock_code == u'159919':
		stock_name = u'sz'+stock_name
	stored_code = stock_name_code_map.get(stock_name)
	if stored_code == None:
		stock_name_code_map[stock_name] = stock_code
	elif stored_code != stock_code:
		print 'stored code is not same: %s %s %s' % (stock_name, stock_code, stored_code)

	elif stored_code == stock_code:
		pass
	else:
		print '!!! error in huatai_rzrq.save_stock_name_code()'


def get_stock_code(stock_name):
	if stock_name == u'300ETF':
		stock_name = u'sz'+stock_name
	return stock_name_code_map.get(stock_name)

def get_required_rows_from_cash_flow():
	f = 'huatai_rzrq_cash_flow.xls'
	if not os.path.isfile(f):
		print 'no huatai cash flow file, skip ...'
		return (None, 0)
	flow_records = normalize.parse_file(f)
	flow_records.rename(columns={u'日期':u'成交日期', u'资金余额':u'本次金额'}, inplace=True)
	flow_records = flow_records.fillna(0)
	flow_records[u'发生金额'] = flow_records[u'借方(收入)'] - flow_records[u'贷方(支出)']
	flow_records['need_merge'] = False

	for i,row in flow_records.iterrows():
		zhaiyao = row[u'摘要']
		if re.match(match_stock, zhaiyao):
			result = re.match(match_stock, zhaiyao)
			operation = result.group(1)
			stock_code = result.group(2)
			stock_name = result.group(3)
			save_stock_name_code(stock_name, stock_code)
			#print operation,type(stock_code),stock_code,type(stock_name),stock_name
		elif re.match(match_bank, zhaiyao):
			result = re.match(match_bank, zhaiyao)
			operation = result.group(1)
			flow_records.loc[i, u'摘要'] = operation
			flow_records.loc[i, 'need_merge'] = True
		elif zhaiyao in [u'直接偿还融资利息', u'卖券偿还融资负债', u'卖券偿还融资利息', u'直接偿还融资负债', u'直接偿还融资费用', u'融资借款', u'卖券偿还融资费用', u'买券偿还融券利息', u'利息归本', u'股息红利税补缴']:
			flow_records.loc[i, 'need_merge'] = True
		else:
			print 'unknown row: %s' % row

	df = flow_records[flow_records['need_merge']==True].copy()
	df[u'发生金额'] = df[u'借方(收入)'] - df[u'贷方(支出)']
	return df




def merge_rzrq_cash_and_stock_flow():
	cash_flow_records = get_required_rows_from_cash_flow()
	if cash_flow_records is None:
		return ''

	f1 = 'rzrq.xls'
	stock_flow_records = normalize.parse_file(f1)
	stock_flow_records[u'证券代码'] = u''
	for i, row in stock_flow_records.iterrows():
		stock_name = row[u'证券名称']
		if type(stock_name) is float and math.isnan(stock_name):
			pass
		else:
			stock_code = get_stock_code(stock_name)
			stock_flow_records.loc[i, u'证券代码'] = stock_code
			stock_number = abs(row[u'成交数量'])
			stock_flow_records.loc[i, u'成交数量'] = stock_number

	
	#stock_flow_records[u'成交日期'] = stock_flow_records[u'成交日期'].astype(int)
	#merge
	stock_flow_records['index'] = stock_flow_records.index
	cash_flow_records['index'] = cash_flow_records.index
	merged_flow_records = pd.concat([stock_flow_records, cash_flow_records])
	sm = merged_flow_records.sort([u'成交日期', 'index']).reset_index()
	rtn_file = u'华泰融资融券账户_merged.xls'
	sm.to_excel(rtn_file, encoding='gbk')
	return rtn_file

def test():
	f = 'huatai_rzrq_cash_flow.xls'
	if not os.path.isfile(f):
		print 'no huatai cash flow file, skip ...'
		return (None, 0)
	flow_records = normalize.parse_file(f)
	flow_records['is_stock'] = False
	for i,row in flow_records.iterrows():
		zhaiyao = row[u'摘要']
		if re.match(match_stock, zhaiyao):
			result = re.match(match_stock, zhaiyao)
			operation = result.group(1)
			stock_code = result.group(2)
			stock_name = result.group(3)
			flow_records.loc[i, 'is_stock'] = True

	is_stock = flow_records['is_stock'] == True
	df = flow_records[is_stock]
	df.to_excel('is_stock.xls', encoding='gbk')




if __name__ == '__main__':
	#merge_rzrq_cash_and_stock_flow()
	#get_required_rows_from_cash_flow()
	test()

