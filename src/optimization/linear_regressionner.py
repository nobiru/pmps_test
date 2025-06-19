# 必要なライブラリのインポート
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

from sklearn.metrics import r2_score
class LinearRegressionner():
    def __init__(self,df):
        self.df = df                              #ある工場の切り替え時間のデータフレーム
        self.exclude_columns = {'ケースid', "ケースID",'切替時間',"保全前期","保全後期"}
        self.x_list = list(set(self.df.columns) - self.exclude_columns)
    
    
    
    
    def get_coef_dict(self,df):
        
        # yにNaNが含まれている行を除外
        df = df.dropna(subset=['切替時間'])
        
        X = df[self.x_list]
        y = df['切替時間']
        
        
        # 線形回帰モデルの作成とトレーニング
        model = LinearRegression()
        model.fit(X, y)

        # 線形回帰モデルの予測値を計算
        y_pred = model.predict(X)

        import streamlit as st
        ##st.write(X)
        #st.write(y)
        #st.write(y_pred.min())
        
        
        
        
        
        # 回帰係数の取得
        coefficients = model.coef_
        intercept = model.intercept_

        # 辞書形式で保存（カラム名をキーにする）
        coef_dict = {
            'intercept': intercept
        }
        for feature, coef in zip(X.columns, coefficients):
            coef_dict[feature] = coef
        
        
        return coef_dict
        
        
        
    
    
    
    
    def main(self):
        # 除外するカラムをセットで定義
        
        linear_model_dict = {}
        coef_dict_0 = self.get_coef_dict(self.df[(self.df["保全前期"]==0) & (self.df["保全後期"]==0)])
        coef_dict_1 = self.get_coef_dict(self.df[(self.df["保全前期"]==1) & (self.df["保全後期"]==0)])
        coef_dict_2 = self.get_coef_dict(self.df[(self.df["保全前期"]==0) & (self.df["保全後期"]==1)])
        coef_dict_3 = self.get_coef_dict(self.df[(self.df["保全前期"]==1) & (self.df["保全後期"]==1)])
        
        linear_model_dict["保全前期なし保全後期なし"] = coef_dict_0
        linear_model_dict["保全前期あり保全後期なし"] = coef_dict_1
        linear_model_dict["保全前期なし保全後期あり"] = coef_dict_2
        linear_model_dict["保全前期あり保全後期あり"] = coef_dict_3
        
        
        return linear_model_dict
    
    
    
    
    def main_inter(self):
        return self.get_coef_dict(self.df)