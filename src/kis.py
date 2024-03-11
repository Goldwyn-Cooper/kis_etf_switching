import os
import warnings
import logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

import requests
import pandas as pd
from src.sb import SupabaseClient

class KISClient:
    def __init__(self) -> None:
        self.cano: str = os.getenv('KIS_CANO')
        if not self.cano:
            raise ValueError('KIS_CANO is not set')
        self.appkey: str = os.getenv('KIS_APP_KEY')
        if not self.appkey:
            raise ValueError('KIS_APP_KEY is not set')
        self.appsecret: str = os.getenv('KIS_APP_SECRET')
        if not self.appsecret:
            raise ValueError('KIS_APP_SECRET is not set')
        self.domain = 'https://openapi.koreainvestment.com:9443'
    
    def set_access_token(self, access_token: str) -> None:
        self.access_token : str = access_token
    
    def get_headers(self, tr_id) -> dict:
        return {
            'Content-Type': 'application/json; charset=utf-8',
            'authorization': f'Bearer {self.access_token}',
            'appkey': self.appkey,
            'appsecret': self.appsecret,
            'tr_id': tr_id,
            'custtype': 'P',            
        }
    
    def get_account_balance(self) -> int:
        url = f'{self.domain}/uapi/domestic-stock/v1/trading/inquire-account-balance'
        headers = self.get_headers('CTRP6548R')
        params = dict(CANO=self.cano,
                      ACNT_PRDT_CD='01',
                      INQR_DVSN_1='',
                      BSPR_BF_DT_APLY_YN='')
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json().get('output1')
        df = pd.DataFrame(data, dtype='float')
        # return int(df.iloc[[0, 2, 6, 16], 1].sum())
        return int(df.iloc[[0, 6, 16], 1].sum())  # 채권 제외

    def get_stock_balance(self) -> pd.DataFrame:
        url = f'{self.domain}/uapi/domestic-stock/v1/trading/inquire-balance'
        headers = self.get_headers('TTTC8434R')
        params = dict(CANO=self.cano,
                      ACNT_PRDT_CD='01',
                      AFHR_FLPR_YN='N',
                      OFL_YN='',
                      INQR_DVSN='02',
                      UNPR_DVSN='01',
                      FUND_STTL_ICLD_YN='N',
                      FNCG_AMT_AUTO_RDPT_YN='N',
                      PRCS_DVSN='00',
                      CTX_AREA_FK100='',
                      CTX_AREA_NK100='')
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json().get('output1')
        df = pd.DataFrame(data).loc[:, ['pdno', 'prdt_name', 'hldg_qty']]
        df.columns = ['symbol', 'ko_name', 'quantity']
        df.quantity = df.quantity.astype(int)
        return df.set_index('symbol').query('quantity > 0')
    
    def trading_payload(self, symbol: str, quantity: int):
        return dict(
            CANO=self.cano,
            ACNT_PRDT_CD='01',
            PDNO=symbol,
            ORD_DVSN='01',
            ORD_QTY=f'{int(quantity)}',
            ORD_UNPR='0')

    def sell_order(self, symbol: str, quantity: int):
        url = f'{self.domain}/uapi/domestic-stock/v1/trading/order-cash'
        headers = self.get_headers('TTTC0801U') # TTTC0801U : 매도, TTTC0802U : 매수
        payload = self.trading_payload(symbol, quantity)
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def buy_order(self, symbol: str, quantity: int):
        url = f'{self.domain}/uapi/domestic-stock/v1/trading/order-cash'
        headers = self.get_headers('TTTC0802U') # TTTC0801U : 매도, TTTC0802U : 매수
        payload = self.trading_payload(symbol, quantity)
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sb = SupabaseClient()
    kis = KISClient()
    access_token = sb.fetch_token_from_cano(kis.cano)
    kis.set_access_token(access_token)
    print(kis.get_account_balance())
    print(kis.get_stock_balance())