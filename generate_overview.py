# -*- coding: utf-8 -*-


import os
from sys import argv
import re
import pandas as pd
from brokers import normalize
import numpy as np
import analyze_account


def merge_all():
	all_df = pd.DataFrame()
	for root, subdirs, files in os.walk('.'):
		print root
		for f in files:
			if f.find('分析结果') != -1:
				print '****** process %s' % f
				old_dir = os.getcwd()
				os.chdir(root)
				df = pd.read_excel(f, encoding='gbk')
				all_df = pd.concat([all_df, df])				
				os.chdir(old_dir)


	return all_df

def compute_rank():
	all_df = merge_all().reset_index()

	all_df['max_asset'] = np.nan
	all_df['max_dd'] = np.nan
	all_df[u'参赛组别'] = u''
	for i,row in all_df.iterrows():
		max_12 = row[u'2014年12月最大资产']
		avg_year = row[u'全年平均资产']
		max_asset = max_12
		if avg_year>max_asset:
			max_asset=avg_year
		all_df.loc[i, 'max_asset'] = max_asset
		s_dd = row[u'最大回撤']
		all_df.loc[i, 'max_dd'] = float(s_dd[:-1])
		all_df.loc[i, u'参赛组别'] = analyze_account.get_group_name(row[u'组别'])

	#print all_df

	sharpe_0 = all_df[u'年化夏普比率']>0
	nv_1 = all_df[u'期末净值']>1
	all_df1 = all_df[sharpe_0 & nv_1].copy()
	all_df1['points'] = np.nan
	all_df1['nv_points'] = np.nan
	all_df1['max_asset_points'] = np.nan
	all_df1['sharpe_points'] = np.nan
	all_df1['max_dd_points'] = np.nan

	out_df = pd.DataFrame()
	for group_type in [1,2,3,4,5]:
		g_df = all_df1[all_df1[u'组别']==group_type].copy()
		calculate_points(g_df)
		out_df = pd.concat([out_df, g_df])

	all_df.to_excel(u'全部选手结果概览.xls', encoding='gbk')
	out_df.to_excel(u'合格参赛选手.xls', encoding='gbk')

def calculate_points(q_df):
	q_max_asset = q_df[u'全年平均资产'].max()
	q_max_sharpe = q_df[u'年化夏普比率'].max()
	q_max_nv = q_df[u'期末净值'].max()

	q_max_dd = q_df[u'max_dd'].max()

	for i,row in q_df.iterrows():
		points=0
		points += 20 * (row['全年平均资产']/q_max_asset)
		points += 60 * (row[u'期末净值']/q_max_nv)
		points += 10 * (row[u'年化夏普比率']/q_max_sharpe)
		points += 10 * (1-row[u'max_dd']/q_max_dd)
		q_df.loc[i, 'points'] = points


def test():
	df = normalize.parse_file(argv[1])
	df['max_asset'] = max(df['a'], df['b'])
	print df

if __name__ == '__main__':
	merge_all()
	compute_rank()


	