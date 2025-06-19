
from libs.name_adjuster.name_adjuster import NameAdjuster      #sys.path.appendするよりよい
import pickle
import pandas as pd
import numpy as np
import datetime
import os
import streamlit as st

class SeqParamsOutputter():
    """
    販売量と期首在庫を順序シミュ用に出力するクラス。
    暫定措置のため、拡張性はない
    
    """
    def __init__(self,sales_amount_df, init_stock_df, jissui_month_list, new_params_dir):
        
        self.params_folder_path = "./順序シミュ用パラメータ/ver0.0.2_杉浦作成_2024年度パラメータ_20240208"    #大元のパラメータファイル
        self.params_folder_path = "./順序シミュ用パラメータ/ver0.0.2_杉浦作成_2024年度パラメータ_20240208"    #大元のパラメータファイル
        self.init_stock_file_path = self.params_folder_path + "/期首在庫.xlsx"
        self.sales_file_path = self.params_folder_path + "/販売計画.xlsx"
        self.quality_ratio_path = self.params_folder_path + "/品質収率.xlsx"
        self.basic_info_path = self.params_folder_path + "/製品基本データ.xlsx"
        self.name_path = self.params_folder_path+"/名称対応表.xlsx"
        
        self.sales_amount_df = sales_amount_df      #販売量の結果df
        self.init_stock_df = init_stock_df          #機首在庫のdf
        self.jissui_month_list = jissui_month_list  #実推月
        self.plant_list = ["L1","L2","L3","L4","L5","L6","L7"] #工場リスト
        
        
        self.new_params_dir = new_params_dir
        
        os.mkdir(self.new_params_dir)
   
    
    def get_org_params(self,plant):
        """
        杉浦さん作成パラメータを読み込む

        Args:
            plant (_type_): _description_

        Returns:
            _type_: _description_
        """
        init_stock_df_org = pd.read_excel(self.init_stock_file_path,sheet_name=plant)       #
        sales_file_df = pd.read_excel(self.sales_file_path,sheet_name=plant)
        quality_ratio_df = pd.read_excel(self.quality_ratio_path,sheet_name=plant)
        basic_info_df = pd.read_excel(self.basic_info_path,sheet_name=plant)
        name_df = pd.read_excel(self.name_path,sheet_name=plant)
        
        
        return init_stock_df_org, sales_file_df, quality_ratio_df, basic_info_df, name_df
        
        
    def preprocessing(self,plant,quality_ratio_df,basic_info_df,):
        """
        パラメータファイルがいけていないことによる謎前処理。
        
        インスタンス変数書き換えたがまあ暫定なので気にしない

        Args:
            plant (_type_): _description_
        """
        

        
        quality_ratio_df = quality_ratio_df.drop(columns=["巻長・巻き方"])
        #init_stock_df_org = init_stock_df_org.rename(columns={'優先品質': '品質'})
        basic_info_df = basic_info_df.rename(columns={"巻長・巻き方":"通称"})
        
        part_sales_amount_df = self.sales_amount_df[self.sales_amount_df["工場"] == plant].drop(columns=["工場"]).rename(columns={"品種名":"通称"})
        part_init_stock_df = self.init_stock_df[self.init_stock_df["工場"] == plant].drop(columns=["工場"]).rename(columns={"品種名":"通称"})
        

        return quality_ratio_df, basic_info_df,part_init_stock_df, part_sales_amount_df    
    
    
    
    def get_preprocess_org(self,plant):
        init_stock_df_org, sales_file_df,\
        quality_ratio_df, basic_info_df, name_df  = self.get_org_params(plant)
        
        quality_ratio_df, basic_info_df,part_init_stock_df, part_sales_amount_df = self.preprocessing(plant,quality_ratio_df,basic_info_df)
        
        return init_stock_df_org, sales_file_df,quality_ratio_df,basic_info_df,name_df,part_init_stock_df, part_sales_amount_df
        
        
    
    
    
    
    
    
    
    
    
    def merge_process(self,name_df, quality_ratio_df,basic_info_df,init_stock_df,sales_amount_df):
        """
        結合して大きなdfを作る

        Args:
            name_df (_type_): _description_
            quality_ratio_df (_type_): _description_
            basic_info_df (_type_): _description_
            init_stock_df (_type_): _description_

        Returns:
            _type_: _description_
        """
        # 左結合
        #left_join_df = pd.merge(name_df, init_stock_df_org, on='品質', how='left')
        left_join_df = pd.merge(name_df, quality_ratio_df, on='品質', how='left')               
        left_join_df = pd.merge(left_join_df, basic_info_df,on="通称",how="left")
        left_join_df = pd.merge(left_join_df, init_stock_df,on="通称",how="left")      #仮に割り当て側にはあっても、名称対応表にないものは消されるので注意。
        left_join_df_filtered = left_join_df[left_join_df['収率'] != 0].dropna()       #L1のSAZMA表記ゆれが解消したらこれいらなくなる。

        left_join_df_filtered2 = pd.merge(left_join_df_filtered, 
                                          sales_amount_df,on="通称",how="left")
        
        df_all = left_join_df_filtered2.drop_duplicates(subset=['通称'])
        
        #本数に直す

        for month in self.jissui_month_list:

            df_all.loc[:,month] = df_all.loc[:,month]*1000/(df_all["定尺"]*df_all["幅"])

        df_all.loc[:,"期首在庫"] = df_all.loc[:,"期首在庫"]*1000/(df_all["定尺"]*df_all["幅"])
                
                
        return df_all
    
    def get_new_init_stock_df(self,df_all,init_stock_df_org):
        #期首在庫の取り出し
        new_init_stock_df = pd.DataFrame(columns=init_stock_df_org.columns)
        new_init_stock_df["優先品質"] = init_stock_df_org["優先品質"]
        new_init_stock_df = new_init_stock_df.fillna(0)
        
        for index, row in df_all.iterrows():
            df1_index = new_init_stock_df[new_init_stock_df['優先品質'] == row['品質']].index
            new_init_stock_df.loc[df1_index, "期首在庫"] = row["期首在庫"]
        
        return new_init_stock_df
    
    def get_new_sales_df(self,df_all,sales_file_df):
        
        new_sales_df = pd.DataFrame(columns=sales_file_df.columns)
        new_sales_df["優先品質"] = sales_file_df["優先品質"]
        new_sales_df = new_sales_df.fillna(0)
        # df2のIDに基づいてdf1を上書き
        for index, row in df_all.iterrows():
            df1_index = new_sales_df[new_sales_df['優先品質'] == row['品質']].index
            for col in self.jissui_month_list:  # IDカラムを除外
                new_sales_df.loc[df1_index, col] = row[col]
        
        return new_sales_df
    
    
    
    
    def output_excel(self,df, filename, sheet_name, round_num=0,initial_flag=False):
        """
        エクセルファイルとしての書き出し
        一番初めに書き出す場合にinitial_flagをTrueにする
        
        """
        
        df = df.round(round_num)
        df = df.replace([np.inf, -np.inf], np.nan)
        
        if initial_flag == True:
            df.to_excel(self.new_params_dir+filename,sheet_name=sheet_name,index=None)
        
        else:
            with pd.ExcelWriter(self.new_params_dir+filename,engine='openpyxl', mode='a') as writer:
                df.to_excel(writer,sheet_name=sheet_name,index=None)
        
        return
    
    
    def main(self):
        for plant in self.plant_list:
            init_stock_df_org, sales_file_df,\
            quality_ratio_df,basic_info_df,name_df,part_init_stock_df, part_sales_amount_df = self.get_preprocess_org(plant)
            
            df_all = self.merge_process(name_df, quality_ratio_df,basic_info_df,part_init_stock_df, part_sales_amount_df)
            
            new_init_stock_df = self.get_new_init_stock_df(df_all,init_stock_df_org) 
            new_sales_df = self.get_new_sales_df(df_all,sales_file_df)
            
            initial_flag = False
            if plant == "L1":
                initial_flag = True
            
            self.output_excel(new_init_stock_df,"期首在庫.xlsx", plant,round_num=2, initial_flag=initial_flag)
            self.output_excel(new_sales_df,"販売計画.xlsx", plant,round_num=2, initial_flag=initial_flag)
        
        

if __name__ == "__main__": 
    import sys
    sys.path.append("./src/")
    with open("./test/sales_amount_df.pickle", mode='rb') as f:
    #with open("./src/test/sales_amount_df.pickle", mode='rb') as f:
        sales_amount_df = pickle.load(f)
    
    with open("./test/init_stock_dict.pickle", mode='rb') as f:
        init_stock_dict = pickle.load(f)
    
    SeqParamsOutputter(sales_amount_df,init_stock_dict)