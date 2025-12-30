# -*- coding: utf-8 -*-
"""
业务逻辑：销售部门季度绩效工资计算
由原始命令行脚本抽离而来，方便接入 Web / 小程序 / App 前端。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List


BASE_MONTHLY = 6000
PERF_QUARTER_POOL = 36000

projects: Dict[str, Dict[str, float]] = {
    "新疆":  {"业绩":0.325,"毛利率":0.25,"结算率":0.025,"开票率":0.05,"回款率":0.2,"审计偏差":0.05,"客情成本":0.1},
    "山东":  {"业绩":0.425,"毛利率":0.275,"结算率":0.025,"开票率":0.025,"回款率":0.175,"审计偏差":0.025,"客情成本":0.05},
    "青海":  {"业绩":0.45,"毛利率":0.25,"结算率":0.025,"开票率":0.025,"回款率":0.15,"审计偏差":0.025,"客情成本":0.075},
    "湖北":  {"业绩":0.3,"毛利率":0.35,"结算率":0.10,"开票率":0.025,"回款率":0.075,"审计偏差":0.05,"客情成本":0.1},
    "华中区域": {"业绩":0.4,"毛利率":0.175,"结算率":0.025,"开票率":0.075,"回款率":0.175,"审计偏差":0.025,"客情成本":0.125}
}


def score_performance(rate: float) -> float:
    if rate < 0.6:
        return min(0, 0 - (0.6 - rate) * 300)
    elif 0.6 <= rate <= 0.8:
        return 20 + (rate - 0.6) * 200
    elif 0.8 < rate <= 1.5:
        return 60 + (rate - 0.8) * 200
    else:  # rate > 1.5
        return max(200, 200 + (rate - 1.5) * 400)


def score_margin(rate: float) -> float:
    if rate < 0.1:
        return min(0, 0 - (0.1 - rate) * 500)
    elif 0.1 <= rate <= 0.25:
        return (rate - 0.1) * 200
    elif 0.25 < rate <= 0.5:
        return 30 + (rate - 0.25) * 400
    else:  # rate > 0.5
        return 130 + (rate - 0.5) * 1000


def score_settlement(days: int) -> float:
    if days >= 20:
        return min(100, 100 - (days - 20) * 5)
    elif 1 < days < 20:
        return min(200, 200 - days * 5)
    elif days == 1:
        return 200
    else:
        return 200


def score_invoice(days: int) -> float:
    if days > 60:
        return min(-200, -200 - (days - 60) * 50)
    if 20 < days <= 60:
        return min(0, 0 - (days - 20) * 5)
    if 5 <= days <= 20:
        return min(125, 125 - (days - 5) * 8)
    return min(150, 150 - days * 5)


def score_payback(days: int) -> float:
    if days > 120:
        return min(-250, -250 - (days - 60) * 1)
    if 60 < days <= 120:
        return min(-10, -10 - (days - 60) * 4)
    if 20 < days <= 60:
        return min(150, 150 - (days - 20) * 4)
    return min(200, 200 - days * 2.5)


def score_audit_bias(rate: float) -> float:
    if 0 <= rate <= 0.02:
        return min(120, 120 - rate * 3000)
    elif 0.02 < rate <= 0.08:
        return min(60, 60 - (rate - 0.02) * 1000)
    else:
        return min(0, 60 - (rate - 0.08) * 800)


def score_customer_cost(rate: float) -> float:
    # 原脚本只覆盖 rate>=0.01；这里补齐 rate<0.01，避免 None
    if rate < 0.01:
        return 120
    if 0.01 <= rate <= 0.03:
        return min(120, 120 - (rate - 0.01) * 2000)
    return min(80, 80 - (rate - 0.03) * 4000)


@dataclass
class CalcResult:
    weights: Dict[str, float]
    performance_rate: float
    breakdown: List[Dict[str, Any]]
    total_score: float
    perf_money: float
    total_salary: float
    after_tax_salary: float


def calculate(
    year_target: float,
    quarter_actual: float,
    margin: float,
    settlement_days: int,
    invoice_days: int,
    payback_days: int,
    audit_bias: float,
    customer_rate: float,
    tax_keep_rate: float = 0.97,
) -> CalcResult:
    if year_target <= 0:
        raise ValueError("年度目标产值必须 > 0")
    if quarter_actual <= 0:
        raise ValueError("实际季度业绩必须 > 0")

    weights = projects[project]
    performance_rate = quarter_actual / (year_target / 4)

    scores = {
        "业绩": score_performance(performance_rate),
        "毛利率": score_margin(margin),
        "结算率": score_settlement(settlement_days),
        "开票率": score_invoice(invoice_days),
        "回款率": score_payback(payback_days),
        "审计偏差": score_audit_bias(audit_bias),
        "客情成本": score_customer_cost(customer_rate),
    }

    breakdown: List[Dict[str, Any]] = []
    weighted_total = 0.0
    for k, s in scores.items():
        w = float(weights.get(k, 0))
        ws = s * w
        weighted_total += ws
        breakdown.append({
            "项目": k,
            "原始得分": round(s, 2),
            "权重": round(w, 4),
            "加权得分": round(ws, 2),
            "累计得分": round(weighted_total, 2),
        })

    perf_money = PERF_QUARTER_POOL * (weighted_total / 100.0)
    total_salary = BASE_MONTHLY * 3 + perf_money
    after_tax_salary = total_salary * tax_keep_rate

    return CalcResult(
        weights=weights,
        performance_rate=performance_rate,
        breakdown=breakdown,
        total_score=weighted_total,
        perf_money=perf_money,
        total_salary=total_salary,
        after_tax_salary=after_tax_salary,
    )
