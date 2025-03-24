import requests

from utils.logger import Logger

logger = Logger.get_logger()

# -------------------------------- API 请求相关 --------------------------------

def funding_rate(symbol: str) -> float:
    """
    获取合约资金费率

    Args:
        symbol: 交易对名称

    Returns:
        float: 资金费率
    """
    try:
        # 获取溢价指数
        url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}'
        response = requests.get(url)
        data = response.json()
        premium_index = float(data['lastFundingRate'])

        # 计算资金费率
        base_rate = 0.0001  # 基础利率为0.01%
        rate = premium_index + max(min(base_rate - premium_index, 0.0005), -0.0005)

        return rate

    except Exception as e:
        logger.error(f"Failed to get funding rate for {symbol}: {e}")
        return 0.0


def funding_fee(
        symbol: str,
        contract_qty: float,
        price: float
) -> float:
    """
    计算合约资金费用

    Args:
        symbol: 交易对名称
        contract_qty: 合约数量
        price: 合约价格

    Returns:
        float: 资金费用
    """
    try:
        rate = funding_rate(symbol)
        nominal_value = contract_qty * price  # 名义价值
        fee = rate * nominal_value
        return fee

    except Exception as e:
        logger.error(f"Failed to calculate funding fee: {e}")
        return 0.0