__author__ = 'siavash'

# QSTK Imports
import QSTK.qstkutil.qsdateutil as dateUtil
import QSTK.qstkutil.DataAccess as dataAccess

# Third Party Imports
import datetime as dateTime
import pandas as pandas
import numpy as np
import copy
import QSTK.qstkstudy.EventProfiler as ep

print "Pandas Version", pandas.__version__


def loadprices(timestamps):
    dataobj = dataAccess.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002012')
    ls_symbols.append('SPY')

    print "reading data"
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']
    ldf_data = dataobj.get_data(timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)

    return d_data, ls_symbols


def findevents(d_data,ls_symbols,timestamps,bollinger_value):
    df_close = d_data['actual_close']
    print "Finding Events"
    # Creating an empty dataframe
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN
    # Time stamps for the event range
    ldt_timestamps = df_close.index
    eventcount = 0
    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
             # Calculating the returns for this timestamp
            f_symboll_today = bollinger_value[s_sym].ix[ldt_timestamps[i]]
            f_symboll_yest = bollinger_value[s_sym].ix[ldt_timestamps[i - 1]]
            f_marketbol_today = bollinger_value['SPY'].ix[ldt_timestamps[i]]
            if f_symboll_today < -2.0 and f_symboll_yest >= -2.0 and f_marketbol_today > 1.2:
                df_events[s_sym].ix[timestamps[i]] = 1
                eventcount += 1

    print "Event count", eventcount

    return df_events


def compute_bollingerbands(close, symbols):
    rollingmean = {}
    rollingstd = {}
    bollinger_value = {}
    for symbol in symbols:
        rollingmean[symbol] = pandas.rolling_mean(close[symbol], 20)
        rollingstd[symbol] = pandas.rolling_std(close[symbol], 20)
        bollinger_value[symbol] = (close[symbol] - rollingmean[symbol]) / rollingstd[symbol]
    return bollinger_value


def main():
    # Start and End date of the charts
    startdate = dateTime.datetime(2008, 1, 1)
    enddate = dateTime.datetime(2009, 12, 31)
    todaydate = dateTime.timedelta(hours=16)
    timestamps = dateUtil.getNYSEdays(startdate, enddate, todaydate)
    print("Startdate:",startdate)
    print("Enddate",enddate)
    prices, symbols = loadprices(timestamps)
    close = prices['actual_close']
    bollinger_value = compute_bollingerbands(close, symbols)
    df_events = findevents(prices,symbols,timestamps, bollinger_value)
    ep.eventprofiler(df_events, prices, i_lookback=20, i_lookforward=20,
                s_filename='MyEventStudy.pdf', b_market_neutral=True, b_errorbars=True,
                s_market_sym='SPY')

if __name__ == '__main__':
    main()

