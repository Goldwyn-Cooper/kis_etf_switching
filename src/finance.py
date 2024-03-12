import warnings
import logging
import ast
from datetime import datetime
from dateutil.relativedelta import relativedelta
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

import requests
import pandas as pd

class FinanceHelper:
    def __init__(self) -> None:
        self.fibo = self.get_fibo(13)

    @staticmethod    
    def get_fibo(n: int) -> list:
        fibo = [0] * max(n+1, 3)
        fibo[1] = 1
        fibo[2] = 1
        for i in range(3, n+1):
            fibo[i] = fibo[i-1] + fibo[i-2]
        return fibo[3:]

    cache = {}

    @classmethod
    def fetch_history(cls, symbol: str) -> pd.DataFrame:
        if symbol in cls.cache:
            return cls.cache[symbol]
        url = 'https://m.stock.naver.com/front-api/v1/external/chart/domestic/info'
        start_time = (datetime.utcnow() - relativedelta(years=1)).strftime('%Y%m%d')
        params = dict(symbol=symbol, requestType=1, timeframe='day',
                    startTime=start_time, endTime='20991231')
        response = requests.get(url, params)
        response.raise_for_status()
        text = response.text.replace('\n', '').replace('\t', '')
        data = ast.literal_eval(text.strip())
        df = pd.DataFrame(data[1:])
        df[0] = pd.to_datetime(df[0])
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Foreigner']
        result = df.set_index('Date').iloc[:, :4]
        cls.cache[symbol] = result 
        return result

    def update_momentum(self, symbol: str):
        price = self.fetch_history(symbol).Close
        momentum = []
        cal_momentum = lambda f:\
            lambda x: (x.iloc[-1] / x.iloc[0] - 1) / f
        for f in self.fibo:
            m = price.rolling(f)\
                .apply(cal_momentum(f))\
                .iloc[-1]
            if not pd.isna(m):
                momentum.append(m)
        score = sum(momentum) / len(momentum) * 252
        return score

    def update_aatr(self, symbol):
        history = self.fetch_history(symbol)
        th = history.High - history.Close.shift(1)
        tl = history.Low - history.Close.shift(1)
        tr = th - tl
        atr = tr.ewm(self.fibo[-1]).mean().iloc[-1]
        aatr = atr / history.Close.iloc[-1]
        return aatr

    def cal_candidate(self, etf: pd.DataFrame, limit: int):
        etf['momentum'] = etf.index.map(self.update_momentum)
        etf['aatr'] = etf.index.map(self.update_aatr)
        etf['ratio'] = (etf.aatr.median() / etf.aatr)\
            .apply(lambda x: min(1, x)) / (etf.category.nunique() * limit)
        # etf.drop(columns=['aatr'], inplace=True)
        etf.sort_values('momentum', ascending=False, inplace=True)        
        print(etf.loc[:, ['ko_name', 'momentum', 'aatr']])
        etf.query('momentum > 0', inplace=True)
        result = etf.groupby('category').head(limit)\
            .sort_values(['category', 'momentum'],
                        ascending=[True, False])\
            .round(3)
        result['price'] = result.index.map(self.fetch_history)\
                            .map(lambda x: x.Close.iloc[-1])
        return result

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    finance = FinanceHelper()

    gold = '411060'
    print(finance.fetch_history(gold).head())
    print(finance.fetch_history(gold).tail())
    print(finance.update_momentum(gold))
    print(finance.update_aatr(gold))

    from sb import SupabaseClient
    sb = SupabaseClient()
    etf = sb.fetch_candidate()
    print(finance.cal_candidate(etf, 3))