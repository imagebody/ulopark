# -*- coding: utf-8 -*-

import re
import os.path
import pandas as pd
from sys import argv
import sys
sys.path.append('/Users/jiangbin/code/python/lib')

import normalize

def merge(f1, f2):
	bf1 = f1[:f1.rfind('.')]
	bf2 = f2[:f2.rfind('.')]
	of1 = normalize.process(f1, bf1)
	of2 = normalize.process(f2, bf2)
	df1 = normalize.parse_file(of1)
	df2 = normalize.parse_file(of2)

	df_all = pd.concat([df1, df2])
	#df_all['old index'] = df_all.index
	df_all = df_all.reset_index()
	df_all.to_excel('tmp_merged.xls', encoding='gbk')

if __name__ == '__main__':
	merge(argv[1], argv[2])