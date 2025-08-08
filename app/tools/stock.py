"""Stock price utilities for Streamlit using yfinance."""

import yfinance as yf
from utils.common import logger


def get_stock_price(symbol: str, period: str = "1d"):
    """Fetch recent stock data and return key metrics.

    Returns dict: {"success": bool, "data": dict|None, "error": str|None}
    """
    try:
        logger.info(f"📈 Fetching stock price for symbol: {symbol}, period: {period}")
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        if hist.empty:
            logger.warning(f"⚠️ No data found for symbol: {symbol}")
            return {"success": False, "error": "No data found for the given symbol."}

        latest = hist.iloc[-1]
        data = {
            "current_price": round(float(latest.get("Close", 0.0)), 2),
            "change": round(float(latest.get("Close", 0.0) - latest.get("Open", 0.0)), 2),
            "volume": int(latest.get("Volume", 0)),
            "info": f"Open: {latest.get('Open', 'N/A')}, High: {latest.get('High', 'N/A')}, Low: {latest.get('Low', 'N/A')}",
        }
        logger.info(f"💸 Stock data retrieved successfully for symbol: {symbol}")
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"❌ Error querying stock price for symbol: {symbol} - {str(e)}")
        return {"success": False, "error": str(e)}
