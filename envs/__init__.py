from gymnasium.envs.registration import register

register(
    id='TradingEnv',
    entry_point='envs.trading_env:TradingEnv',
    disable_env_checker=True
)
register(
    id='TradingEnvBinance',
    entry_point='envs.trading_env_binance:TradingEnvBinance',
    disable_env_checker=True
)

