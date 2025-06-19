import pandas as pd
from openpyxl import load_workbook
import streamlit as st
from io import BytesIO


class NewParamsGetter():
    def __init__(self,prod_amount_dict,sales_amount_dict,all_params_dict,file):
        self.prod_amount_dict = prod_amount_dict
        self.sales_amount_dict = sales_amount_dict
        self.jissui_month_list = all_params_dict["jissui_month_list"]
        self.fuka_dict = all_params_dict["fuka_dict"]
        self.ave_switch_dict = all_params_dict["ave_switch_dict"]
        self.sales_dict = all_params_dict["sales_dict"]
        self.width_dict = all_params_dict["width_dict"]
        self.cs_dict = all_params_dict["cs_dict"]
        self.finalized_sales_dict = all_params_dict["finalized_sales_dict"]
        self.finalized_prod_dict = all_params_dict["finalized_prod_dict"]
        self.init_stock_dict = all_params_dict["init_stock_dict"]
        self.min_continuous_dict = all_params_dict["min_continuous_dict"]
        self.prod_num_times_dict = all_params_dict["prod_num_times_dict"]
        self.basic_stock_min_dict = all_params_dict["basic_stock_min_dict"]
        self.basic_stock_max_dict = all_params_dict["basic_stock_max_dict"]     #基準在庫Max
        self.achieve_rate_dict = all_params_dict["achieve_rate_dict"]
        #self.all_index = self.get_all_index()
        self.all_index = all_params_dict["all_index"]

        self.plant_prod_dict = all_params_dict["plant_prod_dict"]
        #self.plant_prod_dict = self.get_plant_prod_dict()
        self.plant_list = list(self.plant_prod_dict.keys())
        self.prod_plant_dict = all_params_dict["prod_plant_dict"]
        #self.prod_plant_dict = self.get_prod_plant_dict()
        
        self.std_fc_dict = all_params_dict["std_fc_dict"]
        self.std_vc_dict = all_params_dict["std_vc_dict"]
        
        
        
        self.all_prod_list = list(self.cs_dict.keys()) 
        
        
        self.sales_prod_order = all_params_dict["sales_prod_order"]                            #合計販売量のシートの品種カラムと同じ順序のリスト
        self.cs_prod_order = all_params_dict["cs_prod_order"]                                  #csのシートの品種カラムと同じ順序のリスト
        
        
        #self.cs_custom_order_ranking = {value: rank for rank, value in enumerate(self.cs_prod_order)}        #CSの品種順
        self.sales_custom_order_ranking = {value: rank for rank, value in enumerate(self.sales_prod_order)}  #キー品種名、value出現する順番
        
        
        self.file = file    #ファイルオブジェクト
        
    
    def get_sorted_df(self,df,order_mode="cs"):
        """
        
        csや合計販売量のパラメタファイルと同じ順になるようにソートされたdfにする
        
        
        """
        if order_mode == "cs":
            #df['カスタムランク'] = df['品種名'].map(self.cs_custom_order_ranking)
            df['カスタムランク'] = df.apply(lambda row: self.cs_prod_order.get((row['品種名'], row['工場'])), axis=1)
            #df = df.sort_values(by=["工場", 'カスタムランク'])
            df = df.sort_values(by=['カスタムランク'])
            sorted_df = df.drop('カスタムランク', axis=1)
            sorted_df = sorted_df.reset_index(drop=True)
            return sorted_df
        
    
    def convert_dict_to_df(self,amount_dict):
        """
        生産量や販売量の辞書データをデータフレームに変換
        
        """
        record_dict = {}
        df_list = []
        for prod_name in self.all_prod_list:
            record_dict["品種名"] = prod_name
            for plant in self.prod_plant_dict[prod_name]:
                record_dict["工場"] = plant
                for month in self.jissui_month_list:
                    record_dict[month] = [amount_dict[plant,month,prod_name].value()]
                    
                df_list.append(pd.DataFrame(record_dict))

        df_all = pd.concat(df_list)
        df_all[self.jissui_month_list] = df_all[self.jissui_month_list].apply(pd.to_numeric, errors='coerce')
        
        
        df_all = self.get_sorted_df(df_all)
        
        
        return df_all
    
    def update_old_with_calculated(self,df_old, df_calculated):
        # Normalize column names for merging
        df_calculated = df_calculated.rename(columns={'品種名': '品種'})

        # Merge the two sheets
        merged_df = df_old.merge(df_calculated, on=['工場', '品種'], how='left', suffixes=('', '_update'))

        # Define the corresponding columns for updating
        months_mapping = {month: f'{month}_update' for month in self.jissui_month_list}

        # Update the values in the original DataFrame
        for month, update_month in months_mapping.items():
            if month in merged_df.columns and update_month in merged_df.columns:
                merged_df[month] = merged_df[update_month].combine_first(merged_df[month])

        # Drop the temporary update columns
        df_new = merged_df.drop(columns=[col for col in merged_df.columns if col.endswith('_update')])
        
        df_masked = df_old.copy()
        # mask = df_old.notna()
        # df_masked[mask] = df_new[mask]
        
        # 数値セルをdf2の対応する値で更新
        for column in df_old.columns:
            mask = df_old[column].notna()
            df_masked.loc[mask, column] = df_new.loc[mask, column]
        

        return df_masked
    
    
    def update_file_obj(self, df_new_prod, df_new_sales):
        #あきらめ
        pass 
            

    
    
    
    
    
    def main(self):
        prod_amount_df = self.convert_dict_to_df(self.prod_amount_dict)                   #生産量のdf
        sales_amount_df = self.convert_dict_to_df(self.sales_amount_dict)                 #販売量のdf
        
        
        df_old_prod = pd.read_excel(self.file,sheet_name="確定生産量")
        df_old_sales = pd.read_excel(self.file,sheet_name="確定販売量")
        
        
        

        
        df_new_prod = self.update_old_with_calculated(df_old_prod,prod_amount_df)
        df_new_sales = self.update_old_with_calculated(df_old_sales,sales_amount_df)
        
        
        
        st.write("微調整済み確定生産量")
        st.write(df_new_prod)
        
        
        st.write("微調整済み確定販売量")
        st.write(df_new_sales)
        