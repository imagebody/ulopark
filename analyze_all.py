# -*- coding: utf-8 -*-

import os
import glob
import time
import pandas as pd
import analyze_account
from sys import argv
from brokers import normalize


file_types = {
	'dongxing_normal_cash_flow': 
	[u'成交日期',u'成交时间',u'委托类别',u'发生金额',u'剩余金额',u'摘要',u'币种'],
	'dongxing_rzrq_cash_flow':
	[u'成交日期',u'成交时间',u'买卖标志',u'发生金额',u'剩余金额',u'摘要',u'币种'],
	'dongxing_rzrq_cash_flow1':
	[u'日期',u'发生时间',u'资金帐号',u'币种',u'摘要',u'收入金额',u'付出金额',u'本次余额',u'柜员代码',u'入帐日期',u'流水号',u'业务科目',u'申请方式',u'资金来源',u'相关代码',u'相关帐户',u'业务申请号',u'操作站点',u'发生营业部',u'复核柜员'],
	'huatai_rzrq_cash_flow':
	[u'日期',u'摘要',u'借方(收入)',u'贷方(支出)',u'资金余额',u'货币单位',u'备注']

}


def analyze_all(merge_stock_operation_detail=False):
	print '================== begin analyze all files ...'
	print os.getcwd()
	df_overview = pd.DataFrame()

	for root, subdirs, files in os.walk(u'.'):
		print root
		for f in files:
			if f.endswith( (u'合并后_normalized.xls', u'普通账户_normalized.xls', u'融资融券账户_normalized.xls') ) \
			and root.find('--') == -1 :
				print '****** process %s' % f

				old_dir = os.getcwd()
				os.chdir(root)
				
				result_list = []
				if merge_stock_operation_detail == False:
					if f.find(u'融资融券账户') != -1:
						result_list = glob.glob(u'*融资融券账户_分析结果*.xls')
					else:
						result_list = glob.glob(u'*普通账户_分析结果*.xls')
				else: # for renjie
					(uid, name) = analyze_account.get_uid_name()
					prefix = u'/Users/jiangbin/百度云同步盘/work/for_renjie/' +uid+'_'+name
					if f.find(u'融资融券账户') != -1:
						result_list = glob.glob(prefix+u'*融资融券账户_分析结果*.xls')
					else:
						result_list = glob.glob(prefix+u'*普通账户_分析结果*.xls')
				

				if len(result_list)>0:
					pass
				else:
					df = analyze_account.analyze(f, merge_stock_operation_detail)
					df_overview = pd.concat([df_overview, df])

				os.chdir(old_dir)

	df_overview.to_excel(u'全部选手结果概览.xls', encoding='gbk')


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
				if o in [u'融资买入', u'融资利息扣款', u'融资利息', u'融券卖出', u'融资开仓']:
					file_type = 'rzrq'
			if file_type == '':
				file_type = 'normal'
		else:
			file_type = 'unknown!!!'

	return file_type
			
def shellquote(s):
    return "'" + s.replace("'", "'\\''") + "'"

def change_file_names():
	print '================== begin change all file names ...'
	for root, subdirs, files in os.walk(u'.'):
		for f in files:
			if f.endswith( ('xlsx', 'xls') ) and not f.startswith('ignore_') \
			and not f.endswith( ('_normalized.xls', '_merged.xls') ) \
			and root.find('--') == -1 and root.find('!!') == -1 \
			and not root.startswith('ignore_') \
			and f.find(u'分析结果') == -1 and f.find(u'全部选手结果概览') == -1 \
			and f not in [u'合并后_normalized.xls', 'normal.xls', 'rzrq.xls', 'dongxing_normal_cash_flow.xls', 'dongxing_rzrq_cash_flow.xls', 'huatai_rzrq_cash_flow.xls']:
				ff= root + '/' + f
				print 'process file: %s' % ff
				file_type = get_file_type(ff)
				if file_type != 'unknown!!!':
					new_file = root + '/' + file_type + '.xls'
					cmd = 'cp ' + shellquote(ff) + ' ' + shellquote(new_file)
					if os.path.isfile( shellquote(new_file) ):
						cmd = 'mv ' + shellquote(ff) + ' ' + shellquote(new_file)
					result = os.system(cmd)
					if result != 0:
						print cmd + ' error!!!'
				else:
					print '*** skip unknown file type:\n%s' % ff

def normalize_files():
	print '================== begin normalize all files ...'
	for root, subdirs, files in os.walk(u'.'):
		print root
		for f in files:
			if f in ['normal.xls', 'rzrq.xls', 'dongxing_normal_cash_flow.xls', 'dongxing_rzrq_cash_flow.xls', 'huatai_rzrq_cash_flow.xls'] \
			and root.find('--') == -1 and root.find('!!') == -1:
				print 'process file: %s' % f

				old_dir = os.getcwd()
				os.chdir(root)
				if root.find('ignore_') != -1:
					pass
				elif os.path.isfile('norm_done'): # skip to process this dir
					pass
				elif f == 'normal.xls' and os.path.isfile('dongxing_normal_cash_flow.xls'):
					pass
				elif f == 'rzrq.xls' and (os.path.isfile('dongxing_rzrq_cash_flow.xls') or os.path.isfile('huatai_rzrq_cash_flow.xls')):
					pass
				else:
					normalize.process(f)
				os.chdir(old_dir)


if __name__ == '__main__':
	if argv[1] == 'rename':
		change_file_names()
		exit
	if argv[1].startswith('norm'):
		normalize_files()
		exit
	if argv[1].startswith('ana'):
		if len(argv)>2 and argv[2] == 'for_renjie':
			analyze_all(True)
		else:
			analyze_all()
		exit
	
	if argv[1] == 'doall':
		change_file_names()
		time.sleep(5)
		normalize_files()
		time.sleep(5)
		if len(argv)>2 and argv[2] == 'for_renjie':
			analyze_all(True)
		else:
			analyze_all()


	#print get_file_type(argv[1])


