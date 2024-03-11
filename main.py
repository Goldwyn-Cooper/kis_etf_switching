def main() -> None:
    import requests
    from src.telegram import TelegramBot
    from src.kis import KISClient
    from src.sb import SupabaseClient
    from src.finance import FinanceHelper

    bot = TelegramBot()
    try:
        bot.send_message('📌 KIS_ETF_SWITCHING')
        kis = KISClient()
        sb = SupabaseClient()
        access_token = sb.fetch_token_from_cano(kis.cano)
        kis.set_access_token(access_token)
        
        # 계좌 정보
        account_balance = kis.get_account_balance()
        # print(account_balance)
        bot.send_message(f'🌱 거래 가능 금액 : ₩{account_balance:,}')
        stock_balance = kis.get_stock_balance()
        # print(stock_balance)

        # 후보 종목
        finance = FinanceHelper()
        candidate = sb.fetch_candidate()
        limit = account_balance // 10_000_000 // candidate.category.nunique()
        # print(limit)
        table = finance.cal_candidate(candidate, limit)
        print(table.loc[:, ['ko_name', 'momentum']])
        table['amount'] = table['ratio'] * account_balance
        table['quantity'] = table['amount'] / table['price']
        table = table.loc[:, ['ko_name', 'quantity']]
        print(table)
        merged = stock_balance.merge(
            table, left_index=True, right_index=True,
            how='outer', indicator=True, suffixes=('_sell', '_buy'))
        # print(merged)

        # 매도
        sell = merged.query('_merge == "left_only"')\
                .loc[:, ['ko_name_sell', 'quantity_sell']]
        msg = '👋 매도할 종목이 없습니다.' if sell.empty else '👋 매도할 종목'
        for symbol, data in sell.iterrows():
            # print(f'👋 {symbol} {data[0]}')
            # print(kis.sell_order(symbol, data[1]))
            msg += f'\n📋 {symbol} : {data[0]}'
            result = kis.sell_order(symbol, data[1])
            msg += f'\n{"✅" if not int(result.get("rt_cd")) else "❌"} {result.get("msg1")}'
        bot.send_message(msg)

        # 매수
        buy = merged.query('_merge == "right_only"')\
                .loc[:, ['ko_name_buy', 'quantity_buy']]
        msg = '🤗 매수할 종목이 없습니다.' if buy.empty else '🤗 매수할 종목'
        for symbol, data in buy.iterrows():
            # print(f'🤗 {symbol} {data[0]}')
            # print(kis.buy_order(symbol, data[1]))
            msg += f'\n📋 {symbol} : {data[0]}'
            result = kis.buy_order(symbol, data[1])
            msg += f'\n{"✅" if not int(result.get("rt_cd")) else "❌"} {result.get("msg1")}'
        bot.send_message(msg)

    except requests.exceptions.HTTPError as e:
        print(e.response.status_code)
        print(e.response.reason)
    except Exception as e:
        print(type(e))
        print(e)
        bot.send_message(f'{type(e)}\n{e}')


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import warnings
    warnings.filterwarnings('ignore')
    main()
