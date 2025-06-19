import os
import sys
from pathlib import Path
from itertools import chain, combinations
import copy
import glob



import datetime
import pickle

import pandas as pd
import streamlit as st
from openpyxl import load_workbook


root_path = Path(__file__).resolve().parent.parent  # 上2階層上に移動してルートに到達
sys.path.append(str(root_path))                     # ルートディレクトリを sys.path に追加
from setup_paths import add_project_paths           #モジュールのパスの追加
add_project_paths()



from result_outputter import ResultOutputter
from seq_params_outputter import SeqParamsOutputter
from xl_decorator import XlDecorator
from xl_navigation_maker import XlNavigationMaker
from index_generator import CommonProcess
from contradiction_detector import ContradictionDetector



#from hierachical_mip import HierachicalMip


from linear_regressionner import LinearRegressionner
from hierachical_optimizer import HierachicalOptimizer





from output_config import SOLUTION_DIR,RESULT_DIR

#定数のimport
from constants import KAMIKI_MONTH_LIST, PLANT_LIST, OFFLINE_PLANT_LIST,\
                      JISSUI_LIST, ALL_MONTH_LIST,KAMIKI_MONTH_LIST,SHIMOKI_MONTH_LIST,\
                          SHEET_LIST,SWITCH_SHEET_LIST



class AllocationWeb():
    """
    工場・月度割り当て最適化シミュレータ
    
    """
    def __init__(self,plants_type="製膜工場"):
        

        self.sheet_list = SHEET_LIST                   #パラメータエクセルファイルのシート名
        self.switch_sheet_list = SWITCH_SHEET_LIST     #切替時間のパラメータ
        
        
        self.all_month_list = ALL_MONTH_LIST           #一年間の月名リスト
        self.kamiki_month_list = KAMIKI_MONTH_LIST     #上期月名リスト
        self.shimoki_month_list = SHIMOKI_MONTH_LIST   #下期月名リスト
        self.jissui_list = JISSUI_LIST                 #シナリオリスト
        
        if plants_type == "製膜工場":
            self.plant_list = PLANT_LIST                   #全工場リスト
        
        if plants_type == "オフライン工場":
            self.plant_list = OFFLINE_PLANT_LIST       #オフライン工場リスト
            #st.write(self.plant_list)
        
        self.result_dir = RESULT_DIR
        
        
        #制約条件リスト(3/30 負荷時間一致制約を除いた。)
        self.all_constraint_list = [
                                    "負荷時間以下制約",
                                    "合計販売量一致制約","月末在庫0以上制約",
                                    "基準在庫月数Min以上制約","基準在庫月数Max以下制約",
                                    "最低生産回数以上制約","最大生産回数以下制約",
                                    "最低連続生産時間以上制約","確定生産量一致制約",
                                    "確定販売量一致制約"]
        
        #必須の制約条件リスト
        self.base_constraint_list = ["負荷時間以下制約","合計販売量一致制約","月末在庫0以上制約"]
        
        #よく使う制約条件
        self.common_constraint_list = self.base_constraint_list + ["確定生産量一致制約","確定販売量一致制約"]
        
        
        #どの月から適用できるか調整可能な制約条件リスト
        self.adjustable_constraint_list = ["負荷時間以下制約",
                                        "合計販売量一致制約",
                                        "月末在庫0以上制約",
                                        "基準在庫月数Min以上制約",
                                        "基準在庫月数Max以下制約",
                                        "最低連続生産時間以上制約"]
        
        
        #適用する工場を選択可能な制約条件リスト
        self.selectable_constraint_list = ["負荷時間以下制約",
                                           "月末在庫0以上制約",
                                           "基準在庫月数Min以上制約",
                                           "基準在庫月数Max以下制約",
                                           "最低生産回数以上制約",
                                           "最大生産回数以下制約",
                                            "最低連続生産時間以上制約",]
        
        
        
        self.all_obj_list = ["長時間ドープ切り替え回数最小化",
                             "SAZMA系品種連続生産月数最大化",
                             "基準在庫月数Min以上制約違反回数最小化",
                             "基準在庫月数Max以下制約違反回数最小化",
                             "優先SVA品種の合計生産量を最大化",
                             "サブ品種の合計生産量最小化",
                             "合計生産時間最大化",
                             "レア品種の合計生産回数最小化",
                             "超過月末在庫量最小化"]
                             #"合計生産時間最小化"]
        
        self.okini2_obj_list = ["長時間ドープ切り替え回数最小化",
                                "SAZMA系品種連続生産月数最大化",
                                "基準在庫月数Min以上制約違反回数最小化",
                                "基準在庫月数Max以下制約違反回数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "合計生産時間最大化",
                                "超過月末在庫量最小化"]
        
        
        
        #最適解なかった時に探し出す用(最低限)
        #self.temp_obj_list = ["負荷時間以下制約違反量最小化"]
        self.temp_obj_list = ["負荷時間以下制約違反量最小化","基準在庫月数Min超在庫量最小化（原因調査用）","基準在庫月数Max以下制約違反回数最小化","合計生産時間最大化"]
                              #"合計生産時間最大化"]
                             #"超過月末在庫量最小化"]
                             
                             
        #最適解なかった時に探し出す用その２（レア品種優先）
        self.temp2_obj_list = ["長時間ドープ切り替え回数最小化",
                               "SAZMA系品種連続生産月数最大化",
                               "基準在庫月数Min以上制約違反回数最小化",
                                "基準在庫月数Max以下制約違反回数最小化",
                                "負荷時間以下制約違反量最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "合計生産時間最大化",
                                "超過月末在庫量最小化",
                                "基準在庫月数Min超在庫量最小化（原因調査用）"
                               ]
        
        
        self.kensyo_obj_list = ["メインドープによる立上・立下回数最大化"]
        self.kensyo_obj_list2 = ["長時間ドープ切替工場合計切替時間最小化","保全月合計ドープ数最小化","メインドープによる立上・立下回数最大化","全工場合計切替時間最小化"]
        
        self.kensyo_obj_list3 = ["保全月合計ドープ数最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                 "メインドープによる立上・立下回数最大化",
                                "基準在庫月数Min以上制約違反回数最小化",
                                "基準在庫月数Max以下制約違反回数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "合計生産時間最大化",
                                "超過月末在庫量最小化"]
        
        self.kensyo_obj_list3 = ["メインドープによる立上・立下回数最大化",
                                 "保全月合計ドープ数最小化",
                                 "長時間ドープ切替工場合計切替時間最小化",
                                 "基準在庫月数Min以上制約違反回数最小化",
                                 "基準在庫月数Max以下制約違反回数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "合計生産回数最小化",
                                "合計生産時間最大化",]
                                #"超過月末在庫量最小化"]


        self.kensyo_obj_list4 = ["生産イベント月数最大化",
                                 "基準在庫月数Min以上制約違反回数最小化",
                                 "長時間ドープ切替工場合計切替時間最小化",
                                #"保全月合計ドープ数最小化",
                                #"負荷時間スラック変数合計最小化2",
                                #"余力時間最小化",
                                #"基準在庫月数Max以下制約違反回数最小化",
                                #"レア品種の合計生産回数最小化",
                                #"サブ品種の合計生産量最小化",
                                #"メインドープによる立上・立下回数最大化",
                                #"優先SVA品種の合計生産量を最大化",
                                #"合計生産回数最小化",
                                #"合計生産時間最大化",
                                 ]
        
        
        
        self.kensyo_obj_list4 = ["生産イベント月数最大化",
                                "余力時間最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                 #"基準在庫月数Min以上制約違反回数最小化",
                                #"保全月合計ドープ数最小化",
                                #"基準在庫月数Max以下制約違反回数最小化",
                                #"レア品種の合計生産回数最小化",
                                #"サブ品種の合計生産量最小化",
                                #"メインドープによる立上・立下回数最大化",
                                #"優先SVA品種の合計生産量を最大化",
                                #"合計生産回数最小化",
                                #"合計生産時間最大化",
                                 ]
        
        
        #一番良さげ
        self.kensyo_obj_list4 = ["余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "基準在庫月数Min以上制約違反回数最小化",
                                "基準在庫月数Max以下制約違反回数最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "メインドープによる立上・立下回数最大化",
                                "合計生産回数最小化"
                                 ]
        
        #基準在庫の順番変更
        self.kensyo_obj_list4 = ["余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "メインドープによる立上・立下回数最大化",
                                "合計生産回数最小化",
                                "基準在庫月数Min以上制約違反回数最小化",
                                "基準在庫月数Max以下制約違反回数最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                 ]
        
        #基準在庫の目的関数一本化
        self.kensyo_obj_list4 = ["余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "メインドープによる立上・立下回数最大化",
                                "基準在庫月数違反回数最小化",
                                "合計生産回数最小化"
                                 ]
        
        
        #長時間ドープ切替最小化
        self.kensyo_obj_list3 = ["余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "優先SVA品種の合計生産量を最大化",
                                "メインドープによる立上・立下回数最大化",
                                "基準在庫月数違反回数最小化",
                                "合計生産回数最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                 ]
        
        self.kensyo_obj_list3 = ["生産イベント月数最大化",
                                #"余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                "メインドープによる立上・立下回数最大化",
                                #"余力時間最小化2",
                                "基準在庫月数Min以上制約違反回数最小化",
                                "7桁在庫月数合計最小化",
                                "合計生産回数最小化",
                                "優先SVA品種の合計生産量を最大化",
                                 ]
        
        
        self.kensyo_obj_list5 = [#"余力時間最小化2",
                                "生産イベント月数最大化",
                                "年度末7桁基準在庫月数Min以上制約違反回数最小化",               
                                
                                #"合計生産時間最大化",
                                 #"7桁基準在庫月数Min以上制約違反回数最小化",
                                #"7桁基準在庫月数Max以下制約違反回数最小化",
                                #"基準在庫月数Min以上制約違反回数最小化",
                                #"基準在庫月数Max以下制約違反回数最小化",
                                "メイン品種生産量最大化",
                                
                                #"7桁基準在庫月数Min以上制約違反回数最小化",
                                # "7桁基準在庫月数Max以下制約違反回数最小化"
                                 ]
        
        
        
        
        
        
        
        #長時間ドープ切替最小化
        self.kensyo_obj_list2 = ["余力時間最小化",
                                "保全月合計ドープ数最小化",
                                "レア品種の合計生産回数最小化",
                                "サブ品種の合計生産量最小化",
                                "長時間ドープ切替工場合計切替時間最小化",
                                "メインドープによる立上・立下回数最大化",
                                "基準在庫月数違反回数最小化",
                                "合計生産回数最小化",
                                "優先SVA品種の合計生産量を最大化",
                                 ]
        
        
        
        
    def convert_file_to_df(self,file_switch,file):
        """
        ファイルオブジェクトを引数にし、
        各シートをデータフレームにし辞書にして返す
        
        
        """
        df_dict = {}
        
        for sheet_name in self.sheet_list:
            
            # if sheet_name == "生産能力（新）":
            #     df_dict[sheet_name] = pd.read_excel(file,sheet_name=sheet_name,index_col="工場")
            
            if sheet_name == "合計販売量":
                df_dict[sheet_name] = pd.read_excel(file,sheet_name=sheet_name,index_col="品種名")
            
            elif sheet_name == "幅":
                df_dict[sheet_name] = pd.read_excel(file,sheet_name=sheet_name,index_col="品種名")
            
            elif sheet_name == "生産量達成率":
                df_dict[sheet_name] = pd.read_excel(file,sheet_name=sheet_name,index_col="工場")
                
            else:
                df_dict[sheet_name] = pd.read_excel(file,sheet_name=sheet_name)
        
        for sheet_name in self.switch_sheet_list:
            df_dict[sheet_name] = pd.read_excel(file_switch,sheet_name=sheet_name)
        
        return df_dict
    
    
    
    
    # def get_jissui_month_list(self,jissui_name):
    #     """
    #     実行推定の月リストを求める。
        
    #     0実12推、基本予算は厳密には別物らしいので、
    #     一応分けた。内部的な計算はかわらない。
        
    #     """
        
    #     #基本予算の場合は4月～3月すべてを返す。
    #     if jissui_name == "基本予算":
    #         return self.all_month_list
        
    #     ind = jissui_name.find("実")
        
    #     jisseki_num = int(jissui_name[:ind])
        
    #     jissui_month_list = self.all_month_list[jisseki_num:]
        
    #     return jissui_month_list
    
    
    def get_fuka_dict(self,df):
        """
        負荷時間データの辞書形式での取り出し
        
        4月~3月までの辞書になってしまうが、OKとする。(実際にシミュレーションする際に実推月に合わせる)
        
        {'L1': {'4月': 0.0,
            '5月': 0.0,
            '6月': 0.0,
            '7月': 0.0,
            '8月': 0.0,
            '9月': 0.0,
            '10月': 672.0,
            '11月': 384.0,
            '12月': 332.5,
            '1月': 724.0,
            '2月': 382.0,
            '3月': 0.0},
        
        """
        df_fuka = df[df["工程時間内訳"] == "負荷時間"]
        df_fuka = df_fuka.drop("工程時間内訳", axis=1)
        fuka_dict = df_fuka.T.to_dict()
        return fuka_dict
    
    
    def get_prod_capacity_dict(self,df):
        """
        生産能力シートの辞書形式での取り出し
        """
        nested_dict = {}
        for _, row in df.iterrows():
            factory = row['工場']
            metric = row['工程時間内訳']
            if factory not in nested_dict:
                nested_dict[factory] = {}
            for month in df.columns[2:]:
                if month not in nested_dict[factory]:
                    nested_dict[factory][month] = {}
                nested_dict[factory][month][metric] = row[month]
        
        
        # for factory, months in nested_dict.items():
        #     for month, metrics in months.items():
        #         # "保全/工事"が存在するか確認してフラグを設定
        #         if "保全/工事" in metrics:
        #             metrics["保全フラグ"] = 1 if metrics["保全/工事"] != 0 else 0
        
        return nested_dict
            
    
    def get_ave_switch_dict(self,df):
        """
        平均切り替え時間
        
        """
        ave_switch_dict = df.T.to_dict()
        return ave_switch_dict
    
    def get_sales_dict(self,df):
        """
        各月合計販売量
        """
        
        sales_prod_order = list(df.index)
        sales_dict = df.to_dict()
        
        #st.write(sales_dict)
        
        
        return sales_dict,sales_prod_order
        
        
    def get_width_dict(self,df):
        """
        幅
        """
        width_dict = {}
        for name in df.index:
            width_dict[name] = df["幅"][name]
        
        return width_dict
        
    
    def get_cs_prod_order(self,df):
        df = df.dropna()
        cs_prod_order = list(df["品種"])        #結果ファイル書き出し時に必要。
        
        #st.write(cs_prod_order)
        #st.write({value: rank for rank, value in enumerate(cs_prod_order)} )
        
        #タプルをキーとする辞書
        cs_prod_order = { (row['品種'], row['工場']): idx for idx, row in df.iterrows() }
        
        return cs_prod_order
        
    
    def get_cs_dict(self,df):
        """
        cs
        
        {"6UAW":{
            "L3":{
                "4月":62,
                "5月":62,
                "6月":62,
        
        """
        df = df.dropna()



        month_list = list(df.columns)
        month_list.remove("品種")
        month_list.remove("工場")


        prod_list = set(df["品種"])
        plant_list = set(df["工場"])



        cs_dict = {}
        for name in prod_list:
            df_prod = df[df["品種"] == name]
            plant_list = set(df_prod["工場"])
            
            plant_dict = {}
            for plant in plant_list:
                month_dict = {}
                for month in month_list:
                    month_dict[month] = df_prod[df_prod["工場"] == plant][month].values[0]
                
                plant_dict[plant] = month_dict
            
            cs_dict[name] = plant_dict
        
        return cs_dict
    
    
    def get_finalized_sales_dict(self,df):
        """
        確定販売量
        
        """
        df = df.dropna(subset=["品種"])
        
        #st.write(df)

        all_month_list = list(df.columns)
        all_month_list.remove("品種")
        all_month_list.remove("工場")

        #df_2 = df.dropna(axis=1,how="all")

        df_removed = df.dropna(subset=all_month_list,how="all")
        df_removed = df_removed.dropna(how="all",axis=1)

        if df_removed.empty is True:
            finalized_sales_dict = None
            return finalized_sales_dict

        finalized_sales_dict = {}

        prod_list = set(df_removed["品種"])
        for name in prod_list:

            df_prod = df_removed[df_removed["品種"]==name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                df_plant = df_prod[df_prod["工場"]==plant]
                df_plant = df_plant.dropna(how="all",axis=1)
                month_list = list(df_plant.columns)
                month_list.remove("品種")
                month_list.remove("工場")
                month_dict = {}
                for month in month_list:
                    month_dict[month] = df_plant[month].values[0]
                
                plant_dict[plant] = month_dict
            
            finalized_sales_dict[name] = plant_dict


        return finalized_sales_dict
    
    def get_finalized_prod_dict(self,df):
        """
        確定済み生産量
        
        """
        df = df.dropna(subset=["品種"])

        #これ実推の月にすればよくね
        all_month_list = list(df.columns)
        all_month_list.remove("品種")
        all_month_list.remove("工場")

        #df_2 = df.dropna(axis=1,how="all")

        df_removed = df.dropna(subset=all_month_list,how="all")
        df_removed = df_removed.dropna(how="all",axis=1)


        
        if df_removed.empty is True:
            finalized_prod_dict = None
            return finalized_prod_dict

        finalized_prod_dict = {}

        prod_list = set(df_removed["品種"])
        for name in prod_list:

            df_prod = df_removed[df_removed["品種"]==name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                df_plant = df_prod[df_prod["工場"]==plant]
                df_plant = df_plant.dropna(how="all",axis=1)
                month_list = list(df_plant.columns)
                month_list.remove("品種")
                month_list.remove("工場")
                month_dict = {}
                for month in month_list:
                    month_dict[month] = df_plant[month].values[0]
                
                plant_dict[plant] = month_dict
            
            finalized_prod_dict[name] = plant_dict
        
        return finalized_prod_dict
    
    def get_init_stock_dict(self,df):
        """
        期首在庫
        
        """
        df = df.dropna()
        prod_list = set(df["品種"])
        init_stock_dict = {}
        for name in prod_list:
            df_prod = df[df["品種"] == name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                df_prod = df[df["品種"] == name]
                plant_dict[plant] = df_prod[df_prod["工場"]==plant]["期首在庫"].values[0]
            
            init_stock_dict[name] = plant_dict
        
        return init_stock_dict
            
    
    def get_min_continuous_dict(self,df):
        """
        最低連続生産時間
        """
        df = df.dropna()
        min_continuous_dict = {}
        prod_list = set(df["品種"])
        for name in prod_list:
            df_prod = df[df["品種"] == name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                df_prod = df[df["品種"] == name]
                plant_dict[plant] = df_prod[df_prod["工場"]==plant]["最低連続生産時間"].values[0]
            
            min_continuous_dict[name] = plant_dict
        
        return min_continuous_dict
    
    
    def get_prod_num_times_dict(self,df):
        """
        生産回数
        
        """
        df = df.dropna()




        prod_num_times_dict = {}
        prod_list = set(df["品種"])
        for name in prod_list:
            df_prod = df[df["品種"] == name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                min_max_dict = {}
                df_plant = df[df["工場"] == plant]
                df_prod = df[df["品種"] == name]
                
                min_max_dict["min"] = int(df_prod[df_prod["工場"]==plant]["最低生産回数"].values[0])
                min_max_dict["max"] = int(df_prod[df_prod["工場"]==plant]["最大生産回数"].values[0])
            
                plant_dict[plant] = min_max_dict
            
            prod_num_times_dict[name] = plant_dict
        
        return prod_num_times_dict
    
    
    def get_basic_stock_dict(self,df):
        """
        基準在庫月数
        
        """
        df = df.dropna()


        basic_stock_dict = {}
        prod_list = set(df["品種"])
        for name in prod_list:
            df_prod = df[df["品種"] == name]
            plant_list = set(df_prod["工場"])
            plant_dict = {}
            for plant in plant_list:
                min_max_dict = {}
                df_plant = df[df["工場"] == plant]
                df_prod = df[df["品種"] == name]
                
                min_max_dict["min"] = int(df_prod[df_prod["工場"]==plant]["基準在庫月数Min"].values[0])
                min_max_dict["max"] = int(df_prod[df_prod["工場"]==plant]["基準在庫月数Max"].values[0])
                
                plant_dict[plant] = min_max_dict
            
            basic_stock_dict[name] = plant_dict
        
        
        
        
        return basic_stock_dict
    
    def get_achieve_rate_dict(self,df):
        """
        生産量達成率（田村シートは100分率ではなかった。）
        もともと事前想定のモデルは100分率で来ることを想定していたため、ここで100倍する。
        この辺どうするかは別途考える
        """
        df = df*100
        achieve_rate_dict = df.to_dict()
        
        return achieve_rate_dict
    
    def get_special_prod_list(self,df):
        row_tuples_list = list(df.itertuples(index=False, name=None))
        
        return row_tuples_list
    
    def get_switch_coeff_dict_old(self,df):
        # Convert the DataFrame into the dictionary format
        switch_coeff_dict = {
            row['工場']: {
                '生産品種数係数': row['生産品種数係数'],
                '切片': row['切片']
            } for _, row in df.iterrows()
        }
        
        return switch_coeff_dict


    def get_switch_coeff_dict(self,df_switch_dict):
        """
        月中切替時間係数
        
        #将来を見据え、月毎にデータ持つことに。
        直近はL6だけ特別扱いするかも。
        
        """
        switch_coeff_dict = {}
        
        for plant in self.plant_list:
            if plant != "L6":
                switch_coeff_dict[plant] = {}
                coeff = LinearRegressionner(df_switch_dict[plant]).main()
                for month in self.all_month_list:            
                    switch_coeff_dict[plant][month] = coeff
            
            if plant == "L6":
                switch_coeff_dict[plant] = {}
                for month in self.kamiki_month_list:
                    switch_coeff_dict[plant][month] = LinearRegressionner(df_switch_dict[plant]["上期"]).main()
                for month in self.shimoki_month_list:
                    switch_coeff_dict[plant][month] = LinearRegressionner(df_switch_dict[plant]["下期"]).main()
                    
        return switch_coeff_dict
    
    def get_inter_switch_coeff_dict(self,df_inter_switch_dict):
        inter_switch_coeff_dict = {}
        
        for plant in self.plant_list:
            if plant != "L6":
                inter_switch_coeff_dict[plant] = {}
                coeff = LinearRegressionner(df_inter_switch_dict[plant]).main_inter()
                for month in self.all_month_list:
                    inter_switch_coeff_dict[plant][month] = coeff
            
            if plant == "L6":
                inter_switch_coeff_dict[plant] = {}
                for month in self.kamiki_month_list:
                    inter_switch_coeff_dict[plant][month] = LinearRegressionner(df_inter_switch_dict[plant]["上期"]).main_inter()
                for month in self.shimoki_month_list:
                    inter_switch_coeff_dict[plant][month] = LinearRegressionner(df_inter_switch_dict[plant]["下期"]).main_inter()
        
        return inter_switch_coeff_dict
    
    
    
    
    
    
    
    def get_maint_plan_dict(self,df):
        df = df.dropna()
        df_dict = df.to_dict(orient='records')
        nested_dict = {}
        for record in df_dict:
            factory = record['工場']
            maintenance = record['保全名']
            if factory not in nested_dict:
                nested_dict[factory] = {}
            if maintenance not in nested_dict[factory]:
                nested_dict[factory][maintenance] = {}
            for month in record:
                if month not in ['工場', '保全名']:
                    nested_dict[factory][maintenance][month] = record[month]
        for factory in nested_dict:
            for maintenance in nested_dict[factory]:
                nested_dict[factory][maintenance] = {month: value for month, value in 
                                                    nested_dict[factory][maintenance].items() if value != 0}
        return nested_dict
    
    
    def get_categorized_maint_plan_dict(self,df,bundle_maint_options_dict):
        """
        保全計画の辞書を、head,middle,tailに分ける
        
        この時点で、抱き合わせる保全は削除する。
        
        
        "L1":{
                "保全①":{
                "保全前期":{
                "11月":264
                }
                "保全中期":NULL
                "保全後期":{
                "12月":216
                }
                }
                "保全②":{
                "保全前期":{
                "2月":120
                }
                "保全中期":NULL
                "保全後期":{
                "2月":120
                }
                }
                }
        
        """
        nested_dict = self.get_maint_plan_dict(df)
        
        categorized_maint_plan_master_dict= {}
        for factory in nested_dict:
            categorized_maint_plan_master_dict[factory] = {}
            for maintenance in nested_dict[factory]:
                
                months = list(nested_dict[factory][maintenance].keys())
                values = list(nested_dict[factory][maintenance].values())
                length = len(months)
                
                if length == 1:
                    head = {months[0]: values[0] / 2}
                    tail = {months[0]: values[0] / 2}
                    middle = None
                elif length == 2:
                    head = {months[0]: values[0]}
                    tail = {months[1]: values[1]}
                    middle = None
                else:
                    head = {months[0]: values[0]}
                    middle = {months[length // 2]: values[length // 2]}
                    tail = {months[-1]: values[-1]}
                
                categorized_maint_plan_master_dict[factory][maintenance] = {'保全前期': head, '保全中期': middle, '保全後期': tail}
        
        ####抱き合わせする保全を削除####
        categorized_maint_plan_dict = copy.deepcopy(categorized_maint_plan_master_dict)
        
        categorized_maint_plan_deleted_dict = {}
        for factory in nested_dict:
            for maintenance in nested_dict[factory]:
                if bundle_maint_options_dict[factory][maintenance]["抱き合わせ希望"] == True:
                    del categorized_maint_plan_dict[factory][maintenance]
                    categorized_maint_plan_deleted_dict
        
        
            
        return categorized_maint_plan_master_dict, categorized_maint_plan_dict
    
    def get_month_type_dict(self,categorized_maint_plan_dict):
        
        new_data = {}
        # Iterate over each factory in the original data
        for factory, maintenance_types in categorized_maint_plan_dict.items():
            factory_dict = {}
            month_status = {month: "保全前期なし保全後期なし" for month in self.all_month_list}
            
            # Check each type of maintenance and update the month_status dictionary
            for maintenance, phases in maintenance_types.items():
                for phase, phase_data in phases.items():
                    if phase_data is not None:
                        for month, value in phase_data.items():
                            if phase == "保全前期":
                                if "保全前期あり" not in month_status[month]:
                                    month_status[month] = month_status[month].replace("保全前期なし", "保全前期あり")
                            elif phase == "保全後期":
                                if "保全後期あり" not in month_status[month]:
                                    month_status[month] = month_status[month].replace("保全後期なし", "保全後期あり")
            
            # Append the result to the factory dictionary
            factory_dict.update(month_status)
            new_data[factory] = factory_dict
        
        return new_data
    
    
    def get_month_type_dict2(self,categorized_maint_plan_dict):
        """
        月タイプの辞書。切替時間の近似モデルの使い分けのために必要。
        
        "L1":{
            "4月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "5月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "6月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "7月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "8月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "9月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "10月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "11月":{
            "保全前期":"あり"
            "保全後期":"なし"
            }
            "12月":{
            "保全前期":"なし"
            "保全後期":"あり"
            }
            "1月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            "2月":{
            "保全前期":"あり"
            "保全後期":"あり"
            }
            "3月":{
            "保全前期":"なし"
            "保全後期":"なし"
            }
            }

        """
        result = {}
        
        #st.write(categorized_maint_plan_dict)
        
        
        
        for plant, section_data in categorized_maint_plan_dict.items():
            
            result[plant] = {}

            for month in self.all_month_list:
                # デフォルトで "なし" を設定
                result[plant][month] = {
                    "保全前期": "なし",
                    "保全後期": "なし"
                }

            #st.write(result[plant])


            #L6のところでエラーになっている模様（categorized_dictの中身の確認必要）
            # 各保全の項目からデータを挿入
            for maintenance_type, periods in section_data.items():
                
                for period, period_data in periods.items():
                    if period_data:
                        #st.write(period_data)
                        for month, value in period_data.items():
                            
                            # 該当月の前期・後期を"あり"に更新
                            result[plant][month][period] = "あり"

        return result
        
        
        
        
        
    
    def get_maint_hour_dict(self,df,bundle_maint_options_dict):
        """
        各工場各月に保全時間が何時間あるか。
        
                
        "L1":{
            "4月":0
            "5月":0
            "6月":0
            "7月":0
            "8月":0
            "9月":0
            "10月":0
            "11月":264
            "12月":216
            "1月":0
            "2月":240
            "3月":0
            }

        """
        
        nested_dict = self.get_maint_plan_dict(df)
        
        
        df = df.dropna(subset=['保全名'])

        # Remove '保全名' column as it is not needed
        #df = df.drop(columns=['保全名',"抱き合わせ希望","抱き合わせ可能"])
        df = df.drop(columns=['保全名'])
        # Create a dictionary {工場: {月: 時間}}
        result_dict = {}
        months = df.columns[1:]  # Excluding '工場'

        for index, row in df.iterrows():
            factory = row['工場']
            if factory not in result_dict:
                result_dict[factory] = {}
            for month in months:
                if month not in result_dict[factory]:
                    result_dict[factory][month] = 0
                result_dict[factory][month] += row[month]
        
        
        
        return result_dict
    
    
    
    def get_maint_hour_dict_2(self, df, bundle_maint_options_dict):
        """
        各工場各月に保全時間が何時間あるかを計算する。
        ただし、抱き合わせ希望がTrueの場合、該当する月の時間は0にする。

        Parameters:
            df (pd.DataFrame): 入力データフレーム。
            bundle_maint_options_dict (dict): 保全の抱き合わせオプション。

        Returns:
            dict: 工場ごとの月ごとの保全時間の辞書。
        """
        # Remove rows with NaN '保全名'
        df = df.dropna(subset=['保全名'])

        # Initialize result dictionary
        result_dict = {}

        # Identify the month columns
        months = df.columns[2:]

        for _, row in df.iterrows():
            factory = row['工場']
            maint_name = row['保全名']

            # Initialize the factory in the result dictionary if not present
            if factory not in result_dict:
                result_dict[factory] = {month: 0 for month in months}

            # Check if '抱き合わせ希望' is True
            is_bundling_requested = (
                factory in bundle_maint_options_dict and
                maint_name in bundle_maint_options_dict[factory] and
                bundle_maint_options_dict[factory][maint_name]['抱き合わせ希望']
            )

            if not is_bundling_requested:
                # Add times for each month if not bundling requested
                for month in months:
                    result_dict[factory][month] += row[month]

        return result_dict
    
    
    def get_maint_month_list(self,maint_hour_dict):
        """
        保全時間が0でない月のリストを取得する
        
        {
            "L1":[
            0:"11月"
            1:"12月"
            2:"2月"
            ]
            "L2":[
            0:"11月"
            1:"12月"
            ]
        
        
        """
        non_zero_months = {}
        for factory, months in maint_hour_dict.items():
            non_zero_months[factory] = [month for month, hours in months.items() if hours != 0]
        
        
        
        return non_zero_months
        
    
    
    def get_main_dope_prod_dict(self,df):
        nested_dict = {
        row['工場']: {'メインドープ': row['メインドープ'], 'メイン品種': row['メイン品種']}
        for _, row in df.iterrows()}
        
        return nested_dict
        
    
    def get_switch_coeff_dict_temp(self,df_dict):
        """
        切替時間に関しては係数のみ得られれば良く、どうなるかわからないので一旦関数化し退避
        
        """
        
        df_switch_dict = {"L1":df_dict["L1月中切替"],"L2":df_dict["L2月中切替"],"L3":df_dict["L3月中切替"],
                          "L4":df_dict["L4月中切替"],"L5":df_dict["L5月中切替"],
                          "L6":{"上期":df_dict["【上期】L6月中切替"],
                                "下期":df_dict["【下期】L6月中切替"]},
                          "L7":df_dict["L7月中切替"]}
        
        
        df_inter_switch_dict = {"L1":df_dict["L1月間切替（生産品種のみ）"],"L2":df_dict["L2月間切替（生産品種のみ）"],"L3":df_dict["L3月間切替（生産品種のみ）"],
                                "L4":df_dict["L4月間切替（生産品種のみ）"],"L5":df_dict["L5月間切替（生産品種のみ）"],
                                "L6":{"上期":df_dict["【上期】L6月間切替（生産品種のみ）"],
                                      "下期":df_dict["【下期】L6月間切替（生産品種のみ）"]},
                                "L7":df_dict["L7月間切替（生産品種のみ）"]}
        
        df_inter_switch_maint_head_dict = {"L1":df_dict["L1月間切替（保全前期）"],"L2":df_dict["L2月間切替（保全前期）"],"L3":df_dict["L3月間切替（保全前期）"],
                                           "L4":df_dict["L4月間切替（保全前期）"],"L5":df_dict["L5月間切替（保全前期）"],
                                           "L6":{"上期":df_dict["【上期】L6月間切替（保全前期）"],
                                                 "下期":df_dict["【下期】L6月間切替（保全前期）"]},
                                           "L7":df_dict["L7月間切替（保全前期）"]}
        
        
        df_inter_switch_maint_tail_dict = {"L1":df_dict["L1月間切替（保全後期）"],"L2":df_dict["L2月間切替（保全後期）"],"L3":df_dict["L3月間切替（保全後期）"],
                                           "L4":df_dict["L4月間切替（保全後期）"],"L5":df_dict["L5月間切替（保全後期）"],
                                           "L6":{"上期":df_dict["【上期】L6月間切替（保全後期）"],
                                                 "下期":df_dict["【下期】L6月間切替（保全後期）"]},
                                           "L7":df_dict["L7月間切替（保全後期）"]}
        
        
        
        switch_coeff_dict = self.get_switch_coeff_dict(df_switch_dict)
        inter_switch_coeff_dict = self.get_inter_switch_coeff_dict(df_inter_switch_dict)
        inter_switch_maint_head_coeff_dict = self.get_inter_switch_coeff_dict(df_inter_switch_maint_head_dict)
        inter_switch_maint_tail_coeff_dict = self.get_inter_switch_coeff_dict(df_inter_switch_maint_tail_dict)
        
        #st.write("L1の月中切替")
        #st.write(switch_coeff_dict["L1"]["4月"])
        #st.write(inter_switch_coeff_dict)
        
        
        return switch_coeff_dict,inter_switch_coeff_dict,inter_switch_maint_head_coeff_dict,inter_switch_maint_tail_coeff_dict
    
    
    
    
    def get_bundle_maint_options_dict(self,df):
        """
        全工場全ての保全について、抱き合わせ希望と抱き合わせ可能の情報を持つ辞書を作成する。
        
        {
            "L1":{
            "保全①":{
            "抱き合わせ希望":false
            "抱き合わせ可能":false
            }
            "保全②":{
            "抱き合わせ希望":false
            "抱き合わせ可能":false
            }
            }
        
        """
        
        # Drop rows with NaN values in critical columns
        cleaned_data = df.dropna(subset=['工場', '保全名', '抱き合わせ希望', '抱き合わせ可能'])
        
        # Initialize the nested dictionary
        bundle_maint_options_dict = {}
        
        # Populate the dictionary
        for _, row in cleaned_data.iterrows():
            factory = row['工場']
            maintenance = row['保全名']
            desired = bool(row['抱き合わせ希望'])
            possible = bool(row['抱き合わせ可能'])
            
            if factory not in bundle_maint_options_dict:
                bundle_maint_options_dict[factory] = {}
            
            bundle_maint_options_dict[factory][maintenance] = {
                '抱き合わせ希望': desired,
                '抱き合わせ可能': possible
            }
        
        return bundle_maint_options_dict
    
    
    
    def get_bundled_maint_dict_old(self, df, bundle_maint_options_dict):
        """
        Creates a nested dictionary with factory, maintenance name, month, and time
        for maintenance tasks where '抱き合わせ希望' is True and time is greater than 0.

        Parameters:
            df (pd.DataFrame): The input DataFrame containing the data.
            bundle_maint_options_dict (dict): Dictionary with bundle maintenance options.

        Returns:
            dict: A nested dictionary with the desired structure.
        """
        # Initialize an empty dictionary to store the result
        nested_dict = {}

        #st.write(df)

        # Iterate over each row in the dataframe
        for _, row in df.iterrows():
            factory = row['工場']
            maint_name = row['保全名']
            
            # # Skip rows where the maintenance name is NaN
            # if pd.isna(maint_name) or factory not in bundle_maint_options_dict:
            #     continue
            
            # Check if the maintenance is in the dictionary and "抱き合わせ希望" is True
            if maint_name in bundle_maint_options_dict[factory] and bundle_maint_options_dict[factory][maint_name]['抱き合わせ希望']:
                # Create a nested dictionary structure for the factory and maintenance name
                if factory not in nested_dict:
                    nested_dict[factory] = {}
                if maint_name not in nested_dict[factory]:
                    nested_dict[factory][maint_name] = {}
                
                # Iterate over the months and add the time to the dictionary if it's greater than 0
                for month in df.columns[2:]:  # Start from the 3rd column (skip factory and maintenance name)
                    time = row[month]
                    if time > 0:
                        nested_dict[factory][maint_name][month] = time

        return nested_dict
    
    def get_bundled_maint_dict(self, df, bundle_maint_options_dict):
        """
        Creates two nested dictionaries:
        - One for maintenance tasks where '抱き合わせ希望' is True.
        - Another for tasks where '抱き合わせ希望' is False.

        Parameters:
            df (pd.DataFrame): The input DataFrame containing the data.
            bundle_maint_options_dict (dict): Dictionary with bundle maintenance options.

        Returns:
            tuple: Two nested dictionaries (True_dict, False_dict).
        """
        # Initialize two empty dictionaries to store the results
        true_dict = {}
        false_dict = {}

        # Iterate over each row in the dataframe
        for _, row in df.iterrows():
            factory = row['工場']
            maint_name = row['保全名']
            
            # Check if the factory and maintenance name exist in the options dictionary
            if factory in bundle_maint_options_dict and maint_name in bundle_maint_options_dict[factory]:
                # Determine the current "抱き合わせ希望" flag
                is_bundle_true = bundle_maint_options_dict[factory][maint_name]['抱き合わせ希望']
                
                # Select the appropriate dictionary based on the flag
                target_dict = true_dict if is_bundle_true else false_dict

                # Create a nested dictionary structure for the factory and maintenance name
                if factory not in target_dict:
                    target_dict[factory] = {}
                if maint_name not in target_dict[factory]:
                    target_dict[factory][maint_name] = {}

                # Iterate over the months and add the time to the dictionary if it's greater than 0
                for month in df.columns[2:]:  # Start from the 3rd column (skip factory and maintenance name)
                    time = row[month]
                    if time > 0:
                        target_dict[factory][maint_name][month] = time

        return true_dict, false_dict
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    def get_maintplan_dict(self,df_dict):
        
        bundle_maint_options_dict = self.get_bundle_maint_options_dict(df_dict["抱き合わせ保全（新）"])  #抱き合わせ設定
        #st.write(bundle_maint_options_dict)
        
        #保全計画の辞書を、head,middle,tailに分ける
        categorized_maint_plan_master_dict,categorized_maint_plan_dict = self.get_categorized_maint_plan_dict(df_dict["保全計画（新）"],
                                                                                                              bundle_maint_options_dict)
        
        #st.write(categorized_maint_plan_master_dict)
        #st.write(categorized_maint_plan_dict)
        
        
        
        bundled_maint_dict,not_bundled_maint_dict = self.get_bundled_maint_dict(df_dict["保全計画（新）"], 
                                                         bundle_maint_options_dict)   #抱き合わせ保全の辞書
        #st.write(bundled_maint_dict)
        #st.write(not_bundled_maint_dict)
        
        
        
        #保全時間が0でない月のリストを取得する
        maint_hour_dict = self.get_maint_hour_dict_2(df_dict["保全計画（新）"],bundle_maint_options_dict)
        #st.write("maintだよ")
        #st.write(maint_hour_dict)
        
        #各工場各月に保全時間が何時間あるか。
        maint_month_list= self.get_maint_month_list(maint_hour_dict)
        #st.write(maint_month_list)
        
        
        #月タイプの辞書。切替時間の近似モデルの使い分けのために必要。
        month_type_dict = self.get_month_type_dict2(categorized_maint_plan_dict)
        #st.write(month_type_dict)
        
        return bundle_maint_options_dict, bundled_maint_dict,not_bundled_maint_dict,\
            categorized_maint_plan_dict,maint_hour_dict,maint_month_list,month_type_dict
    
    
    def get_dope_group_dict(self,df):
        """
        ドープグループ
        
        """
        nested_dict_with_none = {}

        for _, row in df.iterrows():
            factory = row['工場']
            group_dict = {}
            
            # Assign グループ1
            group_dict['group1'] = row['group1'] if pd.notna(row['group1']) else None
            # Assign グループ2, set None if not present
            group_dict['group2'] = row['group2'] if pd.notna(row['group2']) else None

            nested_dict_with_none[factory] = group_dict

        return nested_dict_with_none
        
        
    def get_dope_group_linking(self,df):
        nested_dict = {}

        for _, row in df.iterrows():
            factory = row['工場']
            group_dict = {}
            
            for group_name in ['group1', 'group2']:
                if pd.notna(row[group_name]):
                    group_dict[group_name] = row[group_name].split(',')  # Split 品種 by commas
                # else:
                #     group_dict[group_name] = None

            nested_dict[factory] = group_dict

        return nested_dict
        
        
    
    
    def get_dope_prod_dict(self,df):
        """
        品種とドープの対応辞書を作成
        
        """
        # 入れ子の辞書を作成する
        nested_dict = {}

        # データを行ごとに処理
        for _, row in df.iterrows():
            品種 = row['品種名']
            ドープ = row['ドープ名']
            
            # 各工場列を確認
            for plant in self.plant_list:
                if row[plant] == 1:  # 1の場合のみ辞書に追加
                    if plant not in nested_dict:
                        nested_dict[plant] = {}
                    if ドープ not in nested_dict[plant]:
                        nested_dict[plant][ドープ] = []
                    nested_dict[plant][ドープ].append(品種)
        
        return nested_dict
    
    def get_dopenum_dope_dict(self,df):
        nested_dict = {}
        for _, row in df.iterrows():
            factory = row['工場']
            nested_dict[factory] = {}
            for dope_col in ['dope1', 'dope2', 'dope3']:
                dope_val = row[dope_col]
                if pd.notna(dope_val):
                    nested_dict[factory][dope_col] = dope_val

        return nested_dict
    
    
    
    def get_groupnum_dopenum_dict(self, plants_groups, plants_dopes):
        result = {}
        
        for plant, groups in plants_groups.items():
            # 結果用の辞書に工場名をキーとして作成
            if plant not in result:
                result[plant] = {}
            
            for group, values in groups.items():
                # 各グループのデータを処理
                if group not in result[plant]:
                    result[plant][group] = []
                
                for value in values:
                    # plants_dopesで同じvalueが見つかったらドープ名を検索
                    for dope_key, dope_value in plants_dopes.get(plant, {}).items():
                        if dope_value == value:
                            result[plant][group].append(dope_key)
        
        return result
        
    
    
    
    
    
    
    
    def get_params_dict(self,file_obj_switch,file_obj):
        """
        ファイルオブジェクトを引数に
        パラメータそれぞれ辞書型にして作成。
        エクセルファイルから辞書作成
        
        その他シート削除
        
        """
        params_dict = {}
        df_dict = self.convert_file_to_df(file_obj_switch,file_obj)
        #params_dict["fuka_dict"] = self.get_fuka_dict(df_dict["生産能力（新）"])
        params_dict["sales_dict"], params_dict["sales_prod_order"]= self.get_sales_dict(df_dict["合計販売量"])
        params_dict["width_dict"] = self.get_width_dict(df_dict["幅"])
        params_dict["cs_dict"] = self.get_cs_dict(df_dict["cs"])
        params_dict["cs_prod_order"] = self.get_cs_prod_order(df_dict["cs"]) 
        params_dict["finalized_sales_dict"] = self.get_finalized_sales_dict(df_dict["確定販売量"])
        params_dict["finalized_prod_dict"] = self.get_finalized_prod_dict(df_dict["確定生産量"])
        params_dict["init_stock_dict"] = self.get_init_stock_dict(df_dict["期首在庫"])
        params_dict["prod_num_times_dict"] = self.get_prod_num_times_dict(df_dict["生産回数"])
        params_dict["min_continuous_dict"] = self.get_cs_dict(df_dict["最低連続生産時間"])         #CSのファイルと同様の形式になったため
        params_dict["basic_stock_min_dict"] = self.get_cs_dict(df_dict["基準在庫月数Min"])
        params_dict["basic_stock_max_dict"] = self.get_cs_dict(df_dict["基準在庫月数Max"])
        params_dict["achieve_rate_dict"] = self.get_achieve_rate_dict(df_dict["生産量達成率（新）"])
        params_dict["std_fc_dict"] = self.get_cs_dict(df_dict["標準FC単価"])
        params_dict["std_vc_dict"] = self.get_cs_dict(df_dict["標準VC単価"])
        params_dict["params_file_name"] = file_obj.name
        
        params_dict["rare_prod_list"] = self.get_special_prod_list(df_dict["レア品種"])
        params_dict["sub_prod_list"] = self.get_special_prod_list(df_dict["サブ品種"])
        params_dict["priority_sva_prod_list"] = self.get_special_prod_list(df_dict["優先SVA品種"])
        
        
        
        params_dict["main_dope_prod_dict"] = self.get_main_dope_prod_dict(df_dict["メインドープ・メイン品種（新）"])
        
        
        #st.write(params_dict["main_dope_prod_dict"])
        
        
        params_dict["prod_capacity_dict"] = self.get_prod_capacity_dict(df_dict["生産能力（新）"])
        
        
        
        params_dict["achieve_rate_dict"] = self.get_cs_dict(df_dict["生産量達成率（新）"])
        #st.write(params_dict["achieve_rate_dict"])        
        
        
        
        params_dict["dope_group_dict"] = self.get_dope_group_dict(df_dict["ドープグループ"])    #ドープグループ
        params_dict["dope_prod_dict"] = self.get_dope_prod_dict(df_dict["工場品種対応表"])    #品種とドープの対応辞書
        params_dict["dope_group_linking_dict"] = self.get_dope_group_linking(df_dict["ドープグループ"])    #ドープグループ
        params_dict["dopenum_dope_dict"] = self.get_dopenum_dope_dict(df_dict["工場ドープ対応表"])    #ドープグループ
        
        #st.write(params_dict["dopenum_dope_dict"])
        
        # st.write("dope_group_linking_dict")
        # st.write(params_dict["dope_group_linking_dict"])
        
        # st.write("dope_group_dict")
        # st.write(params_dict["dope_group_dict"])
        
        #st.write("dope_prod_dict")
        #st.write(params_dict["dope_prod_dict"])
        
        #st.write(params_dict["dopenum_dope_dict"])
        
        
        params_dict["groupnum_dopenum_dict"] = self.get_groupnum_dopenum_dict(params_dict["dope_group_linking_dict"],
                                                                              params_dict["dopenum_dope_dict"])
        
        # st.write("aaa")
        # st.write(params_dict["groupnum_dopenum_dict"])
        
        
        # import pprint
        # pprint.pprint(params_dict["dope_group_linking_dict"])
        
        # pprint.pprint(params_dict["dopenum_dope_dict"])
        
        
        
        ###保全計画関係
        params_dict["bundle_maint_options_dict"], params_dict["bundle_maint_dict"],params_dict["not_bundle_maint_dict"],\
        params_dict["categorized_maint_plan_dict"],params_dict["maint_hour_dict"],\
        params_dict["maint_month_list"],params_dict["month_type_dict"] = self.get_maintplan_dict(df_dict)
        
        #st.write(params_dict["bundle_maint_dict"])
        
        
        #st.write(params_dict["sales_dict"])
        
        #st.write(params_dict["categorized_maint_plan_dict"])
        # st.write(params_dict["month_type_dict"])
        #st.write(params_dict["maint_hour_dict"])
        #st.write(params_dict["maint_month_list"])
        
        
        ###切替時間係数関係
        params_dict["switch_coeff_dict"],params_dict["inter_switch_coeff_dict"],\
        params_dict["inter_switch_maint_head_coeff_dict"],\
        params_dict["inter_switch_maint_tail_coeff_dict"] = self.get_switch_coeff_dict_temp(df_dict)
        #st.write("asasas")
        #st.write(params_dict["switch_coeff_dict"]["L1"]["11月"])
        #st.write(params_dict["inter_switch_coeff_dict"]["L1"]["11月"])
        
        
        #st.write(params_dict["prod_capacity_dict"]["L6"])
        #st.write(params_dict["maint_hour_dict"]["L6"])
        
        return params_dict,df_dict
    
    
    def get_all_params_dict(self,params_dict,all_index, plant_prod_dict, prod_plant_dict,
                            constraint_list,constraint_period_dict,ave_sales_info_dict,
                            constraint_plant_dict,single_factory_prod_list,obj_priority_dict,plant_month_index,
                            prod_month_index,multi_plant_prod_index):
        """
        エクセルからのパラメータのほか、エクセルからひつような変換を施した後のパラメータを追加する

        Args:
            params_dict (_type_): _description_
            all_index (_type_): _description_
            plant_prod_dict (_type_): _description_
            prod_plant_dict (_type_): _description_
            constraint_list (_type_): _description_
            constraint_period_dict (_type_): _description_

        Returns:
            _type_: _description_
        """
        all_params_dict = params_dict.copy()
        all_params_dict["all_index"] = all_index
        all_params_dict["plant_prod_dict"] = plant_prod_dict
        all_params_dict["prod_plant_dict"] = prod_plant_dict
        all_params_dict["constraint_list"] = constraint_list
        all_params_dict["constraint_period_dict"] = constraint_period_dict
        all_params_dict["ave_sales_info_dict"] = ave_sales_info_dict
        all_params_dict["constraint_plant_dict"] = constraint_plant_dict
        all_params_dict["single_factory_prod_list"] = single_factory_prod_list
        all_params_dict["obj_priority_dict"] = obj_priority_dict
        all_params_dict["plant_month_index"] = plant_month_index
        all_params_dict["prod_month_index"] = prod_month_index
        all_params_dict["multi_plant_prod_index"] = multi_plant_prod_index
        
    
        
        return all_params_dict
    
    def get_jissui_month_list(self,jissui_name):
        """
        実行推定の月リストを求める。
        
        0実12推、基本予算は厳密には別物らしいので、
        一応分けた。内部的な計算はかわらない。
        
        """
        
        
        if jissui_name == "基本予算":
            return self.all_month_list
        
        
        ind = jissui_name.find("実")
        
        jisseki_num = int(jissui_name[:ind])
        
        jissui_month_list = self.all_month_list[jisseki_num:]
        
        return jissui_month_list
    
    
    

    
    
    
    
    
    def get_filename(self):
        """
        結果ファイル名取得
        
        """
        now = datetime.datetime.now()
        filename = "結果_"+now.strftime('%Y%m%d_%H%M%S')+".xlsx"
        
        
        sub_folder_name = "期首在庫_販売計画_"+now.strftime('%Y%m%d_%H%M%S')
        new_params_dir = "./生成パラメタ/"+sub_folder_name+"/"
        
        
        
        return filename,new_params_dir
    
    
    def scenario_select_block(self,params_dict):
        """
        予算・実行推定を選択するブロック
        
        """
        
        #実績月をカウント
        count = 0
        for month in params_dict["sales_dict"].keys():
            total = sum(params_dict["sales_dict"][month].values())
            if total == 0:
                count+=1
        
        #index取得(基本予算と0実12推があるのが厄介だが)
        index=0
        for ind, item in enumerate(self.jissui_list):
            if item.startswith(f"{count}実"):
                index=ind
                if index==1:
                    index=0
        
        
        
        
        #予算だけでなく実行推定も
        st.write("")
        st.write("")
        st.subheader("■ シナリオ選択")
        jissui_name = st.selectbox("シナリオを選択してください",self.jissui_list,index=index)
        jissui_month_list = self.get_jissui_month_list(jissui_name)              #今回の実行推定の月リスト
        st.info("※推定月:"+" ".join(jissui_month_list))
        st.write("※期首在庫は実績月末時点での在庫として認識されます。")
        
        return jissui_month_list
    
    
    def constraint_select_block(self):
        """
        制約条件選択ブロック
        
        """
        st.write("")
        st.subheader("■ 制約条件選択")
        
        constraint_mode = st.radio("デフォルト選択",["基本予算用","よく使う制約",
                                              "よく使う制約 + 基準在庫Min（最適解がない時の原因調査用）",
                                              "必須の制約のみ",
                                              "必須の制約 + 基準在庫Min（最適解がない時の原因調査用）",
                                              "すべての制約"])
        
        ###考慮する制約条件を指定###
        st.markdown("""
                    <style>
                        .stMultiSelect [data-baseweb=select] span{
                            max-width: 500px;
                            font-size: 0.9rem;
                        }
                    </style>
                    """, 
                    unsafe_allow_html=True)
        
        
        if constraint_mode == "基本予算用":
            default_list = self.common_constraint_list+["最低生産回数以上制約","最大生産回数以下制約","最低連続生産時間以上制約"]
        
        
        
        
        if constraint_mode == "よく使う制約":
            default_list = self.common_constraint_list
        
        if constraint_mode == "よく使う制約 + 基準在庫Min（最適解がない時の原因調査用）":
            default_list = self.common_constraint_list + ["基準在庫月数Min以上制約"]
        
        
        if constraint_mode == "必須の制約のみ":
            default_list = self.base_constraint_list
        
        if constraint_mode == "必須の制約 + 基準在庫Min（最適解がない時の原因調査用）":
            default_list = self.base_constraint_list + ["基準在庫月数Min以上制約"]
        
        if constraint_mode == "すべての制約":
            default_list = self.all_constraint_list
        
        constraint_list = st.multiselect("考慮する制約条件を選択してください。(※制約条件が無さ過ぎると解けてもファイル書き出し時に失敗することがあります。)",
                                        options=self.all_constraint_list,
                                        default=default_list,)
        return constraint_list
    
    
    
    
    def constraint_period_select_block(self,constraint_list,params_dict):
        """
        制約条件の適用期間選択ブロック
        """
        st.write("")
        st.write("")
        st.write("")
        st.subheader("○ 制約条件の適用期間")
        with st.expander("制約条件の適用期間を指定する（最適解がない時の原因調査に利用）"):
            st.write("下記の制約条件は適用期間を指定できます。")
            #constraint_period_dict = {name: params_dict["jissui_month_list"] for name in self.adjustable_constraint_list}
            #st.write(constraint_period_dict)
            constraint_period_dict = {}
            for constraint_name in constraint_list:
                if constraint_name in self.adjustable_constraint_list:
                    st_end = st.select_slider("■ "+constraint_name,options=params_dict["jissui_month_list"],key=constraint_name,
                                    value=(params_dict["jissui_month_list"][0],params_dict["jissui_month_list"][-1]))
                    
                    st_index = params_dict["jissui_month_list"].index(st_end[0])
                    end_index = params_dict["jissui_month_list"].index(st_end[1])
                    
                    constraint_period_dict[constraint_name] = params_dict["jissui_month_list"][st_index:end_index+1]
        return constraint_period_dict
    
    
    def constraint_plant_select_block(self,constraint_list):
        """
        制約条件の適用工場選択ブロック
        """
        st.subheader("○ 制約条件の適用工場")
        with st.expander("制約条件の適用工場を指定する（最適解がない時の原因調査に利用）"):
            st.write("下記の制約条件は適用工場を指定できます。")
            constraint_plant_dict = {}
            for constraint_name in constraint_list:
                if constraint_name in self.selectable_constraint_list:
                    constraint_plant_list = st.multiselect("■ "+constraint_name,self.plant_list,default=self.plant_list,key=constraint_name+"plant")
                    constraint_plant_dict[constraint_name] = constraint_plant_list
                    
                if constraint_name == "負荷時間以下制約":
                    if len(constraint_plant_dict[constraint_name]) != len(self.plant_list):
                        exclusion_plant_list = list(set(self.plant_list) - set(constraint_plant_dict["負荷時間以下制約"]))
                        st.info(f'{exclusion_plant_list}に対してのみ負荷時間以下制約の代わりに基準在庫月数Min以上制約を付けてください。')
        
        return constraint_plant_dict
    

    
    
    def obj_priority_select_block(self):
        """
        目的関数選択ブロック
        
        #TODO これもUI的に長いのと、基本はいじらなさそうなので、折りたたんでもいいかも。
        最適解ない時用の目的関数よういできるといいな
        
        """
        st.write("")
        st.subheader("■ 目的関数選択")
        
        obj_mode = st.radio("デフォルト選択",["7桁在庫月数の件","検証用4","検証用3","検証用","検証用2","最適化1回目",
                                        "レア品種生産回数最小化優先",
                                       "優先SVA品種生産量最大化優先",
                                       "最適解無しの原因調査用",
                                       "最適解無しの原因調査用その2"])

        
        if obj_mode == "7桁在庫月数の件":
            obj_list = self.kensyo_obj_list5
        
        
        
        if obj_mode == "最適化1回目":
            obj_list = ["余力時間最小化"]
        
        
        if obj_mode == "最適解無しの原因調査用":
            obj_list = self.temp_obj_list
            
        if obj_mode == "最適解無しの原因調査用その2":
            obj_list = self.temp2_obj_list
            
        if obj_mode == "優先SVA品種生産量最大化優先":
            obj_list = self.all_obj_list
        
        if obj_mode == "レア品種生産回数最小化優先":
            obj_list = self.okini2_obj_list
        
        if obj_mode == "検証用":
            obj_list = self.kensyo_obj_list
        if obj_mode == "検証用2":
            obj_list = self.kensyo_obj_list2
        if obj_mode == "検証用3":
            obj_list = self.kensyo_obj_list3
            
        if obj_mode == "検証用4":
            obj_list = self.kensyo_obj_list4
        
        
        
        # 選択された目的関数を保存する辞書
        obj_priority_dict = {}
        # 順位ごとに目的関数を選択するセレクトボックス #TODO モード選択いれたらうまくいかなかくなった？？
        for rank in range(1, len(obj_list) + 1):
            # すでに選択された食べ物を除いたリストを作成
            available_objs = [obj for obj in obj_list if obj not in obj_priority_dict.values()]
            obj = st.selectbox(f'優先度{rank}位の目的関数を選んでください:', [''] + available_objs, index=1,key=rank)
            if obj:
                obj_priority_dict[rank] = obj
        
        return obj_priority_dict
    
    
    
    def stock_setting_select_block(self,params_dict):
        st.write("")
        st.write("")
        st.subheader("■ 在庫月数の計算設定")
        
    
        ave_month_num = st.selectbox("販売量を何か月平均するか",
                                        [i+1 for i in range(len(params_dict["jissui_month_list"]))],
                                        index=len(params_dict["jissui_month_list"])-1)
        ave_sales_mode = st.radio(label="販売量の平均に当月を含むか", options=["含む",'含まない'])
        ave_sales_info_dict = {"ave_month_num":ave_month_num,
                                "ave_sales_mode":ave_sales_mode}
        
        example_month = params_dict['jissui_month_list'][0]
        
        if ave_sales_mode == "含む":
            example_ave_sales_month_list = params_dict["jissui_month_list"][:ave_month_num]
        
        if ave_sales_mode == "含まない":
            example_ave_sales_month_list = params_dict["jissui_month_list"][1:ave_month_num+1]
        
        
        #2がつとか3月の件も。考慮
        st.info(f"※例：{example_month}の在庫月数の計算には、"+" ".join(example_ave_sales_month_list)+" の販売量（の平均値）を使います。")
        
        return ave_sales_info_dict
    
    def mode_select_block(self,df_dict,params_dict):
        st.subheader("■ モード選択")
        with st.expander("モードを指定する（当面はいじらなくてよいです）"):
            mode = st.radio(label="生産能力確認モードを選択した場合は、各工場の代表CSの情報を使って最適化します",options=["詳細割り当てモード",'生産能力確認モード'])
            
            #生産能力確認モードの場合はCSと幅を代表CSと代表幅で上書きする。(代表幅の取り扱いどうする？？（笑）
            if mode == "生産能力確認モード":
                for name in params_dict["cs_dict"].keys():
                    for plant in params_dict["cs_dict"][name].keys():
                        for month in params_dict["cs_dict"][name][plant].keys():
                            params_dict["cs_dict"][name][plant][month] = df_dict["代表CS"]["代表CS"][plant]
                
                #これ変？？いや、あってる？
                params_dict["cs_dict"] = self.get_cs_dict(df_dict["cs"])

    
    def get_init_solution(self):
        """
        初期解がすでにある場合は読み込む
        """
        
        # 選択したフォルダパス
        folder_path = SOLUTION_DIR

        # 指定したフォルダ内のファイルをリストアップ（ディレクトリを除外）
        file_list = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

        default_file = "solution_2025-02-04_17-38-31_余力時間最小化.pkl"
        
        default_index = file_list.index(default_file)

        
        # ファイル選択ウィジェット
        selected_file = st.selectbox('初期解ファイルを選択してください', file_list,default_index)
        
        file_path = os.path.join(folder_path, selected_file)
        with open(file_path, 'rb') as f:
            # Pickleファイルの読み込み
            initial_solution = pickle.load(f)
        
        return initial_solution
    
    

    
    
    def main(self):

        st.title("工場・月度割り当て最適化シミュレータ")
        st.write("------------------------------------")
        st.subheader("■ パラメータ入力")
        
        file_switch = st.file_uploader("切替時間のパラメータファイルをアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        file = st.file_uploader("その他のパラメータファイルをアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        
        #ファイルがアップロードされたら
        if (file_switch is not None) and (file is not None):
            params_dict,df_dict = self.get_params_dict(file_switch,file)                                  #辞書型で保存
            
            #TODO jissui_month_listはあとてparams_dictに入れた方がコードキレイ
            params_dict["jissui_month_list"] = self.scenario_select_block(params_dict)        #シナリオ選択ブロック
            constraint_list = self.constraint_select_block()                                  #考慮する制約条件を指定ブロック
            constraint_period_dict = self.constraint_period_select_block(constraint_list,
                                                                         params_dict)         #制約条件の適用期間選択ブロック
            constraint_plant_dict = self.constraint_plant_select_block(constraint_list)       #制約条件の適用工場選択ブロック
            
            #st.write(constraint_plant_dict)
            
            obj_priority_dict = self.obj_priority_select_block()                              #目的関数選択ブロック
            ave_sales_info_dict = self.stock_setting_select_block(params_dict)                #在庫月数計算設定ブロック
            
            
            
            st.write("")
            st.subheader("■ 計算時間の上限")
            timelimit = st.number_input("1つの目的関数の計算時間の上限を入力してください（あくまで目安であり必ず守られるわけではありません。）",min_value=10,value=100)
            params_dict["timelimit"] = timelimit
            
            st.write("")
            #tolerance_mode = st.checkbox("解無しの場合は余力時間のマイナスを許容し最適化を実行",value=True)
            #params_dict["tolerance_mode"] = tolerance_mode
            
            st.write("")
            st.write("")
            st.write("")
            

            
            
            if "result_file_name" not in st.session_state:
                st.session_state["result_file_name"] = None
                
            if "new_params_dir" not in st.session_state:
                st.session_state["new_params_dir"] = None
                
            
            
            #initial_solution = self.get_init_solution()       #初期解
            initial_solution =None
            params_dict["initial_solution"] = initial_solution
            
            
            
            ##シミュレーション実行
            button = st.button("シミュレーション実行")
            
            if button == True:
                self.result_file_name,self.new_params_dir = self.get_filename()               #結果ファイル
                st.session_state["result_file_name"] = self.result_file_name
                st.session_state["new_params_dir"] = self.new_params_dir
                
                #共通要素
                all_index, plant_prod_dict, prod_plant_dict,\
                single_factory_prod_list,plant_month_index,\
                prod_month_index,multi_plant_prod_index = CommonProcess(params_dict["jissui_month_list"],
                                                params_dict["cs_dict"],
                                                ).main()
                
                
                
                #パラメータ全部まとめた辞書
                all_params_dict = self.get_all_params_dict(params_dict,all_index, plant_prod_dict, prod_plant_dict,
                                                        constraint_list,constraint_period_dict,ave_sales_info_dict,
                                                        constraint_plant_dict,single_factory_prod_list,obj_priority_dict,plant_month_index,
                                                        prod_month_index,multi_plant_prod_index
                                                        )
                
                # with open("./test/all_params_dict.pickle", mode='wb') as f:
                #     pickle.dump(all_params_dict,f)
                
                
                
                    
                #エラーの数
                error_num = ContradictionDetector(all_params_dict).main()                           #エラー見つけモジュール
                
                
                
                #エラーが0個だったら最適化計算実施
                if error_num == 0:
                    #with st.spinner('最適化計算中です。'):
                        
                    ##最適化モジュール動く
                    variables, problem, status, objective_value_dict = HierachicalOptimizer(all_params_dict).main()   #階層的最適化
                    #st.table(objective_value_dict)
                    
                    
                    # with open("./結果/mip_result_dict.pickle", mode='wb') as f:
                    #      pickle.dump(variables,f)
                    
                    
                    
                    
                    

                    #TODOステータスは-3~1まであるのですべて捕捉できるように。
                    if (status != "Optimal") and (status == "Not Solved"):
                        st.warning("制約をすべて満たした最適解が見つかりませんでした。")
                        
                        
                    if (status == "Optimal") or (status == "Not Solved"):
                        placeholder = st.empty()
                        placeholder.success("制約をすべて満たした最適解が見つかりました。結果ファイル生成中です。操作しないでください。")
                        st.table(objective_value_dict)
                        init_stock_df, sales_amount_df = ResultOutputter(all_params_dict,variables, problem,
                                                                        self.result_file_name).main()
                        
                        XlDecorator(self.result_file_name,all_params_dict["jissui_month_list"]).main()
                        
                        XlNavigationMaker(self.result_file_name).main()
                        
                        
                        # SeqParamsOutputter(sales_amount_df, init_stock_df, 
                        #                 params_dict["jissui_month_list"],self.new_params_dir).main()
                        
                        placeholder.empty()
            
            
            st.write("-----------------------")
            st.subheader("■ 最適化結果")
            st.write("直前に実行した計算結果がダウンロードできます。（計算未実行の場合は何も表示されません。）")
            
            #結果ファイルがある場合はダウンロードボタンを表示する。
            if st.session_state["result_file_name"] is not None:
                result_file_path = RESULT_DIR / st.session_state["result_file_name"]
                if os.path.isfile(result_file_path):
                    with open(result_file_path, "rb") as fp:
                        btn = st.download_button(
                            label="結果ファイルダウンロード",
                            data=fp,
                            file_name=st.session_state["result_file_name"],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="result")
                        
                # if os.path.isfile("./結果/"+st.session_state["result_file_name"]):
                #     with open(st.session_state["new_params_dir"] +"期首在庫.xlsx", "rb") as fp:
                #         btn = st.download_button(
                #             label="（順序シミュ用）期首在庫パラメータファイルダウンロード",
                #             data=fp,
                #             file_name="期首在庫.xlsx",
                #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                #             key="init_stock")
                
                # if os.path.isfile("./結果/"+st.session_state["result_file_name"]):
                #     with open(st.session_state["new_params_dir"] +"販売計画.xlsx", "rb") as fp:
                #         btn = st.download_button(
                #             label="（順序シミュ用）販売計画ファイルダウンロード",
                #             data=fp,
                #             file_name="販売計画.xlsx",
                #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                #             key="sales")
                
            
##########################################################################################
if __name__ == "__main__":
    AllocationWeb().main()
            