import streamlit as st
import sqlite3
import pandas as pd

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

# カテゴリテーブルを作成（もし存在しない場合）
c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    category_name TEXT
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

def add_category(category_name):
    c.execute("INSERT INTO categories (category_name) VALUES (?)", (category_name,))
    conn.commit()

def get_categories():
    c.execute("SELECT category_name FROM categories")
    return [row[0] for row in c.fetchall()]

def delete_category(category_name):
    c.execute("DELETE FROM categories WHERE category_name = ?", (category_name,))
    conn.commit()

# タイトル
st.title("費用管理アプリ")

# サイドバーでカテゴリーを選択し、商品名と費用を一括入力
st.sidebar.header("費用の一括入力")

# 既存カテゴリを取得
categories = get_categories()
categories = categories if categories else ["家賃", "食費", "交通費", "趣味"]  # カテゴリがない場合のデフォルト

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

# カテゴリ追加フォーム
st.sidebar.header("カテゴリ追加")
new_category = st.sidebar.text_input("新しいカテゴリー名を入力")
if st.sidebar.button("カテゴリを追加"):
    if new_category:
        add_category(new_category)
        st.sidebar.success(f"新しいカテゴリー「{new_category}」が追加されました！")
        st.rerun()  # ページを再読み込みして最新のデータを表示
    else:
        st.sidebar.error("カテゴリ名を入力してください。")

# カテゴリ削除フォーム
st.sidebar.header("カテゴリ削除")
category_to_delete = st.sidebar.selectbox("削除するカテゴリーを選択", categories)
if st.sidebar.button("カテゴリを削除"):
    if category_to_delete:
        delete_category(category_to_delete)
        st.sidebar.success(f"カテゴリー「{category_to_delete}」が削除されました！")
        st.rerun()  # ページを再読み込みして最新のデータを表示
    else:
        st.sidebar.error("削除するカテゴリーを選択してください。")

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
else:
    st.write("まだ費用が入力されていません。サイドバーから入力してください。")

# アプリ終了時の接続クローズ
st.sidebar.write("アプリを閉じるとデータベースの接続が自動で切れます。")
