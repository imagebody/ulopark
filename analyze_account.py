# -*- coding: utf-8 -*-

import pandas as pd
import os
import re
from sys import argv
import json
import math
from datetime import datetime
from pandas.tseries.offsets import BDay
import SinaQuote
import myconfig

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append(myconfig.main_path)

from account import Account
from brokers import normal     
import compute


def get_uid_name():
	full_path = os.getcwd()
	dir_name = full_path[(full_path.rindex('/')+1):]
	m = re.match(u'([\d]+)_?([^-_1]+).*', dir_name)
	uid = m.group(1)
	name = m.group(2).decode('utf-8')
	return (uid, name)

# 1 普通千万
# 2 信用千万
# 3 普通百万
# 4 信用百万
def get_group_name(g):
	sg = u''
	if g==1:
		sg = u'普通千万'
	elif g==2:
		sg = u'信用千万'
	elif g==3:
		sg = u'普通百万'
	elif g==4:
		sg = u'信用百万'
	elif g==5:
		sg = u'潜力组'
	else:
		print 'error group number %f' % g

	return sg

def get_account_group(account_value_max_201412, account_value_average, account_type):
	max_value = account_value_max_201412
	if account_value_average > max_value:
		max_value = account_value_average
	if account_type.find(u'普通') != -1:
		if max_value > 10000000:
			return 1
		elif max_value > 1000000:
			return 3
		elif max_value > 500000:
			return 5
	elif account_type.find(u'融资融券') != -1:
		if max_value > 10000000:
			return 2
		elif max_value > 1000000:
			return 4
		elif max_value > 500000:
			return 5

def print_result_overview(account_type, pdf, buy_sell_count, writer):
	print account_type
	account_value_20141231 = pdf[-1:][u'总资产'].iloc[0]
	account_value_average = pdf[u'总资产'].mean()
	#account_value_average_201412 = pdf[-23:][u'总资产'].mean()
	account_value_max_201412 = pdf[-23:][u'总资产'].max()
	total_profit = pdf[-1:][u'累计赢利'].iloc[0]
	nv_20141231 = pdf[-1:][u'净值'].iloc[0]
	sharpe = compute.nv_sharpe(pdf)
	max_drawdown = compute.max_dd(pdf[u'净值'])
	max_dd_str = '{:.2f}'.format(abs(max_drawdown)*100)+'%'
	(uid, name) = get_uid_name()
	account_group = get_account_group(account_value_max_201412, account_value_average, account_type)
	d = pd.DataFrame(data=[(uid, name, account_type.decode('utf-8'), account_value_20141231, account_value_max_201412, account_value_average, total_profit, nv_20141231, sharpe, max_dd_str, account_group, 0, buy_sell_count)],
					 columns=[u'微博id', u'姓名', u'账户类型', u'期末总资产', u'2014年12月最大资产', u'全年平均资产', u'累计赢利', u'期末净值', u'年化夏普比率', u'最大回撤', u'组别', u'总得分', u'买卖次数'])
	
	#d[u'名次']
	d.to_excel(writer, sheet_name=u'收益分析概览', encoding='gbk')
	return d

def format_nv_history(nv_df):
	for i, row in nv_df.iterrows():
		nv_df.loc[i, u'总资产'] = '{:,.2f}'.format(row[u'总资产'])
		nv_df.loc[i, u'股票市值'] = '{:,.2f}'.format(row[u'股票市值'])
		nv_df.loc[i, u'融券市值'] = '{:,.2f}'.format(row[u'融券市值'])
		nv_df.loc[i, u'现金'] = '{:,.2f}'.format(row[u'现金'])
		nv_df.loc[i, u'净值'] = '{:,.4f}'.format(row[u'净值'])
		nv_df.loc[i, u'份额'] = '{:,.2f}'.format(row[u'份额'])
		nv_df.loc[i, u'累计赢利'] = '{:,.2f}'.format(row[u'累计赢利'])
		nv_df.loc[i, u'累计利息'] = '{:,.2f}'.format(row[u'累计利息'])


def analyze(file_name, merge_stock_operation_detail=False):
	account_type = re.sub('_normalized\.xls', '', file_name)
	flow_records = pd.read_excel(file_name, encoding='gbk')

	SinaQuote.reset()
	broker_processor = globals()['normal']	
	init_account = Account(None)
	for i, row in flow_records.iterrows():
		broker_processor.handle_row(row, init_account, i==0)

	init_account.calculate_init_cash_if_no_remain_amount(flow_records)
	init_account.print_position()
	init_account.print_init_position()
	init_account_value = init_account.calculate_init_position_value(20140101)
	init_date = int(init_account.get_init_date())
	print init_date
	print init_account_value
	print init_account.init_cash

	account = Account( init_account )
	account_status_data = []
	#print "%d: %s" % (1, account.report_init())
	process_day = datetime(2014,1,1)
	init_day = datetime(init_date/10000, init_date%10000/100, init_date%100)

	while process_day < init_day:
		account.set_date(int(process_day.strftime('%Y%m%d')))
		account.calculate_nv()
		print account.get_status_data()
		account_status_data.append(account.get_status_data())
		process_day = compute.next_bday(process_day)

	for i, row in flow_records.iterrows():
		d = broker_processor.get_row_date(row)
		row_date = datetime(d/10000, d%10000/100, d%100)
		while row_date > process_day:
			account.calculate_nv(int(process_day.strftime('%Y%m%d')))
			print account.get_status_data()
			#if process_day == datetime(2014,2,24) or process_day == datetime(2014,2,25):
			#	account.print_position()
			#if int(process_day.strftime('%Y%m%d')) == 20140509 or int(process_day.strftime('%Y%m%d')) == 20140512:
			#account.report_position_detail()
			account_status_data.append(account.get_status_data())
			process_day = compute.next_bday(process_day)
			account.set_date(int(process_day.strftime('%Y%m%d')))
		broker_processor.handle_row(row, account, i==0)
		account.calculate_nv() # 每个操作必须重新计算净值
		#print account.get_status_data(), d, row['operation'], row['actual_amount'], row['stock_code'], row['stock_name']
	while process_day <= datetime(2014,12,31):
			account.calculate_nv(int(process_day.strftime('%Y%m%d')))
			print account.get_status_data()
			account_status_data.append(account.get_status_data())
			process_day = compute.next_bday(process_day)
			account.set_date(int(process_day.strftime('%Y%m%d')))
		
	df_nv_history = pd.DataFrame(data=account_status_data, columns=account.get_status_columns())
	(uid, name) = get_uid_name()
	out_file_name = uid + '_' + name + '_' + account_type + u'_分析结果' + datetime.now().strftime('%Y%m%d%H%M%S') + '.xls'
	if merge_stock_operation_detail:
		out_file_name = u'/Users/jiangbin/百度云同步盘/work/for_renjie/'+out_file_name
	(profit_sum_list, profit_detail_df_list) = account.get_profit_detail(20141231)
	#df_profit_detail = pd.DataFrame(data=profit_list, columns=profit_columns)
	df_profit_sum = pd.DataFrame(data=profit_sum_list, columns=[u'代码', u'名称', u'累计赢利'])
	df_init_position = init_account.get_init_position_dataframe()
	df_final_position = account.get_position_dataframe(20141231)
	#account.stock_position.get_detail_stock_flow(20141231)
	buy_sell_count = account.buy_sell_count

	df_overview = pd.DataFrame()
	with pd.ExcelWriter(out_file_name) as writer:
		df_overview = print_result_overview(account_type, df_nv_history, buy_sell_count, writer)
		df_nv_history.to_excel(writer, sheet_name=u'净值历史', encoding='gbk')
		df_profit_sum = add_stock_code_prefix(df_profit_sum, u'代码')
		df_profit_sum.to_excel(writer, sheet_name=u'个股赢利汇总', encoding='gbk')
		write_profit_detail(writer, profit_detail_df_list, merge_stock_operation_detail)
		df_init_position[u'类型'] = u'期初持仓'
		df_final_position[u'类型'] = u'期末持仓'
		df_position_all = pd.concat([df_init_position, df_final_position])
		df_position_all = add_stock_code_prefix(df_position_all, u'代码')
		change_init_date(df_position_all)
		df_position_all.to_excel(writer, sheet_name=u'期初期末持仓', encoding='gbk')

		
	return df_overview
		
def write_profit_detail(writer, df_list, merge_stock_operation_detail):
	if merge_stock_operation_detail:
		df_all = pd.DataFrame()
		for df in df_list:
			df_all = pd.concat([df_all, df])
		df_all = add_stock_code_prefix(df_all, u'代码')
		change_init_date(df_all)
		df_all.to_excel(writer, sheet_name=u'个股赢利明细', encoding='gbk')

	else:
		startrow=0
		for spdf in df_list:
			spdf = add_stock_code_prefix(spdf, u'代码')
			change_init_date(spdf)
			spdf.to_excel(writer, sheet_name=u'个股赢利明细', startrow=startrow, encoding='gbk')
			(row_count, col_count) = spdf.shape
			startrow += row_count+2
		


def merge_df_list(df_list):
	df_all = pd.DataFrame()
	for df in df_list:
		df_all = pd.concat([df_all, df])
	return df_all

def add_stock_code_prefix(df, cname):
	df = df.reset_index()
	for i,row in df.iterrows():
		stock_name = SinaQuote.get_sh_sz(row[cname])
		if stock_name != u'':
			df.loc[i, cname] = stock_name
	del df['index']
	return df

def change_init_date(df):
	for i,row in df.iterrows():
		date = row[u'日期']
		if date == 20140101:
			df.loc[i, u'日期'] = 20140102



def test1():
	df = pd.read_excel(argv[1], encoding='gbk')
	print df
	format_nv_history(df)
	print df

def test2():
	print get_uid_name()


if __name__ == '__main__':
	#analyze(argv[1], argv[2])
	#merge_and_analyze()
	analyze(argv[1], True)
	#test1()
	#test2()
