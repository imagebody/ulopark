# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys
import myconfig

con = None

try:
    con = lite.connect(myconfig.sqlite3_db_file)
    cur = con.cursor()    
    #cur.execute('SELECT SQLITE_VERSION()')
    #data = cur.fetchone()
    #print "SQLite version: %s" % data                
except lite.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)
#finally:
#    if con:
#        con.close()


def insert(key, price):
	cur.execute('insert into stock_price values (\'%s\', %f)' % (key, price))
	con.commit()

def get(key):
	cur.execute('select price from stock_price where key = \'%s\'' % key)
	return cur.fetchone()

def get_new_stock_code(shengou_code):
	sql = 'select code from new_stock_info where shengou_code = \'%s\'' % shengou_code
	#print sql
	cur.execute(sql)
	return cur.fetchone()

def get_new_stock_name(stock_code):
	sql = 'select name from new_stock_info where code = \'%s\'' % stock_code
	#print sql
	cur.execute(sql)
	return cur.fetchone()

def get_new_stock_price(stock_code, stock_date):
	sql = 'select first_trading_day, issue_price from new_stock_info where code = \'%s\'' % stock_code
	#print sql
	cur.execute(sql)
	row = cur.fetchone()
	if row != None:
		first_trading_day = row[0]
		issue_price = row[1]
		if int(first_trading_day) > int(stock_date):
			return issue_price
	return -1

def get_xianjin_fund_price(stock_code, stock_date):
	#print stock_code, type(stock_code), stock_date
	if stock_code in [u'BE0100', u'S51293', u'519915', u'500015']:
		return 1
	#elif stock_code == u'GC001R001':
	#	return 1000
	elif stock_code in [u'519888', u'519808']:
		return 0.01
	#elif stock_code in ['131810', '131811', '131800', '131809', '131801', '131802', '131803', '131805', '131806']:
	#	return 100
	#elif stock_code in ['204001','204002','204003','204004','204007','204014','204028','204091','204182']:
	#	return 1000
	else:
		return -1

def get_missing_stock_price(stock_code, stock_date):
	sql = 'select close from missing_stock_data where code=\'%s\' and date=\'%s\'' % (stock_code, stock_date)
	cur.execute(sql)
	row = cur.fetchone()
	if row != None:
		return row[0]
	return -1	










if __name__ == '__main__':
	insert('600000', 1.11)
	insert('600001', 2.22)
	insert(600002, 2.22)
	print get('600000')[0]
	print get('600001')[0]
	print get(600002)[0]
	print get('600')
	print get_missing_stock_price(150168, 20141231)
	print get_missing_stock_price('150168', '20141230')
	print get_missing_stock_price('127001', '20140101')