import os
import warnings
import logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.WARNING)

import pandas as pd
from supabase import create_client, Client

class SupabaseClient:
    def __init__(self):
        if not os.getenv('SUPABASE_URL'):
            raise ValueError('SUPABASE_URL is not set')
        if not os.getenv('SUPABASE_KEY'):
            raise ValueError('SUPABASE_KEY is not set')
        self.client : Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY'),
        )
    
    def fetch_candidate(self) -> pd.DataFrame:
        query = self.client.table('KIS_ETF')\
                .select('*')
        result = query.execute()
        return pd.DataFrame(result.data).set_index('symbol')
    
    def fetch_token_from_cano(self, cano: str) -> dict:
        query = self.client.table('KIS_TOKEN')\
                .select('access_token')\
                .eq('cano', cano)
        result = query.execute()
        return result.data[0].get('access_token')

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    supabase = SupabaseClient()
    print(supabase.fetch_candidate())
    print(supabase.fetch_token_from_cano(os.getenv('KIS_CANO')))