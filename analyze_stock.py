#!/usr/bin/env python3
"""
股票分析主脚本
整合数据获取、量价分析、目标价计算
"""

import json
import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def full_analysis(stock_code):
    """
    完整股票分析流程
    
    Args:
        stock_code: 股票代码
    
    Returns:
        dict: 完整分析报告
    """
    
    print(f"📊 正在分析股票: {stock_code}")
    print("=" * 50)
    
    # Step 1: 获取数据
    print("\n[1/4] 获取股票数据...")
    from stock_data import get_stock_data
    
    data = get_stock_data(stock_code, days=60)
    
    if "error" in data:
        print(f"❌ 数据获取失败: {data['error']}")
        return {"error": data['error']}
    
    current_price = data['close'][-1]
    print(f"✓ 获取到 {len(data['close'])} 个交易日数据")
    print(f"✓ 当前价格: {current_price}")
    
    # Step 2: 量价分析
    print("\n[2/4] 进行量价分析...")
    from analysis import analyze_volume_price
    
    analysis = analyze_volume_price(data)
    print(f"✓ 趋势判断: {analysis['trend']['type']} ({analysis['trend']['strength']})")
    print(f"✓ 量价模式: {analysis['volume_relation']['pattern']}")
    print(f"✓ 均线位置: {analysis['ma_analysis']['position']}")
    
    # Step 3: 目标价计算
    print("\n[3/4] 计算目标价...")
    from target_price import calculate_target_price, calculate_support_resistance
    
    target = calculate_target_price(data)
    support_resistance = calculate_support_resistance(data['close'], target['box_size'])
    print(f"✓ 短期目标: {target['final']['short_term']}")
    print(f"✓ 中期目标: {target['final']['mid_term']}")
    print(f"✓ 长期目标: {target['final']['long_term']}")
    
    # Step 4: 生成报告
    print("\n[4/4] 生成分析报告...")
    report = generate_report(stock_code, data, analysis, target, support_resistance)
    
    print("\n" + "=" * 50)
    print("✅ 分析完成!")
    
    return report

def generate_report(stock_code, data, analysis, target, support_resistance):
    """生成完整的分析报告"""
    
    close = data['close']
    current_price = close[-1]
    
    # 计算涨跌幅
    if len(close) >= 5:
        change_5d = (current_price - close[-5]) / close[-5] * 100
    else:
        change_5d = 0
    
    if len(close) >= 20:
        change_20d = (current_price - close[-20]) / close[-20] * 100
    else:
        change_20d = 0
    
    report = {
        "stock_code": stock_code,
        "market": data['market'],
        "data_date": data['dates'][-1] if data['dates'] else None,
        "current_price": current_price,
        "change_5d": round(change_5d, 2),
        "change_20d": round(change_20d, 2),
        "ma20": analysis['ma20'],
        "ma60": analysis['ma60'],
        "trend": analysis['trend'],
        "volume_analysis": analysis['volume_relation'],
        "ma_position": analysis['ma_analysis'],
        "signals": analysis['signals'],
        "recommendation": analysis['recommendation'],
        "stop_loss": analysis['stop_loss'],
        "target_price": target['final'],
        "support_resistance": support_resistance,
        "risk_warning": "本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"
    }
    
    return report

def print_report(report):
    """打印分析报告"""
    
    print("\n" + "=" * 60)
    print("📊 股票技术分析报告")
    print("=" * 60)
    
    print(f"\n【基本信息】")
    print(f"  股票代码: {report['stock_code']}")
    print(f"  市场: {report['market']}")
    print(f"  当前价格: {report['current_price']}")
    print(f"  5日涨跌: {report['change_5d']:+.2f}%")
    print(f"  20日涨跌: {report['change_20d']:+.2f}%")
    
    print(f"\n【技术指标】")
    print(f"  20日均线: {report['ma20']}")
    print(f"  60日均线: {report['ma60']}")
    
    print(f"\n【趋势判断】")
    print(f"  当前趋势: {report['trend']['type']}")
    print(f"  趋势强度: {report['trend']['strength']}")
    print(f"  均线位置: {report['ma_position']['position']}")
    
    print(f"\n【量价分析】")
    print(f"  量价模式: {report['volume_analysis']['pattern']}")
    print(f"  信号: {report['volume_analysis']['signal']}")
    print(f"  量比: {report['volume_analysis']['volume_ratio']}")
    
    print(f"\n【技术信号】")
    for signal in report['signals']:
        print(f"  • {signal}")
    
    print(f"\n【交易建议】")
    print(f"  操作: {report['recommendation']['action']}")
    print(f"  仓位: {report['recommendation']['position']}")
    print(f"  理由: {report['recommendation']['reason']}")
    
    print(f"\n【止损建议】")
    print(f"  止损价位: {report['stop_loss']['recommended']}")
    print(f"  止损比例: {report['stop_loss']['stop_loss_pct']:.1f}%")
    print(f"  (固定8%: {report['stop_loss']['fixed_8pct']}, 均线: {report['stop_loss']['ma20']})")
    
    print(f"\n【目标价】")
    print(f"  短期(1-2周): {report['target_price']['short_term']} ({(report['target_price']['short_term']/report['current_price']-1)*100:+.1f}%)")
    print(f"  中期(1-3月): {report['target_price']['mid_term']} ({(report['target_price']['mid_term']/report['current_price']-1)*100:+.1f}%)")
    print(f"  长期(3-6月): {report['target_price']['long_term']} ({(report['target_price']['long_term']/report['current_price']-1)*100:+.1f}%)")
    
    if report['support_resistance']:
        sr = report['support_resistance']
        print(f"\n【支撑/阻力】")
        print(f"  阻力位: {sr.get('resistance', [])}")
        print(f"  支撑位: {sr.get('support', [])}")
    
    print(f"\n【风险提示】")
    print(f"  {report['risk_warning']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_stock.py <stock_code> [--json]")
        print("  A股: 6位数字 (如 600519)")
        print("  港股: 5位数字 (如 00700)")
        print("  --json: 输出JSON格式")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    output_json = "--json" in sys.argv
    
    report = full_analysis(stock_code)
    
    if "error" not in report:
        if output_json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report)
    else:
        print(f"\n❌ 分析失败: {report['error']}")
