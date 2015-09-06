import pandas as pd
import portfolio
import myconfig




def get_stock_hist_df(stock_cd, start_day, end_day):
	# stock_cd format sh000300, day format 2011-05-01
	file = myconfig.stock_data_path + u'/' + stock_cd + u'.csv'

	df = pd.read_csv(file)
	big_than_start_day = df['date'] >= start_day
	small_than_end_day = df['date'] <= end_day
	df_filtered = df[big_than_start_day & small_than_end_day].copy().sort(['date']).reset_index()
	#print df
	return df_filtered



def generate_nv():
	# date format 2015-08-31
	start_day = '2011-05-01'
	end_day = '2014-11-01'
	benchmark_index = 'sh000300'
	index_k_df = get_stock_hist_df(benchmark_index, start_day, end_day)
	stock_nv_list = []
	stock_last_nv = {}
	portfolio_last_nv = 1
	index_last_nv = 1
	last_stock_list = []
	last_total_nv = 0
	for i, row in index_k_df.iterrows():
		#print i, row['date'], row['change']
		day = row['date']
		index_open = row['open']
		index_close = row['close']
		index_change = row['change']
		index_nv = index_last_nv * (1+index_change)
		index_last_nv = index_nv

		stock_list = portfolio.get_stock_list(day)
		stock_num = len(stock_list)		
		if stock_list != last_stock_list:
			stock_last_nv.clear()
			last_stock_list = stock_list
			last_total_nv = stock_num	
		
		portfolio_nv = 1
		portfolio_chg = 0
		total_nv = 0
		day_nv = [day, index_close, index_change, index_nv, portfolio_chg, portfolio_last_nv, portfolio_nv, total_nv, stock_num]
		
		for stock in stock_list:
			s_df = portfolio.portfolio_hist_k_map[stock]
			chg_series = s_df[s_df['date']==day]['change']
			chg = 0
			if not chg_series.empty:
				chg = chg_series.iloc[0]
			last_nv = 1
			if stock in stock_last_nv:
				last_nv = stock_last_nv[stock]
			nv = last_nv * (1 + chg)
			stock_last_nv[stock] = nv
			total_nv += nv
			day_nv.extend([stock, chg, last_nv, nv])

		portfolio_chg = (total_nv - last_total_nv)/last_total_nv
		last_total_nv = total_nv
		portfolio_nv = portfolio_last_nv * (1+portfolio_chg)
		day_nv[4] = portfolio_chg
		day_nv[5] = portfolio_last_nv
		day_nv[6] = portfolio_nv
		day_nv[7] = total_nv
		day_nv[8] = stock_num
		portfolio_last_nv = portfolio_nv

		stock_nv_list.append(day_nv)
	#print stock_nv_list
	nv_df = pd.DataFrame(data=stock_nv_list)
	nv_df.to_csv('portfolio_nv.csv')




if __name__ == '__main__':
	#print get_stock_hist_df('sh000300', '2011-05-01', '2014-11-01')
	generate_nv()