import pandas as pd
import myconfig

N1 = myconfig.n_day_entry
N2 = myconfig.n_day_exit
starttime = pd.to_datetime('20110501')
endtime = pd.to_datetime('20110901')

stock_data = pd.read_csv(myconfig.stock_data_path+'/sz300072.csv', parse_dates=['date'])
stock_data = stock_data[['date', 'high', 'low', 'close', 'change']]
stock_data = stock_data[stock_data['date'] >= starttime]
stock_data = stock_data[stock_data['date'] <= endtime]
stock_data.sort('date', inplace=True)
stock_data.reset_index(inplace=True)


stock_data['N1High'] = pd.rolling_max(stock_data['high'], N1)
#stock_data['N1High'].fillna(value=pd.expanding_max(stock_data['high']), inplace=True)
stock_data['N1High'].fillna(value=myconfig.pesudo_max_stock_price, inplace=True)
stock_data['N2Low'] = pd.rolling_min(stock_data['low'], N2)
#stock_data['N2Low'].fillna(value=pd.expanding_min(stock_data['low']), inplace=True)
stock_data['N2Low'].fillna(value=myconfig.pesudo_min_stock_price, inplace=True)

#print stock_data

buy_index = stock_data[stock_data['close'] > stock_data['N1High'].shift(1)].index
stock_data.loc[buy_index, 'signal'] = 1

sell_index = stock_data[stock_data['close'] < stock_data['N2Low'].shift(1)].index
stock_data.loc[sell_index, 'signal'] = 0

stock_data['amount'] = stock_data['signal'].shift(1)
#stock_data['amount'].fillna(method='ffill', inplace=True)


stock_data['netvalue'] = (stock_data['change'] * stock_data['amount'] + 1.0).cumprod()
print stock_data

#print stock_data[['date','netvalue']]



