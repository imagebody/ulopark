# -*- coding: utf-8 -*-


import os
from sys import argv
import re
import glob
from brokers import normalize


def grep_files():
	result_list = []
	for root, subdirs, files in os.walk(u'.'):
		print root
		for f in files:
			if not root.startswith('ignore_') and not f.startswith('ignore_') and \
			f.endswith( ('.xls', '.xlsx') ) and not f.endswith( ('normalized.xls', 'merged.xls') ) and \
			f not in ['normal.xls', 'rzrq.xls', 'dongxing_normal_cash_flow.xls', 'dongxing_rzrq_cash_flow.xls', 'huatai_rzrq_cash_flow.xls'] :
				print 'process %s' % root+'/'+f
				old_dir = os.getcwd()
				os.chdir(root)
				df = normalize.parse_file(f)
				if u'剩余数量' in df.columns:
					print '*** find file : %s' % f
					result_list.append(root+'/'+f)
				os.chdir(old_dir)
	for i in result_list:
		print i


if __name__ == '__main__':
	grep_files()