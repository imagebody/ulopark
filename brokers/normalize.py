# -*- coding: utf-8 -*-

from sys import argv
import pandas as pd
import numpy as np
import re
import math
from xlrd.biffh import XLRDError
import sys
sys.path.append(u'/Users/jiangbin/百度云同步盘/work/lib')


import dongxing_normal
import dongxing_rzrq
import huatai_rzrq

import SinaQuote

match_zhaiyao = u'([^\(:, ]+).*'

operation_map = {
'init position'         : [u'初始持仓'],
'buy'                   : [u'普通买入', u'证券买入', u'证券买入清算', u'买入', u'担保品买入', u'买入担保品', u'买', u'融资买入', u'融资开仓', u'基金申购', u'信用买入', u'买入成交清算资金', u'申购资金划出', u'配股认购', u'证券理财认购确认', u'配股缴款'],
'buy (new stock)'       : [u'缴中签款', u'中签扣款', u'申购中签', u'申购中签款', u'新股中签成本划出'],
'buy (bond repurchase)' : [u'报价融券回购', u'报价1天期客户买', u'基金申购拨出', u'融券回购购回日', u'回购融券', u'专项融券回购续约', u'专项融券回购', u'报价回购拆出', u'回购拆出', u'回购融券清算', u'质押回购拆出', u'融券', u'融券回购', u'回购融券成交划出资金'],
'sell'                  : [u'普通卖出', u'证券卖出', u'证券卖出清算', u'卖出', u'担保品卖出', u'卖出担保品', u'卖', u'卖券还款', u'还款卖出', u'卖券还钱', u'基金赎回', u'信用卖出', u'卖出成交清算资金', u'赎回资金划入'],
'sell (bond repurchase)': [u'报价融券购回', u'报价1天期客到期', u'基金赎回拨入', u'专项融券终止', u'专项融券购回', u'拆出报价购回', u'拆出购回', u'融券购回清算', u'拆出质押购回', u'融券购回', u'回购融券购回资金划入'],
'short'                 : [u'融券卖出', u'融券开仓'],
'cover'                 : [u'买券还券', u'还券买入'],
'direct return'         : [u'直接还券', u'还券划转'], # 直接还券＝sell＋cover
'stock in'              : [u'股份转入', u'担保划入', u'担保品转入', u'担保物转入', u'担保品划入', u'担保转入', u'指定'],
'stock out'             : [u'股份转出', u'协议转让', u'担保划出', u'担保物转出', u'担保转出', u'撤指', u'担保品划出'],
'bank transfer'         : [u'日终资金上下账'],
'bank in money'         : [u'入金', u'银行转入', u'银行转存', u'银证转入', u'资金划入', u'银行转证券', u'银证转帐存'],
'bank out money'        : [u'出金', u'银行转出', u'银行转取', u'银证转出', u'资金划出', u'证券转银行', u'银证转帐取'],
'borrow cash'           : [u'小贷通初始交易', u'融资资金划入', u'股票回购', u'东兴股票质押融资', u'融资借入', u'融资借款'],
'return cash'           : [u'小贷通购回交易', u'卖券偿还融资负债', u'融资负债直接还款', u'融资负债卖券还款', u'偿还本金', u'卖券偿还本金', u'卖出偿还本金', u'直接还款', u'融资直接还钱划出', u'普卖开仓券还款', u'卖券实际还款', u'股票购回', u'东兴股票质押解除', u'偿还融资负债本金', u'直接偿还融资负债'],
'pay interest'          : [u'资金交收通知扣', u'买券偿还融券利息', u'卖券偿还融资费用', u'支出', u'融资利息支付', u'费用负债归还', u'费用利息支付', u'偿还融券费用', u'卖出偿还利息', u'偿还融资其它费用', u'卖券偿还融券费用', u'卖券偿还融资利息', u'融资利息', u'融资利息扣款', u'偿还融资利息', u'直接偿还融资费用', u'直接偿还融资利息'],
'pay tax'               : [u'股息红利差异', u'股息个税征收', u'销户利息税支出', u'股息税', u'股息红利扣税', u'红利差异税扣税', u'深圳市场股息红利个人所得税扣款', u'上海市场股息红利个人所得税扣款', u'股息红利税补缴', u'股息红利差异扣税', u'股息差别税'],
'earn interest'         : [u'利息结算', u'基金红利拨入', u'销户利息入本金', u'季度利息入本金', u'红利', u'红利发放', u'股息入帐', u'股息入账', u'批量利息归本', u'货币ETF未兑付收益', u'利息归本', u'红利入账', u'结息入账'],
'earn stock'            : [u'基金红股', u'送股', u'红股入帐', u'红股入账'],
'earn stock interest'   : [u'红股派息'],
'fenji fund split'      : [u'分级基金分拆'],
'todo: tuoguan'         : [u'托管转入', u'托管转出'],
'todo: no price data'   : [u'sina无价格数据'],
'pass: new stock'       : [u'申', u'上市流通', u'新股入帐', u'新股相关', u'定价申购', u'申购扣款', u'新股申购', u'申购还款', u'申购返款', u'申购配号', u'配号', u'缴申购款', u'还申购款', u'新股申购成本划出', u'新股申购成本归还'],
'pass: other'           : [u'登记指定', u'证券转入', u'证券调出', u'权证入帐', u'负债直接还钱预', u'融资直接还钱划', u'指', u'转账取预冻结', u'转账冻结取消', u'资产账户币种开户', u'带资金补登', u'约定购回购回', u'投票确认', u'配股权证到帐', u'前台收费', u'多还退券', u'撤销交易账户', u'资金扎差冻结取消', u'余券划转', u'负债直接还钱预划出', u'转存管转出', u'转存管转入', u'登记指定相关', u'基金其他'],
'pass: fenji fund'      : [u'申购赎回过入', u'申购赎回过出', u'基金分拆-母鸡', u'分级基金－母基操作'],
'pass: dongxing'        : [u'清算冻结', u'部分解除', u'ETF申购现金替代差额', u'新股上市流通', u'新股上市转出']
}

def process_deal_date(ds):
	s = ds[u'deal_date']
	#print s
	ss = str(s)
	if len(ss) == 14:
		date = ss[:8]
		time = ss[-6:]
		ds[u'deal_date'] = date
		ds[u'deal_time'] = time
	elif ss.find('-') != -1:
		r = ss.split('-')
		date = r[0]+'0'*(2-len(r[1]))+r[1]+'0'*(2-len(r[2]))+r[2]
		ds[u'deal_date'] = date
	elif ss.find('/') != -1:
		r = ss.split('/')
		date = r[0]+'0'*(2-len(r[1]))+r[1]+'0'*(2-len(r[2]))+r[2]
		ds[u'deal_date'] = date
	return ds

def handle_date_time(df):
	if 'deal_time' not in df.columns:
		df['deal_time'] = ''
	
	return df.apply(process_deal_date, axis=1)

def norm_operation(op):
	if op.startswith('="'):
		op = op[2:]
	norm_op = ''
	for key, array in operation_map.items():
		if op in array:
			norm_op = key
	
	if norm_op == '':
		print '!!!unknown op %s' % op
	return norm_op

def parse_file(file):
	df = None
	try:
		df = pd.read_excel(file, encoding='gbk')
	except XLRDError:
		df = pd.read_table(file, sep='\t', encoding='gbk')
		for c in df.columns:
			c1 = re.sub(u'[="]', '', c)
			df.rename(columns = {c:c1}, inplace=True)
		for i, row in df.iterrows():
			for c in row.index:
				cell = df.loc[i,c]
				#print cell,type(cell)
				if type(cell) is unicode:
					df.loc[i, c] = re.sub(u'[="]', '', cell)

	return df
			

def remove_space_in_column_names(df):
	df.rename(columns=lambda x: x.strip(), inplace=True)

def remove_space(col):
	if col.dtype == object:
		col = col.str.strip()
	return col


def change_column_names(df):
	remove_space_in_column_names(df)
	for c in df.columns:
		if c in [u'成交日期', u'发生日期', u'委托日期', u'交割日期', u'日期', u'交收日期']:
			df.rename(columns = {c: 'deal_date'}, inplace=True)
		elif c in [u'成交时间', u'发生时间']:
			df.rename(columns = {c: 'deal_time'}, inplace=True)
		elif c in [u'业务名称', u'委托类别', u'买卖标志', u'操作', u'买卖方向', u'交易类别', u'业务标志']:
			df.rename(columns = {c: 'operation'}, inplace=True)
		elif c in [u'摘要']:
			df.rename(columns = {c: 'zhaiyao'}, inplace=True)
		elif c in [u'成交均价', u'成交价格', u'价格']:
			df.rename(columns = {c: 'stock_price'}, inplace=True)
		elif c in [u'手续费', u'净佣金', u'佣金', u'实收佣金', u'交易费用']:
			df.rename(columns = {c: 'commision'}, inplace=True)
		elif c in [u'证券名称', u'股票名称']:
			df.rename(columns = {c: 'stock_name'}, inplace=True)
		elif c in [u'证券代码', u'股票代码', u'代码']:
			df.rename(columns = {c: 'stock_code'}, inplace=True)		
		elif c in [u'成交数量', u'数量', u'发生数量', u'发生数', u'成交股数']:
			df.rename(columns = {c: 'stock_number'}, inplace=True)		
		elif c in [u'成交金额']:
			df.rename(columns = {c: 'deal_amount'}, inplace=True)		
		elif c in [u'发生金额', u'应收金额', u'清算金额', u'收付金额', u'变动金额']:
			df.rename(columns = {c: 'actual_amount'}, inplace=True)		
		elif c in [u'资金余额', u'剩余金额', u'资金本次余额', u'本次金额', u'本次资金余额', u'可用金额']:
			df.rename(columns = {c: 'remain_amount'}, inplace=True)		
		elif c in [u'股份余额', u'剩余数量', u'股票余额', u'库存数', u'可用余额']:
			df.rename(columns = {c: 'remain_stock'}, inplace=True)		
		elif c in [u'备注']:
			df.rename(columns = {c: 'beizhu'}, inplace=True)		
		else:
			pass

def pre_process(df):
	change_column_names(df)
	merge_zhaiyao_and_operation(df)
	#df = df.apply(remove_space, axis=0)  # only for 2089526857张洁,

	for i, row in df.iterrows():
		if row[u'operation'] in [u'基金申购拨出', u'基金赎回拨入'] and \
		type(row[u'stock_code']) is unicode and row[u'stock_code'].startswith(u'AA0007'):
			df.loc[i, u'stock_number'] = abs(row[u'actual_amount'])

		if row[u'operation'] in [u'基金申购', u'基金赎回']:
			if type(row[u'stock_code']) is float and \
			math.isnan(row[u'stock_code']): # no stock code
				df.loc[i, u'operation'] = u'基金其他'
		
		if row[u'operation'] == u'基金分拆':
			if row[u'stock_name'].endswith((u'A', u'B')):
				df.loc[i, u'operation'] = u'分级基金分拆'
			else:
				df.loc[i, u'operation'] = u'基金分拆-母鸡'

		if row[u'operation'] in [u'托管转入', u'托管转出']:
			#print row[u'stock_code']
			if row[u'stock_code'] in [u'163113', u'165521']:
				df.loc[i, u'operation'] = u'分级基金－母基操作'
			#print row[u'operation'], row[u'stock_name'], type(row[u'stock_name'])
			stock_name = SinaQuote.getNewStockName(unicode(row[u'stock_name']))
			if stock_name != '':
				df.loc[i, u'operation'] = u'新股相关'

		if row[u'stock_code'] == u'799999':
			df.loc[i, u'operation'] = u'登记指定相关'

		if type(row[u'operation']) in [float, int] or type(row[u'stock_name']) in [int]:
			print row[u'operation'],row
		if row[u'operation'].startswith(u'托管转入') and type(row[u'stock_name']) is unicode and row[u'stock_name'].endswith((u'A', u'B')):
			df.loc[i, u'operation'] = u'分级基金分拆'
		
		if row[u'operation'] == u'托管转入' and type(row[u'stock_name']) is unicode and row[u'stock_name'].startswith(u'DR'):
			df.loc[i, u'operation'] = u'红股入帐'

		if u'成交编号' in row.index:
			if row[u'operation'] == u'其他' and row[u'成交编号'] == u'股息差别税':
				df.loc[i, u'operation'] = u'股息差别税'
			if row[u'operation'] == u'转托' and row[u'成交编号'] == u'转托管转入':
				df.loc[i, u'operation'] = u'指定'
			if row[u'operation'] == u'托管转入' and row[u'成交编号'] == u'上市流通':
				df.loc[i, u'operation'] = u'新股相关'
			if row[u'operation'] == u'托管转出' and row[u'成交编号'] == u'上市转出':
				df.loc[i, u'operation'] = u'新股相关'

		if 'beizhu' in row.index:
			if row[u'operation'] == u'托管转出' and row['beizhu'] == u'托管转出' \
			and (str(int(row[u'stock_code'])) not in [u'163113', u'165521']):
				print row[u'stock_code'], row[u'operation'], row[u'beizhu']
				df.loc[i, u'operation'] = u'担保转出'

		if row['operation'] == u'撤指' and row['stock_number'] == 0:
			df.loc[i, u'operation'] = u'转存管转出'		

		# handle special case 
		if row[u'stock_code'] == 82046:
			df.loc[i, u'stock_code'] = 2046	

	out_file = '普通账户.xls'
	for o in df['operation']:
		if o in [u'融资利息扣款', u'融资买入', u'融资利息']:
			out_file = '融资融券账户.xls'

	return ( df.apply(process_operation, axis=1), out_file )


def merge_zhaiyao_and_operation(df):
	has_zhaiyao = 'zhaiyao' in df.columns
	has_operation = 'operation' in df.columns
	if has_zhaiyao and not has_operation:
		df.rename(columns = {'zhaiyao':'operation'}, inplace=True)
	elif has_zhaiyao and has_operation:
		df.rename(columns = {'operation':'operation1'}, inplace=True)
		df.rename(columns = {'zhaiyao':'operation'}, inplace=True)
	else:
		pass

def process_operation(ds):
	s = ds[u'operation']
	result = re.match(match_zhaiyao, s)
	if result != None:
		norm_op = norm_operation( result.group(1) )
		ds[u'operation'] = norm_op
	return ds


def process(file, given_out_file=''):
	out_file = file
	print out_file
	if file.startswith('dongxing_normal_'):
		out_file = dongxing_normal.merge_cash_stock_flow()
		if out_file == '':
			return ''

	if file.startswith('dongxing_rzrq_'):
		out_file = dongxing_rzrq.merge_rzrq_cash_and_stock_flow()
		if out_file == '':
			return ''

	if file.startswith('huatai_rzrq_'):
		out_file = huatai_rzrq.merge_rzrq_cash_and_stock_flow()
		if out_file == '':
			return ''

	df = parse_file(out_file)

	(df, out_file1) = pre_process(df)
	df = handle_date_time(df)
	if file.startswith( ('dongxing_', 'huatai_') ) == False:
		out_file = out_file1

	out_file = re.sub('_merged', '', out_file)
	out_file = re.sub('\.', '_normalized.', out_file)
	if given_out_file != '':
		out_file = given_out_file + '/' + out_file
	print out_file
	df.to_excel(out_file, encoding='gbk')
	return out_file


	

if __name__ == '__main__':
	process(argv[1], '.')