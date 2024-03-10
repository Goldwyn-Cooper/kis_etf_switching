from unittest import TestCase, main, skip
import os
import logging
logging.basicConfig(level=logging.WARNING)

from dotenv import load_dotenv
load_dotenv()
import pandas as pd

from src.kis import KISClient
from src.sb import SupabaseClient
from src.finance import FinanceHelper

class FinanceTests(TestCase):
    def setUp(self) -> None:
        self.finance = FinanceHelper()
    
    def test_fetch_history(self):
        gold = '411060'
        df = self.finance.fetch_history(gold)
        self.assertIsInstance(df, pd.DataFrame)
    
    def test_update_momentum(self):
        gold = '411060'
        score = self.finance.update_momentum(gold)
        self.assertIsInstance(score, float)
    
    def test_update_aatr(self):
        gold = '411060'
        aatr = self.finance.update_aatr(gold)
        self.assertIsInstance(aatr, float)
    
    def test_cal_candidate(self):
        etf = SupabaseClient().fetch_candidate()
        df = self.finance.cal_candidate(etf, 3)
        self.assertIsInstance(df, pd.DataFrame)

class KISTests(TestCase):
    def setUp(self) -> None:
        self.kis = KISClient()
        sb = SupabaseClient()
        access_token = sb.fetch_token_from_cano(self.kis.cano)
        self.kis.set_access_token(access_token)

    def test_app_key(self):
        app_key = os.getenv('KIS_APP_KEY')
        self.assertIsInstance(app_key, str)

    def test_app_secret(self):
        app_secret = os.getenv('KIS_APP_SECRET')
        self.assertIsInstance(app_secret, str)
    
    def test_cano(self):
        cano = os.getenv('KIS_CANO')
        self.assertIsInstance(cano, str)
    
    def test_get_account_balance(self):
        balance = self.kis.get_account_balance()
        self.assertIsInstance(balance, int)
    
    def test_get_stock_balance(self):
        df = self.kis.get_stock_balance()
        self.assertIsInstance(df, pd.DataFrame)
    
class SupabaseTests(TestCase):
    def setUp(self) -> None:
        self.sb = SupabaseClient()

    def test_url(self):
        url = os.getenv('SUPABASE_URL')
        self.assertIsInstance(url, str)

    def test_key(self):
        key = os.getenv('SUPABASE_KEY')
        self.assertIsInstance(key, str)

    def test_fetch_candidate(self):
        df = self.sb.fetch_candidate()
        self.assertIsInstance(df, type(pd.DataFrame()))
    
    def test_fetch_token_from_cano(self):
        token = self.sb.fetch_token_from_cano(os.getenv('KIS_CANO'))
        self.assertIsInstance(token, str)
    
class TelegramTests(TestCase):        
    def test_bot_token(self):
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.assertIsInstance(bot_token, str)

    def test_chat_id(self):
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.assertIsInstance(chat_id, str)

    @skip('Do not need to test')
    def test_send_message(self):
        from src.telegram import TelegramBot
        bot = TelegramBot()
        bot.send_message('📌 KIS_ETF_SWITCHING')

if __name__ == '__main__':
    main()