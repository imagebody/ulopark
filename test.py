# -*- coding: utf-8 -*-


import os
from os import path
import pandas as pd
import analyze_account
from sys import argv
from brokers import normalize
import re
import analyze_account
import compute
import math
import SinaQuote

file_types = {
	'dongxing_normal_cash_flow': 
	[u'成交日期',u'成交时间',u'委托类别',u'发生金额',u'剩余金额',u'摘要',u'币种'],
	'dongxing_rzrq_cash_flow':
	[u'成交日期',u'成交时间',u'买卖标志',u'发生金额',u'剩余金额',u'摘要',u'币种']
}



def get_file_type(file):
	df = normalize.parse_file(file)
	column_list = [x for x in df.columns.values if not x.startswith('Unnamed:')]
	file_type = ''
	for t,l in file_types.items():
		if column_list == l:
			file_type = t

	if file_type == '':
		normalize.change_column_names(df)
		normalize.merge_zhaiyao_and_operation(df)
		if 'operation' in df.columns:
			for o in df['operation']:
				if o in [u'融资买入', u'融资利息扣款', u'融资利息']:
					file_type = 'rzrq'
			if file_type == '':
				file_type = 'normal'
		else:
			file_type = 'unknown!!!'

	return file_type

def remove_space(col):
	col = col.str.strip()
	return col

def test1():
	df = normalize.parse_file(argv[1])
	for i in df[u'业务名称   ']:
		print '='+i+'='
	df = df.apply(remove_space, axis=0)
	print '************'
	for i in df[u'业务名称   ']:
		print '='+i+'='

	df.to_excel('1.xls', encoding='gbk')

def compare_file():
	for line in open(argv[1]):
		a = line.split(' ')
		print a[0], re.sub('[\(\)0-9]','', a[1].strip())

def get_dir_names():
	for root, subdirs, files in os.walk(u'.'):
		for d in subdirs:
			(uid, name) = get_uid_name(d)
			print uid,name

def get_uid_name(dir_name):
	m = re.match(u'([\d]+)_?([^-_]+).*', dir_name)
	uid = m.group(1)
	name = m.group(2).decode('utf-8')
	return (uid, name)

def test_para(a,b,c=1,d='d'):
	print a,',',b,',',c,',',d

def rename_column():
	for line in open(argv[1]):
		a = line.split('\t')
		s = u''
		for c in a:
			s += 'u\''+c+'\','
		print s

def test_max_dd():
	df = normalize.parse_file(argv[1])
	ser = df[u'收盘']
	df['max2here'] = pd.expanding_max(ser)
	df['dd2here'] = ser - df['max2here']
	df['ddpct'] = df['dd2here'] / df['max2here']
	#df.to_excel('399300maxdd.xls',encoding='gbk')
	print '({data:['
	for i,row in df.iterrows():
		date=row[u'日期'].lstrip()
		date = date.replace('/', '-')
		print '{symbol:"399300",d:"'+date+'",h:'+'{:.2f}'.format(-row['ddpct']*100)+'},'
	
	(row_count, col_count) = df.shape
	print '],total:"'+str(row_count)+'"})'


def test2():
	df = normalize.parse_file(argv[1])
	for i,row in df.iterrows():
		if not pd.isnull(row[u'成交类别']):
			df.loc[i, u'买卖方向'] = row[u'成交类别']

	df.to_excel('stock_flow.xls', encoding='gbk')

def test3():
	df = normalize.parse_file(argv[1])
	df[u'买卖方向'] = u''
	df[u'证券代码'] = u''
	for i,row in df.iterrows():
		#print row[u'备注']
		s = re.match(u'(=")?([\u4e00-\u9fa5]+):?([\u4e00-\u9fa5]*)', row[u'备注'])
		df.loc[i, u'买卖方向'] = s.group(2)
		df.loc[i, u'证券代码'] = s.group(3)

	print df[u'买卖方向'].value_counts()
	print df[u'证券代码'].value_counts()
	#df.to_excel('cash_flow.xls', encoding='gbk')
	is_no_stock_name = df[u'证券代码'] == u''
	is_stock_name = df[u'证券代码'] != u''
	no_stock_df = df[is_no_stock_name].copy()
	stock_df = df[is_stock_name].copy()
	print no_stock_df[u'买卖方向'].value_counts()
	return (no_stock_df, stock_df, df)

def test4():
	df = normalize.parse_file(argv[2])
	print df[u'证券名称'].value_counts()
	return df

def test5():
	(cash_rows_no_stock, cash_rows_stock, cash_rows_all) = test3()
	cash_rows_no_stock.rename(columns={u'日期':u'成交日期'}, inplace=True)
	stock_rows = test4()
	print stock_rows.shape, cash_rows_stock.shape
	stock_rows[u'op'] = cash_rows_stock[u'买卖方向']
	stock_rows[u'name'] = cash_rows_stock[u'证券代码']
	all_rows =pd.concat([cash_rows_no_stock, stock_rows])
	sm = all_rows.sort([u'成交日期', u'序号']).reset_index()
	sm.to_excel('merged1.xls', encoding='gbk')

def test_merge():
	cash = normalize.parse_file('1.xlsx')
	cash['type'] = 'cash'
	stock = normalize.parse_file('2.xlsx')
	stock['type'] = 'stock'
	m = pd.merge(stock, cash, how='outer', on=[u'发生日期', u'发生金额']).sort([u'发生日期'])
	m.to_excel('m.xls', encoding='gbk')


def process_5379536715():
	cash_rows = normalize.parse_file(argv[1])
	match_pattern = u'([\u4e00-\u9fa5]+):(.*)'
	for i,row in cash_rows.iterrows():
		r = re.match(match_pattern, row[u'摘要'])
		if r!=None:
			operation = r.group(1)
			stock_name = r.group(2)
			cash_rows.loc[i, u'操作'] = operation
			cash_rows.loc[i, u'证券名称'] = stock_name
		else:
			print 'unknown row %s' % row
	cash_rows.to_excel('modi.xls', encoding='gbk') 

def reverse_order():
	rows = normalize.parse_file(argv[1])
	orows = rows.sort([u'成交日期', u'成交时间']).reset_index()
	orows.to_excel('modi.xls', encoding='gbk')

def get_actual_amount():
	rows = normalize.parse_file(argv[1])
	rows[u'发生金额'] = rows[u'收入金额'] - rows[u'付出金额']
	rows.to_excel('cash_flow.xls', encoding='gbk')

def test_max_dd():
	df = normalize.parse_file(argv[1])
	ser = df[u'净值']
	df['max2here'] = pd.expanding_max(ser)
	df['dd2here'] = ser - df['max2here']
	df['ddpct'] = df['dd2here'] / df['max2here']
	df.to_excel('max_dd.xls', encoding='gbk')

def process_zhanye():
	df = normalize.parse_file(u'资金流水.201503062221.xls')
	match_stock_pattern = u'([\u4e00-\u9fa5]{4,5})([0-9]{6})([\u4e00-\u9fa5\uff21 A-Z0-9]+)'
	df['operation'] = u''
	df['stock_code'] = u''
	df['stock_name'] = u''
	df['is_stock'] = False
	df[u'发生金额'] = 0
	for i,row in df.iterrows():
		income = row[u'借方(收入)'] 
		outcome = row[u'贷方(支出)']
		#print income,outcome
		if math.isnan(income):
			income = 0
		if math.isnan(outcome):
			outcome = 0
			#print income-outcome
		df.loc[i,u'发生金额'] = income-outcome

		if re.match(match_stock_pattern, row[u'摘要']) != None:
			r = re.match(match_stock_pattern, row[u'摘要'])
			operation = r.group(1)
			df.loc[i,'operation'] = operation
			stock_code = r.group(2)
			df.loc[i,'stock_code'] = stock_code
			stock_name = r.group(3)
			df.loc[i,'stock_name'] = stock_name
			df.loc[i,'is_stock'] = True
			#print operation,stock_code, stock_name
		elif re.match(u'(银行转存|银行转取)\[工行存管\]', row[u'摘要']) != None:
			r = re.match(u'(银行转存|银行转取)\[工行存管\]', row[u'摘要'])
			operation = r.group(1)
			df.loc[i,'operation'] = operation





	stock_df = df[df['is_stock'] == True]
	stock_df.to_excel('is_stock.xls', encoding='gbk')
	#not_stock_df = df[df['is_stock'] == False]
	#not_stock_df.to_excel('not_stock.xls', encoding='gbk')


def process_zhanye1():
	stock_flow = normalize.parse_file(u'2014.201503062156.xls')
	process_zhanye2(stock_flow)
	stock_flow['index'] = stock_flow.index
	cash_flow = normalize.parse_file('not_stock.xls')
	cash_flow['index'] = cash_flow.index
	all_flow = pd.concat([stock_flow, cash_flow]).sort([u'成交日期','index']).reset_index()
	all_flow.to_excel('合并处理后.xls',encoding='gbk')

def process_zhanye2(stock_flow):
	name_code_map={}
	is_stock = normalize.parse_file('is_stock.xls')
	for i,row in is_stock.iterrows():
		name_code_map[row['stock_name']] = row['stock_code']


	stock_flow[u'证券代码'] = u''
	for i,row in stock_flow.iterrows():
		name = row[u'证券名称']
		if not type(name) is unicode and math.isnan(name):
			pass
		else:
			stock_flow.loc[i,u'证券代码']=name_code_map[name]
		if row[u'摘要'] == u'直接还券':
			price = row[u'成交均价']
			number = row[u'成交数量']
			stock_flow.loc[i,u'成交金额'] = -price*number
			stock_flow.loc[i,u'发生金额'] = price*number


def process_zhanye3():
	not_stock = normalize.parse_file('not_stock.xls')
	for i,row in not_stock.iterrows():
		if re.match(u'(银行转存|银行转取)\[工行存管\]', row[u'摘要']) != None:
			r = re.match(u'(银行转存|银行转取)\[工行存管\]', row[u'摘要'])
			operation = r.group(1)
			not_stock.loc[i,u'摘要'] = operation
	not_stock.to_excel('not_stock.xls',encoding='gbk')

def process_cbond():
	df = normalize.parse_file(u'合并处理后.xls')
	for i,row in df.iterrows():
		stock_name = row[u'证券名称']
		stock_number = row[u'成交数量']
		if type(stock_name) is unicode and stock_name.endswith(u'转债'):
			df.loc[i,u'成交数量']=stock_number*10
	df.to_excel('合并处理后1.xls')

def merge():
	d1 = normalize.parse_file(u'普通账户_normalized.xls')
	d2 = normalize.parse_file(u'东兴普通账户_normalized.xls')
	alldf = pd.concat([d1,d2])
	alldf.to_excel('合并后_normalized.xls',encoding='gbk')

def process_1488061441():
	df = normalize.parse_file(u'卓建华2014交割单1.201503050951.xlsx')
	for i,row in df.iterrows():
		operation = row[u'委托类别']
		bianhao = row[u'成交编号']
		stock_name = row[u'证券名称']
		stock_code = row[u'证券代码']
		if operation == u'直接还款' and bianhao == u'申购扣款':
			df.loc[i,u'委托类别'] = u'申购扣款'
		elif stock_name == u'申购款' and operation == u'直接还款':
			stock_name = SinaQuote.getNewStockName(stock_code)
			if stock_name == '':
				print 'error, new stock name not found:%s' % stock_code

			df.loc[i,u'证券名称'] = stock_name
			df.loc[i,u'委托类别'] = u'申购扣款'

	df.to_excel(u'调整后.xls',encoding='gbk')

def remove_empty_lines():
	df = normalize.parse_file(argv[1])
	df['is_empty'] = False
	for i,row in df.iterrows():
		deal_date = row[u'成交日期']
		print deal_date
		if type(deal_date) is float and math.isnan(deal_date):
			df.loc[i,'is_empty'] = True

	df[df['is_empty']==False].to_excel('processed.xls',encoding='gbk')

def add_actual_amount():
	df = normalize.parse_file(argv[1])
	df[u'发生金额'] = 0
	for i,row in df.iterrows():
		operation = row[u'买卖方向']
		deal_amount = row[u'成交金额']
		actual_amount = deal_amount
		if operation == u'买入':
			actual_amount = -deal_amount
		df.loc[i,u'发生金额'] = actual_amount
		stock_number = row[u'成交数量']
		if stock_number==0:
			if operation == u'买入':
				df.loc[i,u'买卖方向'] = u'支出'
				df.loc[i,u'发生金额'] = -deal_amount
			else:
				df.loc[i,u'买卖方向'] = u'红利'
				df.loc[i,u'发生金额'] = deal_amount
	df.to_excel('processed.xls',encoding='gbk')

def process_5447231412():
	df = normalize.parse_file(u'all.xlsx')
	for i,row in df.iterrows():
		operation = row[u'操作']
		stock_name = row[u'证券名称']
		stock_code = row[u'证券代码']
		if stock_name == u'申购款' and operation in [u'申', u'卖']:
			stock_name = SinaQuote.getNewStockName(stock_code)
			if stock_name == '':
				print 'error, new stock name not found:%s' % stock_code
			df.loc[i,u'证券名称'] = stock_name
			if operation == u'申':
				df.loc[i,u'操作'] = u'申购扣款'
			else:
				df.loc[i,u'操作'] = u'申购还款'

	df.to_excel(u'调整后.xls',encoding='gbk')

def process_2271516673():
	df = normalize.parse_file(argv[1])
	df[u'证券名称'] = u''
	df[u'业务名称'] = u''
	error_op = {}
	for i,row in df.iterrows():
		zhaiyao = row[u'摘要']
		match_pattern = u'([\u4e00-\u9fa5]+)(:|\?|\()([\u4e00-\u9fa5\uff21 A-Z0-9]*)'
		r = re.match(match_pattern, zhaiyao)
		if r!=None:
			operation = r.group(1)
			df.loc[i, u'业务名称'] = operation
			stock_name = r.group(3)
			df.loc[i, u'证券名称'] = stock_name
		elif zhaiyao in [u'融资利息扣款']:
			df.loc[i, u'业务名称'] = u'融资利息扣款'
		else:
			print 'error row %s'%zhaiyao

	df.to_excel(u'调整后.xls',encoding='gbk')

def get_old_dirs():
	df = normalize.parse_file(argv[1])
	for i,row in df.iterrows():
		
		
if __name__ == '__main__':
	#print get_file_type(argv[1])
	#test1()
	#compare_file()
	#get_dir_names()
	#rename_column()
	#process_zhanye()
	#process_zhanye1()
	process_2271516673()


