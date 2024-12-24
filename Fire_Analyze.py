import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 日本語フォントを指定（Windowsの場合は「MS Gothic」など）
rcParams['font.family'] = 'MS Gothic'

import sqlite3

# データベースの初期化
conn = sqlite3.connect("expenses.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    category TEXT,
    cost INTEGER
)
""")
conn.commit()

# ヘルパー関数
def add_expense(category, cost):
    c.execute("INSERT INTO expenses (category, cost) VALUES (?, ?)", (category, cost))
    conn.commit()

def get_expenses():
    c.execute("SELECT category, cost FROM expenses")
    return pd.DataFrame(c.fetchall(), columns=["カテゴリー", "費用"])

def calculate_annual_income(total_expenses, inflation_rate, years):
    return total_expenses * 12 * ((1 + inflation_rate) ** years)

def calculate_fi(total_expenses, inflation_rate, years, investment_return):
    annual_expenses = total_expenses * 12 * ((1 + inflation_rate) ** years)
    return annual_expenses / investment_return

# タイトル
st.title("将来必要な費用計算アプリ")

# サイドバーで費用をまとめて入力
st.sidebar.header("費用の一括入力")
with st.sidebar.form("expense_form"):
    categories = st.text_area("カテゴリー名（カンマ区切り）", placeholder="例: 家賃, 食費, 交通費")
    costs = st.text_area("費用（カンマ区切り）", placeholder="例: 50000, 30000, 10000")
    submitted = st.form_submit_button("一括追加")
    if submitted:
        try:
            # 入力を処理
            category_list = categories.split(",")
            cost_list = [int(cost.strip()) for cost in costs.split(",")]
            if len(category_list) == len(cost_list):
                for category, cost in zip(category_list, cost_list):
                    add_expense(category.strip(), cost)
                st.sidebar.success("データを一括追加しました！")
            else:
                st.sidebar.error("カテゴリーと費用の数が一致していません。")
        except ValueError:
            st.sidebar.error("費用には数値を入力してください。")

# 費用一覧の表示
expenses_df = get_expenses()
if not expenses_df.empty:
    st.subheader("費用一覧")
    st.dataframe(expenses_df)

    # 合計費用
    total_expenses = expenses_df["費用"].sum()
    st.write(f"### 月の合計費用: {total_expenses:,} 円")

    # 必要収入を計算
    inflation_rate = st.slider("想定インフレ率（%）", 0.0, 5.0, 2.0) / 100
    years = st.slider("目標達成までの年数", 1, 50, 10)
    if st.button("必要収入を計算"):
        annual_income_needed = calculate_annual_income(total_expenses, inflation_rate, years)
        st.write(f"### 必要な年間収入（将来価値）: {annual_income_needed:,.0f} 円")

    # FIを計算
    investment_return = st.slider("投資の想定利回り（%）", 1.0, 10.0, 4.0) / 100
    if st.button("FIに必要な金額を計算"):
        fi_amount = calculate_fi(total_expenses, inflation_rate, years, investment_return)
        st.write(f"### FIに必要な総額: {fi_amount:,.0f} 円")

    # 費用のグラフ表示
    st.subheader("費用の視覚化")
    fig, ax = plt.subplots()
    expenses_df.plot(kind="bar", x="カテゴリー", y="費用", ax=ax, legend=False, color="skyblue")
    ax.set_ylabel("費用（円）")
    ax.set_title("カテゴリーごとの費用")
    st.pyplot(fig)

else:
    st.write("まだ費用が入力されていません。サイドバーから入力してください。")

# データ削除オプション
if st.sidebar.button("データをリセット"):
    c.execute("DELETE FROM expenses")
    conn.commit()
    st.sidebar.success("データベースをリセットしました！")

# アプリ終了時の接続クローズ
st.sidebar.write("アプリを閉じるとデータベースの接続が自動で切れます。")
