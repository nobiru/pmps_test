# 必要なライブラリをインポート
import streamlit as st
import numpy as np
import pandas as pd
import pulp
from pulp import LpProblem, LpVariable, LpMaximize, LpBinary, LpStatus

# GUI上に表示するタイトルと、文章を設定
st.title("ナップサック問題をGUIで解く")
st.write("制約条件を入れてね")

# 品物リスト
lt=["牛乳", "おにぎり", "サンドイッチ"]
# 牛乳、おにぎり、サンドイッチの容量のリスト。それぞれ一個ずつある。
w=[1, 0.7, 0.5]
# 牛乳、おにぎり、サンドイッチの値段のリスト
v=[200, 150, 120]
# 制約条件：ナップサックの容量。GUI上で操作できるようにst.number_input関数を使用して設定。
W = st.number_input("ナップサックの容量を入れてね", min_value=1.0, max_value=10.0, value=1.0, step=1.0)

# 後で使うfor loopのためにリストの長さを変数rに格納
r = len(w)
# 数理モデルの箱を作成。今回は最大化問題。
problem = pulp.LpProblem(sense = pulp.LpMaximize)
# 変数の設定。ｘというリストを使う。
x = [pulp.LpVariable("x%d"%i, cat = LpBinary) for i in range(r)]
# 目的関数を設定
problem += pulp.lpDot(v, x)
# 制約条件を設定
problem += pulp.lpDot(w, x) <= W

# 実行ボタン。チェックボックスをGUI上でクリックしたら計算スタート。
agree = st.checkbox('条件設定が終わったらチェックしてね')
if agree:
    status = problem.solve()
    st.write("状態", pulp.LpStatus[status])
    tmp=[xs.value() for xs in x]
    st.write([lt[a] for a in range(len(lt)) if tmp[a] == 1])
    st.write("最大価値",problem.objective.value())