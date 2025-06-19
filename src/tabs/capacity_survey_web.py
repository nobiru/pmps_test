from allocation_web import AllocationWeb
import streamlit as st
from index_generator import CommonProcess
from contradiction_detector import ContradictionDetector
import itertools
#from hierachical_mip import HierachicalMip
#from mip_core_2 import MipCore
import time

class CapacitySurveyWeb(AllocationWeb):
    """    
    生産キャパ自動調査
    
    いろいろめんどいのでAllocationWebを継承する。

    """
    def __init__(self):
        super().__init__()
    

    def powerset(self,input_list):
        """
        べき集合を生成する関数
        
        工場のリストを受け取って、そのすべての部分集合をリストで返す。
        
        
        #TODO 全工場が要素である集合は抜けているが、それでいいのか？

        """
        # 空リストから元のリストの長さまでの組み合わせを生成
        result = []
        for r in range(len(input_list)):
            combinations = itertools.combinations(input_list, r)
            result.extend(combinations)
        return result
    
    def get_constraint_period_dict(self,constraint_list,params_dict):
        constraint_period_dict = {}
        for constraint_name in constraint_list:
            if constraint_name in self.adjustable_constraint_list:
                constraint_period_dict[constraint_name] = params_dict["jissui_month_list"]
        
        return constraint_period_dict
        
        
    def get_constraint_plant_dict(self,constraint_list,powerset):
        """
        負荷時間以下制約を付けるのは、powersetの補集合。
        つまり、powersetに含まれる工場については、負荷時間以下制約を付けない。


        """
        constraint_plant_dict = {}
        for constraint_name in constraint_list:
            if constraint_name in self.selectable_constraint_list:
                
                if constraint_name == "負荷時間以下制約":
                    complement_set = set(self.plant_list) - set(powerset)         #補集合
                    constraint_plant_dict[constraint_name] = list(complement_set)
                else:
                    constraint_plant_dict[constraint_name] = self.plant_list
        
        return constraint_plant_dict
    
    def get_obj_priority_dict(self):
        obj_priority_dict = {1:"基準在庫月数Min以上制約違反回数最小化"}
        return obj_priority_dict
    
    
    def get_stock_setting(self,params_dict):
        
        ave_month_list = [i+1 for i in range(len(params_dict["jissui_month_list"]))]
        ave_month_num = ave_month_list[len(params_dict["jissui_month_list"])-1]
        
        ave_sales_mode = "含む"
        ave_sales_info_dict = {"ave_month_num":ave_month_num,
                                "ave_sales_mode":ave_sales_mode}
        
        return ave_sales_info_dict
    
    
    def get_run_flag(self,powerset,factor_powerset_list):
        """
        負荷時間以下制約を付ける工場の組み合わせについて、
        
        最適解のあった工場の集合の部分集合であれば必ず最適解になるので、
        それはわざわざ計算する必要がないのでここではじく。
        
        プログラム的には↑を直接ではなく補集合で実施。
        
        
        factor_powerset_list: 最適解があった工場の組み合わせの、補集合のリスト
        （つまり負荷時間以下制約を抜いた工場の組み合わせ。）
        
        
        """
        
        run_flag = True
        for factor_powerset in factor_powerset_list:
            if set(factor_powerset).issubset(set(powerset)):
                run_flag = False
        return run_flag
        
    
    
    
    
    def main(self):
        st.title("負荷時間不足工場の調査")
        st.write("必須の制約でも最適解がない時の調査専用シミュレータです。")     #TODO 確定生産・確定販売つきでもいける？
        st.write("------------------------------------")
        st.subheader("■ パラメータ入力")
        file = st.file_uploader("パラメータファイルアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        
        #ファイルがアップロードされたら
        if file is not None:
            params_dict,df_dict = super().get_params_dict(file)                                  #辞書型で保存
            
            
            params_dict["jissui_month_list"] = super().scenario_select_block(params_dict)        #シナリオ選択ブロック
            params_dict["timelimit"] = 300
            
            ##シミュレーション実行
            button = st.button("負荷時間不足工場の調査実行")    
            
            if button == True:
                with st.status(f'負荷時間不足工場（群）を探しています。', expanded=True) as progress2:
                    progressHolder = st.empty()
                    my_bar = progressHolder.progress(0,text="お待ちください")
                    
                    
                    self.result_file_name,self.new_params_dir = self.get_filename()               #結果ファイル
                            
                    #共通要素
                    all_index, plant_prod_dict, prod_plant_dict,single_factory_prod_list = CommonProcess(params_dict["jissui_month_list"],
                                                                                                        params_dict["cs_dict"]).main()
                    
                    
                    all_powerset_list = self.powerset(self.plant_list)         #すべてのべき集合のリスト
                    

                    
                    factor_powerset_list = []                                                          #生産キャパ不足工場と認定された工場クラスタリスト
                    
                    #すべての組み合わせで実行
                    for index,powerset in enumerate(all_powerset_list):
                        
                        ratio = index/len(all_powerset_list)
                        my_bar.progress(ratio, text=f'{round(ratio*100)}％終了')
                        
                        run_flag = self.get_run_flag(powerset,factor_powerset_list)                    #シミュレーション実行するかどうか。
                        
                        if run_flag is True:
                            constraint_list = self.base_constraint_list                                          #必須の制約のみ
                            constraint_period_dict = self.get_constraint_period_dict(constraint_list,
                                                                                    params_dict)                 #制約条件の適用期間の辞書
                            constraint_plant_dict = self.get_constraint_plant_dict(constraint_list,powerset)     #制約条件の適用工場の辞書
                            
                            
                            obj_priority_dict = self.get_obj_priority_dict()                                       #目的関数（たぶんこれはなんでもいいハズ）
                            ave_sales_info_dict = self.get_stock_setting(params_dict)    
                        
                        
                            #パラメータ全部まとめた辞書
                            all_params_dict = self.get_all_params_dict(params_dict,all_index, plant_prod_dict, prod_plant_dict,
                                                                    constraint_list,constraint_period_dict,ave_sales_info_dict,
                                                                    constraint_plant_dict,single_factory_prod_list,obj_priority_dict,
                                                                    )
                                
                                
                            #エラーの数
                            error_num = ContradictionDetector(all_params_dict).main()                           #エラー見つけモジュール
                            
                            
                            
                            #エラーが0個だったら最適化計算実施
                            if error_num == 0:
                                ##最適化モジュール動く
                                prod_amount_dict,sales_amount_dict,status,objective_value = MipCore(all_params_dict,
                                                                                            obj_name=obj_priority_dict[1],
                                                                                            additional_constraint_dict={},
                                                                                            timelimit=params_dict["timelimit"]).main()    #最適化実施
                            
                                #最適解ありパターン
                                if (status == 1) or (status == 0):
                                    factor_powerset_list.append(powerset)
                                    if index == 0:
                                        #全工場付与で最適解ありなケースに該当
                                        break    
                    
                    
                    
                    if len(factor_powerset_list[0]) == 0:
                        
                        #st.write(factor_powerset_list)
                        ratio = 1.0
                        my_bar.progress(ratio, text=f'{round(ratio*100)}％終了')
                        time.sleep(0.5)
                        my_bar.empty()
                        st.success("負荷時間の不足している工場はありません。")
                        
                    else: 
                        my_bar.empty()
                        st.write("負荷時間の足りない工場（群）の候補は以下の通りです。")
                        st.write("候補が複数出てきた場合は、負荷時間の調整しやすい組み合わせの候補を選んでください。")
                        for index,factor_powerset in enumerate(factor_powerset_list):
                            output = 'と'.join([f"{element}" for element in factor_powerset])
                            st.success(f'候補{index+1}：{output}')
                    progress2.update(label="調査終了！", state="complete", expanded=True)