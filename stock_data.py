#!/usr/bin/env python3
"""
股票数据获取脚本
支持A股和港股的历史数据获取

网络配置说明:
- 默认尝试直接连接（无代理）
- 如需使用代理，请设置环境变量或修改下面的配置
- 常见代理端口: 7897 (Clash), 7890, 1080, 8080

使用示例:
    # 无代理运行
    python stock_data.py 600415
    
    # 使用代理运行
    HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897 python stock_data.py 600415
"""

import sys
import json
import os
import ssl
import urllib.request
import re
from datetime import datetime, timedelta

# ============== 网络配置 ==============
# 如果遇到网络问题，请修改以下配置:
PROXY_ENABLED = False  # 设置为 True 启用代理
PROXY_HTTP = "http://127.0.0.1:7897"
PROXY_HTTPS = "http://127.0.0.1:7897"

# 或者使用环境变量中的代理
USE_ENV_PROXY = True

# 是否忽略SSL证书验证（用于开发/测试）
IGNORE_SSL_VERIFY = True


def get_proxy_dict():
    """获取代理配置"""
    if USE_ENV_PROXY:
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        if http_proxy or https_proxy:
            return {'http': http_proxy, 'https': https_proxy}
    
    if PROXY_ENABLED:
        return {'http': PROXY_HTTP, 'https': PROXY_HTTPS}
    
    return None


def create_ssl_context():
    """创建SSL上下文"""
    if IGNORE_SSL_VERIFY:
        # 创建不验证SSL的上下文（仅用于开发测试）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    else:
        # 使用系统默认SSL上下文
        try:
            import certifi
            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()


def get_opener():
    """创建配置好的urllib opener"""
    proxy = get_proxy_dict()
    
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler(proxy))
    else:
        # 无代理
        handlers.append(urllib.request.ProxyHandler({}))
    
    ssl_ctx = create_ssl_context()
    handlers.append(urllib.request.HTTPSHandler(context=ssl_ctx))
    
    return urllib.request.build_opener(*handlers)


def get_stock_data(stock_code, days=60):
    """
    获取股票历史数据
    
    Args:
        stock_code: 股票代码 (A股6位，港股5位)
        days: 获取天数
    
    Returns:
        dict: 包含日期、开盘、最高、最低、收盘、成交量
    """
    
    # 判断市场
    if len(stock_code) == 6:
        market = "A股"
    elif len(stock_code) == 5:
        market = "港股"
    else:
        return {"error": "不支持的股票代码格式", "tips": "A股6位，港股5位"}
    
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days * 2)
    
    # 方法1: 使用东方财富API
    try:
        data = get_data_eastmoney(stock_code, start_date, end_date)
        if data and "error" not in data:
            return data
    except Exception as e:
        print(f"东方财富API失败: {e}", file=sys.stderr)
    
    # 方法2: 使用新浪API
    try:
        data = get_data_sina(stock_code)
        if data and "error" not in data:
            return data
    except Exception as e:
        print(f"新浪API失败: {e}", file=sys.stderr)
    
    # 方法3: 尝试无代理直接连接
    try:
        global USE_ENV_PROXY, PROXY_ENABLED
        old_env = USE_ENV_PROXY
        old_proxy = PROXY_ENABLED
        USE_ENV_PROXY = False
        PROXY_ENABLED = False
        
        data = get_data_eastmoney(stock_code, start_date, end_date)
        
        USE_ENV_PROXY = old_env
        PROXY_ENABLED = old_proxy
        
        if data and "error" not in data:
            return data
    except Exception as e:
        print(f"无代理连接失败: {e}", file=sys.stderr)
    
    return {
        "error": "数据获取失败，请检查网络设置",
        "tips": "可尝试: HTTP_PROXY=http://127.0.0.1:7897 python stock_data.py 600415",
        "mock_data_example": True
    }


def get_data_eastmoney(stock_code, start_date, end_date):
    """使用东方财富API获取数据"""
    
    # A股: 1.xxxxxx, 港股: 116.xxxxx
    if len(stock_code) == 6:
        secid = f"1.{stock_code}"
    else:
        secid = f"116.{stock_code}"
    
    url = (
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        f"fields1=f1,f2,f3,f4,f5,f6&"
        f"fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116,f117,f178,f181,f204,f205,f207&"
        f"ut=7eea3edcaed734bea9cbfc24409ed989&"
        f"klt=101&fqt=0&"
        f"secid={secid}&"
        f"beg={start_date.strftime('%Y%m%d')}&"
        f"end={end_date.strftime('%Y%m%d')}"
    )
    
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://finance.eastmoney.com/'
    })
    
    opener = get_opener()
    with opener.open(req, timeout=15) as response:
        data = json.loads(response.read().decode('utf-8'))
    
    if data.get('data') and data['data'].get('klines'):
        klines = data['data']['klines']
        
        dates = []
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        volumes = []
        
        for line in klines:
            parts = line.split(',')
            dates.append(parts[0])
            open_prices.append(float(parts[1]))
            close_prices.append(float(parts[2]))
            high_prices.append(float(parts[3]))
            low_prices.append(float(parts[4]))
            volumes.append(float(parts[5]) * 100)
        
        result = {
            "stock_code": stock_code,
            "market": "A股" if len(stock_code) == 6 else "港股",
            "dates": dates,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volumes,
        }
        
        result['ma20'] = calculate_ma(result['close'], 20)
        result['ma60'] = calculate_ma(result['close'], 60)
        result['atr'] = calculate_atr(result['high'], result['low'], result['close'])
        result['volume_ma20'] = calculate_ma(result['volume'], 20)
        
        return result
    
    return {"error": "无数据"}


def get_data_sina(stock_code):
    """使用新浪API获取数据"""
    
    if len(stock_code) == 6:
        prefix = 'sh' if stock_code.startswith('6') else 'sz'
        code = f"{prefix}{stock_code}"
    else:
        code = f"hk{stock_code}"
    
    url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale=240&datalen=60&ma=no"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    opener = get_opener()
    with opener.open(req, timeout=15) as response:
        raw = response.read().decode('utf-8')
    
    data = json.loads(raw)
    
    if data:
        result = {
            "stock_code": stock_code,
            "market": "A股" if len(stock_code) == 6 else "港股",
            "dates": [d['day'] for d in data],
            "open": [float(d['open']) for d in data],
            "close": [float(d['close']) for d in data],
            "high": [float(d['high']) for d in data],
            "low": [float(d['low']) for d in data],
            "volume": [float(d['volume']) for d in data],
        }
        
        result['ma20'] = calculate_ma(result['close'], 20)
        result['ma60'] = calculate_ma(result['close'], 60)
        result['atr'] = calculate_atr(result['high'], result['low'], result['close'])
        result['volume_ma20'] = calculate_ma(result['volume'], 20)
        
        return result
    
    return {"error": "无数据"}


def calculate_ma(prices, period):
    """计算移动平均线"""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            avg = sum(prices[i-period+1:i+1]) / period
            result.append(round(avg, 2))
    return result


def calculate_atr(high, low, close, period=14):
    """计算平均真实波幅 (ATR)"""
    tr = []
    for i in range(len(high)):
        if i == 0:
            tr.append(high[i] - low[i])
        else:
            h_l = high[i] - low[i]
            h_c = abs(high[i] - close[i-1])
            l_c = abs(low[i] - close[i-1])
            tr.append(max(h_l, h_c, l_c))
    
    result = []
    for i in range(len(tr)):
        if i < period - 1:
            result.append(None)
        else:
            avg = sum(tr[i-period+1:i+1]) / period
            result.append(round(avg, 2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stock_data.py <stock_code> [days]")
        print(__doc__)
        sys.exit(1)
    
    stock_code = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    print(f"正在获取 {stock_code} 的数据...")
    print(f"代理配置: {get_proxy_dict()}")
    
    data = get_stock_data(stock_code, days)
    print(json.dumps(data, ensure_ascii=False, indent=2))
