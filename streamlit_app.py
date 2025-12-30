# -*- coding: utf-8 -*-
"""
手机可用版本（推荐）
Streamlit Web 表单 — 省份自动切换权重
部署后手机浏览器打开链接即可使用（可“添加到主屏幕”当App）。
"""
import pandas as pd
import streamlit as st
from salary_logic import projects, calculate

st.set_page_config(page_title="武汉开明销售部季度绩效工资计算", layout="centered")

st.title("武汉开明销售部季度绩效工资计算")
st.caption("选择省份与项目 → 填写数据 → 一键计算绩效与汇总")

# ---------------- 省份对应权重表 ----------------
province_weights = {
    "新疆": {
        "业绩": 0.325,
        "毛利率": 0.25,
        "结算率": 0.025,
        "开票率": 0.05,
        "回款率": 0.2,
        "审计偏差": 0.05,
        "客情成本": 0.1
    },
    "山东": {
        "业绩": 0.425,
        "毛利率": 0.275,
        "结算率": 0.025,
        "开票率": 0.025,
        "回款率": 0.175,
        "审计偏差": 0.025,
        "客情成本": 0.05
    },
    "青海": {
        "业绩": 0.45,
        "毛利率": 0.25,
        "结算率": 0.025,
        "开票率": 0.025,
        "回款率": 0.15,
        "审计偏差": 0.025,
        "客情成本": 0.075
    },
    "湖北": {
        "业绩": 0.3,
        "毛利率": 0.35,
        "结算率": 0.1,
        "开票率": 0.025,
        "回款率": 0.075,
        "审计偏差": 0.05,
        "客情成本": 0.1
    },
    "华中地区": {
        "业绩": 0.4,
        "毛利率": 0.175,
        "结算率": 0.025,
        "开票率": 0.075,
        "回款率": 0.175,
        "审计偏差": 0.025,
        "客情成本": 0.125
    }
}

# ---------------- 表单输入区 ----------------
province = st.selectbox("选择省份", list(province_weights.keys()))
project = st.selectbox("项目名称", list(projects.keys()))

# 自动选择当前省份的权重
weights = province_weights[province]

df_weights = (
    pd.Series(weights, name="权重")
      .rename_axis("指标")
      .reset_index()
)
df_weights["权重(%)"] = (df_weights["权重"] * 100).round(2).astype(str) + "%"

st.subheader(f"📊 {province}省项目指标权重表")
st.dataframe(df_weights, use_container_width=True, hide_index=True)
st.info(f"提示：当前省份为 {province}，权重总和为 {sum(weights.values()):.2f}。")

# ---------------- 输入区 ----------------
col1, col2 = st.columns(2)
with col1:
    year_target = st.number_input("年度目标产值", min_value=0.0, value=5000000.0, step=10000.0, format="%.2f")
    quarter_actual = st.number_input("实际季度业绩", min_value=0.0, value=250000.0, step=10000.0, format="%.2f")
    margin = st.number_input("毛利率（如 -0.05）", min_value=-3.0, max_value=1.0, value=0.25, step=0.01, format="%.4f")
with col2:
    settlement_days = st.number_input("结算时间（工作日）", min_value=0, value=10, step=1)
    invoice_days = st.number_input("开票时间（工作日）", min_value=0, value=10, step=1)
    payback_days = st.number_input("回款时间（工作日）", min_value=0, value=30, step=1)

col3, col4 = st.columns(2)
with col3:
    audit_bias = st.number_input("审计偏差率（如 0.01）", min_value=0.0, value=0.01, step=0.001, format="%.4f")
with col4:
    customer_rate = st.number_input("客情费率（如 0.01）", min_value=0.0, value=0.01, step=0.001, format="%.4f")

tax_keep_rate = st.number_input("税后保留比例（默认 0.97）", min_value=0.0, max_value=1.0, value=0.97, step=0.001, format="%.3f")

# ---------------- 计算按钮 ----------------
if st.button("开始计算"):
    try:
        res = calculate(
            project=project,
            year_target=year_target,
            quarter_actual=quarter_actual,
            margin=margin,
            settlement_days=int(settlement_days),
            invoice_days=int(invoice_days),
            payback_days=int(payback_days),
            audit_bias=audit_bias,
            customer_rate=customer_rate,
            tax_keep_rate=tax_keep_rate,
        )
    except Exception as e:
        st.error(f"计算出错：{e}")
    else:
        st.success("✅ 计算完成")

        # ---------------- 汇总部分 ----------------
        st.subheader("汇总")
        st.write(f"**业绩完成率：** {res.performance_rate*100:.2f}%")
        st.write(f"**总绩效得分：** {res.total_score:.2f}")
        st.write(f"**季度绩效工资：** {res.perf_money:.2f}")
        st.write(f"**季度总工资（税前）：** {res.total_salary:.2f}")
        st.write(f"**季度税后总工资：** {res.after_tax_salary:.2f}")

        # ---------------- 评分明细 ----------------
        st.subheader("评分明细")
        df = pd.DataFrame(res.breakdown)
        st.dataframe(df, use_container_width=True)
