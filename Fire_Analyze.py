import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# データベース接続
conn = sqlite3.connect("expenses.db")
c = conn.cursor()

# 新しいテーブルを作成（もし存在しない場合）
c.execute(""" 
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    category TEXT,
    product TEXT,
    cost INTEGER
)
""")
conn.commit()

# ヘルパー関数
def add_expense(category, product, cost):
    c.execute("INSERT INTO expenses (category, product, cost) VALUES (?, ?, ?)", (category, product, cost))
    conn.commit()

def get_expenses():
    c.execute("SELECT id, category, product, cost FROM expenses")
    return c.fetchall()

def delete_expenses(expense_ids):
    for expense_id in expense_ids:
        c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()

# タイトル
st.title("費用管理アプリ")

# サイドバーでカテゴリーを選択し、商品名と費用を一括入力
st.sidebar.header("費用の一括入力")

# 既存カテゴリを取得
categories = ["家賃", "食費", "交通費", "趣味"]  # カテゴリがない場合のデフォルト

category = st.sidebar.selectbox("カテゴリーを選択", categories)
with st.sidebar.form("expense_form"):
    products = st.text_area("商品名（カンマ区切り）", placeholder="例: 家賃, 食費, 交通費")
    costs = st.text_area("費用（カンマ区切り）", placeholder="例: 50000, 30000, 10000")
    submitted = st.form_submit_button("一括追加")
    if submitted:
        try:
            # 入力された商品名と費用を処理
            product_list = products.split(",")
            cost_list = [int(cost.strip()) for cost in costs.split(",")]
            if len(product_list) == len(cost_list):
                for product, cost in zip(product_list, cost_list):
                    add_expense(category, product.strip(), cost)
                st.sidebar.success("データを一括追加しました！")
            else:
                st.sidebar.error("商品名と費用の数が一致していません。")
        except ValueError:
            st.sidebar.error("費用には数値を入力してください。")

# FIREページ
st.header("FIRE (Financial Independence, Retire Early) 目標")

# 予測年収計算
years = st.sidebar.number_input("予測する年数", min_value=1, max_value=50, value=10, step=1)

# 費用一覧の表示（DataFrameとして表示）
expenses = get_expenses()
if expenses:
    st.subheader("費用一覧")
    
    # DataFrameに変換
    expenses_df = pd.DataFrame(expenses, columns=["ID", "カテゴリー", "商品名", "費用"])
    
    # 表を表示
    st.dataframe(expenses_df.drop("ID", axis=1))  # IDは表示しない
    
    # チェックボックスを表示する
    selected_ids_to_delete = []
    for index, row in expenses_df.iterrows():
        expense_id = row['ID']
        product_name = row['商品名']  # 商品名を表示
        checkbox = st.checkbox(f"削除: {product_name}", key=f"delete_{expense_id}")
        if checkbox:
            selected_ids_to_delete.append(expense_id)

    # 削除ボタン
    if st.button("選択した項目を削除"):
        if selected_ids_to_delete:
            delete_expenses(selected_ids_to_delete)
            st.success(f"{len(selected_ids_to_delete)} 項目が削除されました。")
            st.rerun()  # ページを再読み込みして最新のデータを表示
        else:
            st.warning("削除する項目を選択してください。")

    # ダウンロードボタンを追加
    def to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Expenses')
        return output.getvalue()

    def to_json(df):
        return df.to_json(orient="records", lines=True).encode('utf-8')

    # ダウンロードオプション
    st.subheader("データダウンロード")
    
    # CSVとしてダウンロード
    csv = to_csv(expenses_df)
    st.download_button(
        label="CSVとしてダウンロード",
        data=csv,
        file_name="expenses.csv",
        mime="text/csv"
    )
    
    # Excelとしてダウンロード
    excel = to_excel(expenses_df)
    st.download_button(
        label="Excelとしてダウンロード",
        data=excel,
        file_name="expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # JSONとしてダウンロード
    json = to_json(expenses_df)
    st.download_button(
        label="JSONとしてダウンロード",
        data=json,
        file_name="expenses.json",
        mime="application/json"
    )

    # グラフ作成
    st.subheader("費用のカテゴリ別合計")
    category_costs = expenses_df.groupby("カテゴリー")["費用"].sum()
    fig, ax = plt.subplots()
    category_costs.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title("カテゴリー別合計費用")
    ax.set_ylabel("費用")
    ax.set_xlabel("カテゴリー")
    
    # グラフを表示
    st.pyplot(fig)

    # グラフ画像をダウンロード
    def get_image(fig):
        img_stream = BytesIO()
        fig.savefig(img_stream, format='png')
        img_stream.seek(0)
        return img_stream.read()

    # ダウンロードボタン（グラフ画像）
    graph_image = get_image(fig)
    st.download_button(
        label="グラフを画像としてダウンロード",
        data=graph_image,
        file_name="category_expenses.png",
        mime="image/png"
    )

# アプリ終了時の接続クローズ
st.sidebar.write("アプリを閉じるとデータベースの接続が自動で切れます。")
