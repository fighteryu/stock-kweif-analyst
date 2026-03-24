#!/usr/bin/env python3
"""
目标价计算脚本
使用经典点图法 (Point and Figure Chart) 计算股票目标价
"""

import json
import sys
import math

def calculate_target_price(data, method="standard"):
    """
    计算目标价
    
    Args:
        data: 股票数据
        method: 计算方法 (standard/advanced)
    
    Returns:
        dict: 目标价信息
    """
    
    close_prices = data['close']
    high_prices = data['high']
    low_prices = data['low']
    atr = data.get('atr', [None]*len(close_prices))
    
    current_price = close_prices[-1]
    current_atr = None
    for a in reversed(atr):
        if a is not None:
            current_atr = a
            break
    
    # 计算箱体大小
    if current_atr:
        box_size = current_atr  # 使用ATR作为箱体
    else:
        box_size = current_price * 0.01  # 或使用1%原则
    
    # 方法一：标准目标价计算
    standard = calculate_standard_target(close_prices, box_size)
    
    # 方法二：趋势强度调整
    adjusted = calculate_adjusted_target(close_prices, standard)
    
    # 方法三：点图法原理
    pnf = calculate_pnf_target(close_prices, box_size)
    
    return {
        "current_price": current_price,
        "box_size": round(box_size, 2),
        "standard": standard,
        "adjusted": adjusted,
        "pnf": pnf,
        "final": {
            "short_term": round(adjusted['short_term'], 2),
            "mid_term": round(adjusted['mid_term'], 2),
            "long_term": round(adjusted['long_term'], 2)
        }
    }

def calculate_standard_target(close_prices, box_size):
    """标准目标价计算（基于百分比）"""
    current = close_prices[-1]
    
    # 基础目标
    short_term = current * 1.10   # 10%
    mid_term = current * 1.20    # 20%
    long_term = current * 1.50    # 50%
    
    # 计算近期涨幅
    if len(close_prices) >= 20:
        recent_change = (close_prices[-1] - close_prices[-20]) / close_prices[-20]
    else:
        recent_change = 0
    
    return {
        "short_term": short_term,
        "mid_term": mid_term,
        "long_term": long_term,
        "recent_change_pct": round(recent_change * 100, 2)
    }

def calculate_adjusted_target(close_prices, standard):
    """基于趋势强度调整目标价"""
    current = close_prices[-1]
    
    if len(close_prices) < 20:
        return standard
    
    # 计算20日均线斜率
    ma20 = sum(close_prices[-20:]) / 20
    ma20_prev = sum(close_prices[-25:-5]) / 20
    ma20_slope = (ma20 - ma20_prev) / ma20_prev
    
    # 判断趋势强度
    if ma20_slope > 0.03:  # 强势上涨
        multiplier = 1.5
    elif ma20_slope > 0.01:  # 温和上涨
        multiplier = 1.2
    elif ma20_slope < -0.03:  # 强势下跌
        multiplier = 0.7
    elif ma20_slope < -0.01:  # 温和下跌
        multiplier = 0.9
    else:  # 震荡
        multiplier = 1.0
    
    return {
        "short_term": round(current * (1 + 0.10 * multiplier), 2),
        "mid_term": round(current * (1 + 0.20 * multiplier), 2),
        "long_term": round(current * (1 + 0.50 * multiplier), 2)
    }

def calculate_pnf_target(close_prices, box_size):
    """
    点图法 (Point and Figure) 目标价计算
    
    原理：
    1. 只记录价格变动，忽略时间
    2. 上涨用X表示，下跌用O表示
    3. 需要3格转向才能改变列（3格原则）
    4. 目标价 = 突破点 + (列高 × 2)
    """
    
    if len(close_prices) < 30:
        return {"error": "数据不足"}
    
    current = close_prices[-1]
    
    # 构建简化版点图数据
    boxes = []
    for i, price in enumerate(close_prices):
        boxes.append({
            "price": price,
            "box_num": int(price / box_size)
        })
    
    # 找到最近一波上涨的X列高度
    up_cols = []  # 记录各列X的数量
    current_direction = None
    current_col_height = 0
    
    for i in range(1, len(boxes)):
        prev_box = boxes[i-1]['box_num']
        curr_box = boxes[i]['box_num']
        
        if curr_box > prev_box:  # 上涨
            if current_direction == "up":
                current_col_height += 1
            else:
                if current_direction == "down" and current_col_height >= 3:
                    up_cols.append(current_col_height)
                current_direction = "up"
                current_col_height = 1
        elif curr_box < prev_box:  # 下跌
            if current_direction == "down":
                current_col_height += 1
            else:
                if current_direction == "up" and current_col_height >= 3:
                    up_cols.append(current_col_height)
                current_direction = "down"
                current_col_height = 1
    
    # 最后一列也要算
    if current_direction == "up" and current_col_height >= 3:
        up_cols.append(current_col_height)
    
    # 使用最大的上涨列计算目标
    if up_cols:
        max_col_height = max(up_cols)
        
        # 点图法目标价公式：突破点 + (列高 × 2)
        short_term = current + (max_col_height * box_size)
        mid_term = current + (max_col_height * box_size * 1.5)
        long_term = current + (max_col_height * box_size * 2)
        
        return {
            "max_column_height": max_col_height,
            "short_term": round(short_term, 2),
            "mid_term": round(mid_term, 2),
            "long_term": round(long_term, 2),
            "method": "Point and Figure (3-box reversal)"
        }
    else:
        # 没有满足条件的列，使用默认计算
        return calculate_standard_target(close_prices, box_size)

def calculate_support_resistance(close_prices, box_size):
    """计算支撑位和阻力位"""
    
    if len(close_prices) < 20:
        return {}
    
    current = close_prices[-1]
    
    # 简单支撑阻力计算
    highs = sorted(close_prices[-20:], reverse=True)[:5]
    lows = sorted(close_prices[-20:])[:5]
    
    resistance = [round(h, 2) for h in highs[:3]]
    support = [round(l, 2) for l in lows[:3]]
    
    return {
        "resistance": resistance,
        "support": support,
        "current": round(current, 2)
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python target_price.py <stock_data.json>")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
    
    result = calculate_target_price(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
