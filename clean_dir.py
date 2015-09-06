# -*- coding: utf-8 -*-


import os
from sys import argv
import re
import glob



def remove_middle_files(clean_all=False):
	for root, subdirs, files in os.walk(u'.'):
		print root
		for f in files:
			if f.endswith( ('_normalized.xls', '_merged.xls') ) \
			or f in ['normal.xls', 'rzrq.xls', 'dongxing_normal_cash_flow.xls', 'dongxing_rzrq_cash_flow.xls', 'huatai_rzrq_cash_flow.xls'] \
			or re.match(u'全部选手结果概览.xls', f) != None \
			or (re.search(u'分析结果', f) != None and clean_all):
				if f == u'合并后_normalized.xls':
					continue
				print '****** process %s' % f
				old_dir = os.getcwd()
				os.chdir(root)
				
				if clean_all == False:
					for p in [u'*普通账户_分析结果*xls', u'*融资融券账户_分析结果*xls']:
						result_list = glob.glob(p)
						if len(result_list) > 1:
							max_date = ''
							for rf in result_list:
								match_r = re.match(u'.*分析结果([\d]+).xls', rf)
								date = match_r.group(1)
								if date>max_date:
									max_date=date
							for rf in result_list:
								if rf.find(max_date) == -1:
									cmd = u'mv %s /tmp/gaoshou1' % rf
									print cmd
									os.system(cmd.encode('utf-8'))

				cmd = u'mv %s /tmp/gaoshou1' % f
				os.system(cmd.encode('utf-8'))		


				os.chdir(old_dir)


if __name__ == '__main__':
	print len(argv)
	if len(argv)>1 and argv[1] == 'all':
		remove_middle_files(True)
	else:
		remove_middle_files()