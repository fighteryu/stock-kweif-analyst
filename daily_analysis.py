#!/usr/bin/env python3
"""
每日股票分析自动发送脚本
配合cron定时任务使用
"""

import json
import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from stock_data import get_stock_data
from analysis import analyze_volume_price
from target_price import calculate_target_price, calculate_support_resistance

def generate_report(stock_code):
    """生成分析报告"""
    
    print(f"正在分析股票: {stock_code}")
    
    # 获取数据
    data = get_stock_data(stock_code, days=60)
    
    if "error" in data:
        return f"数据获取失败: {data.get('error', '未知错误')}"
    
    # 分析
    analysis = analyze_volume_price(data)
    target = calculate_target_price(data)
    sr = calculate_support_resistance(data['close'], target['box_size'])
    
    current = data['close'][-1]
    
    # 生成报告
    report = f"""📊 股票技术分析 - {stock_code}

【基本信息】
• 当前价格: {current:.2f}元
• 20日均线: {analysis['ma20']:.2f}元
• 5日涨跌: {analysis['volume_relation']['price_change_pct']:.1f}%

【趋势判断】
• 当前趋势: {analysis['trend']['type']} ({analysis['trend']['strength']})
• 均线位置: {analysis['ma_analysis']['position']}

【量价分析】
• 量价模式: {analysis['volume_relation']['pattern']}
• 信号: {analysis['volume_relation']['signal']}

【交易建议】
• 操作: {analysis['recommendation']['action']}
• 仓位: {analysis['recommendation']['position']}

【止损建议】
• 止损价位: {analysis['stop_loss']['recommended']:.2f}元
• 止损比例: {analysis['stop_loss']['stop_loss_pct']:.1f}%

【目标价】
• 短期: {target['final']['short_term']:.2f}元 ({(target['final']['short_term']/current-1)*100:+.0f}%)
• 中期: {target['final']['mid_term']:.2f}元 ({(target['final']['mid_term']/current-1)*100:+.0f}%)
• 长期: {target['final']['long_term']:.2f}元 ({(target['final']['long_term']/current-1)*100:+.0f}%)

【支撑/阻力】
• 阻力: {sr.get('resistance', [])}
• 支撑: {sr.get('support', [])}

⚠️ 本分析仅供参考，不构成投资建议"""
    
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        stock_code = "600415"  # 默认分析小商品城
    else:
        stock_code = sys.argv[1]
    
    report = generate_report(stock_code)
    print(report)
