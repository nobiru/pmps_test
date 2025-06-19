
import streamlit as st
import pandas as pd
from linear_regressionner import LinearRegressionner
import io

class ApproxFormulaWeb():
    def __init__(self):
        self.all_sheet_name = ["L1月中切替","L2月中切替","L3月中切替","L4月中切替","L5月中切替","L6月中切替","L7月中切替"]
        self.all_plant_list = ["L1","L2","L3","L4","L5","L6","L7"]
    
    def main(self):
        
        file = st.file_uploader("切替時間のパラメータファイルアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        #ファイルがアップロードされたら
        if file is not None:
            
            switch_dict ={}
            flattened_dict = {}
            for plant in self.all_plant_list:
                df = pd.read_excel(file,sheet_name=f"{plant}月中切替")
                linear_model_dict = LinearRegressionner(df).main()
                st.write(linear_model_dict)
            
            
            
                
                        
            
            
                switch_dict[plant] = linear_model_dict
                flattened_dict[plant] = pd.DataFrame([linear_model_dict])
            
            
            st.write(switch_dict)
            st.write(flattened_dict["L1"])
            
            # 入れ子の辞書を平坦化する
            # flattened_data = pd.json_normalize(df_switch_dict, sep='_')
            
            # # DataFrameをExcelファイルに変換
            # output = io.BytesIO()
            # with pd.ExcelWriter(output, engine='openpyxl') as writer:
            #     flattened_data.to_excel(writer, index=False, sheet_name='Sheet1')
            # output.seek(0)

            # # ダウンロードボタンを作成
            # btn = st.download_button(
            #     label="結果ファイルダウンロード",
            #     data=output,
            #     file_name="結果ファイル.xlsx",  # ファイル名に.xlsx拡張子を付ける
            #     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            #     key="result"
            # )