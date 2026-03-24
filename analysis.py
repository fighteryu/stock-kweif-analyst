#!/usr/bin/env python3
"""
股票量价分析脚本
基于科威夫(Wyckoff)量价分析方法
"""

import json
import sys

def analyze_volume_price(data):
    """
    量价分析核心函数
    
    Args:
        data: 股票数据字典
    
    Returns:
        dict: 分析结果
    """
    
    close = data['close']
    volume = data['volume']
    ma20 = data.get('ma20', [None]*len(close))
    ma60 = data.get('ma60', [None]*len(close))
    high = data['high']
    low = data['low']
    
    # 取最近数据
    n = len(close)
    current_price = close[-1]
    current_volume = volume[-1]
    
    # 计算技术指标
    ma20_current = ma20[-1] if ma20[-1] else current_price
    ma60_current = ma60[-1] if n > 60 and ma60[-1] else current_price
    
    # 1. 趋势判断
    trend =判断趋势(close, ma20, ma60)
    
    # 2. 量价关系分析
    volume_relation = 分析量价关系(close, volume, n)
    
    # 3. 均线分析
    ma_analysis = 分析均线位置(close, ma20, ma60)
    
    # 4. 信号识别
    signals = 识别信号(close, volume, high, low, ma20, volume)
    
    # 5. 交易建议
    recommendation = 生成建议(trend, volume_relation, ma_analysis, signals)
    
    # 6. 止损价
    stop_loss = 计算止损价(close, ma20, signals)
    
    return {
        "current_price": current_price,
        "ma20": ma20_current,
        "ma60": ma60_current,
        "trend": trend,
        "volume_relation": volume_relation,
        "ma_analysis": ma_analysis,
        "signals": signals,
        "recommendation": recommendation,
        "stop_loss": stop_loss
    }

def 判断趋势(close, ma20, ma60):
    """判断价格趋势"""
    if len(close) < 20:
        return {"type": "震荡", "strength": "弱"}
    
    current_close = close[-1]
    current_ma20 = ma20[-1] if ma20[-1] else current_close
    
    # 判断20日均线方向
    ma20_direction = "上行" if ma20[-1] > ma20[-5] else "下行" if ma20[-1] < ma20[-5] else "走平"
    
    if current_close > current_ma20:
        if ma20_direction == "上行":
            return {"type": "上涨", "strength": "强"}
        return {"type": "上涨", "strength": "中"}
    elif current_close < current_ma20:
        if ma20_direction == "下行":
            return {"type": "下跌", "strength": "强"}
        return {"type": "下跌", "strength": "中"}
    else:
        return {"type": "震荡", "strength": "弱"}

def 分析量价关系(close, volume, n):
    """分析量价关系"""
    if n < 20:
        return {"status": "数据不足"}
    
    # 最近5天的量价变化
    price_change = close[-1] - close[-5]
    volume_change = volume[-1] - volume[-5]
    
    # 20日均量
    vol_ma20 = sum(volume[-20:]) / 20
    current_vol_ratio = volume[-1] / vol_ma20 if vol_ma20 > 0 else 1
    
    # 经典量价模式识别
    if price_change > 0 and volume_change > 0:
        pattern = "放量上涨"
        signal = "健康上涨"
    elif price_change > 0 and volume_change < 0:
        pattern = "缩量上涨"
        signal = "量价背离，警惕顶背离"
    elif price_change < 0 and volume_change > 0:
        pattern = "放量下跌"
        signal = "可能最后一跌"
    elif price_change < 0 and volume_change < 0:
        pattern = "缩量下跌"
        signal = "趋势延续"
    else:
        pattern = "横盘"
        signal = "观望"
    
    return {
        "pattern": pattern,
        "signal": signal,
        "volume_ratio": round(current_vol_ratio, 2),
        "price_change_pct": round(price_change/close[-5]*100, 2)
    }

def 分析均线位置(close, ma20, ma60):
    """分析均线位置关系"""
    if len(close) < 60:
        return {"position": "数据不足"}
    
    current_close = close[-1]
    current_ma20 = ma20[-1] if ma20[-1] else current_close
    current_ma60 = ma60[-1] if ma60[-1] else current_close
    
    if current_close > current_ma20 > current_ma60:
        return {"position": "多头排列", "bullish": True}
    elif current_close < current_ma20 < current_ma60:
        return {"position": "空头排列", "bullish": False}
    else:
        return {"position": "均线缠绕", "bullish": None}

def 识别信号(close, volume, high, low, ma20, volume_list):
    """识别关键交易信号"""
    signals = []
    n = len(close)
    
    if n < 20:
        return ["数据不足"]
    
    # 放量突破信号
    vol_ma20 = sum(volume[-20:]) / 20
    if volume[-1] > vol_ma20 * 1.5 and close[-1] > (ma20[-1] if ma20[-1] else close[-1]):
        signals.append("放量突破20日均线 - 买入信号")
    
    # 缩量回调企稳信号
    if volume[-1] < vol_ma20 * 0.5 and close[-1] > close[-3] and close[-1] > (ma20[-1] if ma20[-1] else close[-1]):
        signals.append("缩量回调企稳 - 买入机会")
    
    # 放量跌破信号
    if volume[-1] > vol_ma20 * 1.5 and close[-1] < (ma20[-1] if ma20[-1] else close[-1]):
        signals.append("放量跌破20日均线 - 卖出信号")
    
    # 锤子线信号
    if n >= 5:
        body = abs(close[-1] - close[-2])
        lower_shadow = min(close[-1], close[-2]) - low[-1]
        if lower_shadow > body * 2 and lower_shadow > (high[-1] - max(close[-1], close[-2])) * 0.5:
            signals.append("锤子线 - 底部信号")
    
    # 射击之星信号
    if n >= 5:
        body = abs(close[-1] - close[-2])
        upper_shadow = high[-1] - max(close[-1], close[-2])
        if upper_shadow > body * 2 and upper_shadow > (min(close[-1], close[-2]) - low[-1]) * 0.5:
            signals.append("射击之星 - 顶部信号")
    
    if not signals:
        signals.append("无明显信号")
    
    return signals

def 生成建议(trend, volume_relation, ma_analysis, signals):
    """生成交易建议"""
    trend_type = trend['type']
    trend_strength = trend['strength']
    pattern = volume_relation['pattern']
    
    # 简化逻辑
    if trend_type == "上涨" and volume_relation['pattern'] in ["放量上涨", "缩量上涨"]:
        if volume_relation['pattern'] == "放量上涨":
            action = "加仓"
            position = "可加仓20-30%"
            reason = "上涨趋势中的放量上涨，健康走势"
        else:
            action = "持有观察"
            position = "保持当前仓位"
            reason = "缩量上涨需警惕量价背离"
    
    elif trend_type == "下跌" and volume_relation['pattern'] in ["放量下跌", "缩量下跌"]:
        action = "止损减仓"
        position = "建议减仓50%"
        reason = "下跌趋势中应减少损失"
    
    elif trend_type == "上涨" and volume_relation['pattern'] in ["放量下跌"]:
        action = "部分减仓"
        position = "可减仓30%"
        reason = "上涨趋势中的放量下跌需警惕"
    
    elif trend_type == "震荡":
        if volume_relation['pattern'] == "缩量下跌":
            action = "可以建仓"
            position = "建议10-20%"
            reason = "震荡底部缩量，可能是机会"
        elif volume_relation['pattern'] == "放量上涨":
            action = "积极建仓"
            position = "建议30%"
            reason = "放量突破，趋势向好"
        else:
            action = "观望"
            position = "暂时持有"
            reason = "震荡行情，保持谨慎"
    
    else:
        action = "观望"
        position = "保持现有仓位"
        reason = "等待更明确信号"
    
    return {
        "action": action,
        "position": position,
        "reason": reason,
        "signals": signals
    }

def 计算止损价(close, ma20, signals):
    """计算止损价"""
    current_price = close[-1]
    ma20_price = ma20[-1] if ma20[-1] else current_price
    
    # 三种止损方式取保守值
    stop_loss_fixed = current_price * 0.92  # 8%固定止损
    stop_loss_ma = ma20_price  # 均线止损
    
    # 推荐止损价（取较保守的）
    recommended = min(stop_loss_fixed, stop_loss_ma)
    
    return {
        "fixed_8pct": round(stop_loss_fixed, 2),
        "ma20": round(stop_loss_ma, 2),
        "recommended": round(recommended, 2),
        "stop_loss_pct": round((current_price - recommended) / current_price * 100, 2)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analysis.py <stock_data.json>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
    
    result = analyze_volume_price(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
