import streamlit as st
from itertools import combinations
from allocation_web import AllocationWeb
from index_generator import CommonProcess
from hierachical_optimizer import HierachicalOptimizer

class BundlingMaintSurveyWeb(AllocationWeb):
    """
    "抱き合わせる保全の組み合わせ調査"のwebアプリを提供するクラス
    
    そもそも必須の制約ですら最適解がないような、保全の抱き合わせの組み合わせを
    排除するために実行。
    
    
    
    """

    
    def __init__(self):
        super().__init__()
    
    
    
    
    def generate_all_combinations(self,nested_dict):
        """
        Generate a list of all possible combinations of entries where:
        '抱き合わせ可能' is True and '抱き合わせ希望' is False.
        
        Args:
            nested_dict (dict): Original nested dictionary.
        
        Returns:
            list: List of all possible combinations as tuples.
        """
        # Extract all eligible entries
        eligible_entries = []
        for factory, maintenances in nested_dict.items():
            for maintenance, details in maintenances.items():
                if details['抱き合わせ可能'] and not details['抱き合わせ希望']:
                    eligible_entries.append((factory, maintenance))
        
        # Generate all combinations
        all_combinations = []
        for r in range(1, len(eligible_entries) + 1):
            all_combinations.extend(combinations(eligible_entries, r))
        
        return all_combinations

    def apply_combination_to_dict(self,nested_dict, combination):
        """
        Generate a new dictionary by applying a specific combination to the nested dictionary.
        Set '抱き合わせ希望' to True in the relevant entries.
        
        Args:
            nested_dict (dict): Original nested dictionary.
            combination (list of tuple): Combination of (factory, maintenance) to apply.
        
        Returns:
            dict: New dictionary with the combination applied.
        """
        # Create a deep copy of the original dictionary
        new_dict = {factory: {maintenance: details.copy() 
                            for maintenance, details in maintenances.items()} 
                    for factory, maintenances in nested_dict.items()}
        
        # Apply the combination
        for factory, maintenance in combination:
            if factory in new_dict and maintenance in new_dict[factory]:
                new_dict[factory][maintenance]['抱き合わせ希望'] = True
        
        return new_dict
    
    
    
    
    def get_temp_maintplan_dict(self,df_dict,temp_bundle_maint_options_dict):
        

        
        #保全計画の辞書を、head,middle,tailに分ける
        categorized_maint_plan_master_dict,categorized_maint_plan_dict = super().get_categorized_maint_plan_dict(df_dict["保全計画（新）"],temp_bundle_maint_options_dict)
        
        #st.write(categorized_maint_plan_master_dict)
        #st.write(categorized_maint_plan_dict)
        
        
        
        bundled_maint_dict = super().get_bundled_maint_dict(df_dict["保全計画（新）"], temp_bundle_maint_options_dict)   #抱き合わせ保全の辞書
        #st.write(bundled_maint_dict)
        
        
        
        #保全時間が0でない月のリストを取得する
        maint_hour_dict = super().get_maint_hour_dict_2(df_dict["保全計画（新）"],temp_bundle_maint_options_dict)
        #st.write("maintだよ")
        #st.write(maint_hour_dict)
        
        #各工場各月に保全時間が何時間あるか。
        maint_month_list= super().get_maint_month_list(maint_hour_dict)
        #st.write(maint_month_list)
        
        
        #月タイプの辞書。切替時間の近似モデルの使い分けのために必要。
        month_type_dict = super().get_month_type_dict2(categorized_maint_plan_dict)
        #st.write(month_type_dict)
        
        
        return bundled_maint_dict,categorized_maint_plan_dict,maint_hour_dict,maint_month_list,month_type_dict
    
    
    
    
    
    
    
    def main(self):
        st.title("抱き合わせる保全の組み合わせ調査")
        st.write("必須の制約で最適解があるような、保全の抱き合わせの組み合わせを探す専用シミュレータです。")     #TODO 確定生産・確定販売つきでもいける？
        
        
        
        file_switch = st.file_uploader("切替時間のパラメータファイルをアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        file = st.file_uploader("その他のパラメータファイルをアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
        
        #ファイルがアップロードされたら
        if (file_switch is not None) and (file is not None):
            params_dict,df_dict = super().get_params_dict(file_switch,file)                                  #辞書型で保存
            
            params_dict["jissui_month_list"] = super().scenario_select_block(params_dict)        #シナリオ選択ブロック
            params_dict["timelimit"] = 10
            
            
            
            constraint_list = self.constraint_select_block()                                  #考慮する制約条件を指定ブロック
            constraint_period_dict = self.constraint_period_select_block(constraint_list,
                                                                         params_dict)         #制約条件の適用期間選択ブロック
            constraint_plant_dict = self.constraint_plant_select_block(constraint_list)       #制約条件の適用工場選択ブロック
            
            #obj_priority_dict = self.obj_priority_select_block()                              #目的関数選択ブロック
            #st.write(obj_priority_dict)
            
            obj_priority_dict={1:"メインドープによる立上・立下回数最大化"}
            ave_sales_info_dict = self.stock_setting_select_block(params_dict)                #在庫月数計算設定ブロック
            
            
            
            #共通要素
            all_index, plant_prod_dict, prod_plant_dict,single_factory_prod_list,plant_month_index= CommonProcess(params_dict["jissui_month_list"],
                                                                                                    params_dict["cs_dict"],
                                                                                                    ).main()
            
            
            
            #パラメータ全部まとめた辞書
            all_params_dict = self.get_all_params_dict(params_dict,all_index, plant_prod_dict, prod_plant_dict,
                                                    constraint_list,constraint_period_dict,ave_sales_info_dict,
                                                    constraint_plant_dict,single_factory_prod_list,obj_priority_dict,plant_month_index
                                                    )
            
            
            bundle_maint_options_dict = all_params_dict["bundle_maint_options_dict"]
            
            
            ##シミュレーション実行
            button = st.button("抱き合わせる保全の組み合わせ調査実行")    
            
            if button == True:
                #with st.status(f'解がある抱き合わせ方を探しています。', expanded=True) as progress2:
                progressHolder = st.empty()
                my_bar = progressHolder.progress(0,text="お待ちください")
                
                
                
                # Generate all combinations
                all_combinations = self.generate_all_combinations(bundle_maint_options_dict)
                all_combinations.reverse()
                
                for combination in all_combinations:
                    temp_bundle_maint_options_dict = self.apply_combination_to_dict(bundle_maint_options_dict,combination)
                    
                    bundled_maint_dict,categorized_maint_plan_dict,\
                    maint_hour_dict,maint_month_list,month_type_dict = self.get_temp_maintplan_dict(df_dict,temp_bundle_maint_options_dict)
                    
                    params_dict["bundle_maint_options_dict"] = temp_bundle_maint_options_dict
                    params_dict["bundle_maint_dict"] = bundled_maint_dict
                    params_dict["categorized_maint_plan_dict"] = categorized_maint_plan_dict
                    params_dict["maint_hour_dict"] = maint_hour_dict
                    params_dict["maint_month_list"] = maint_month_list
                    params_dict["month_type_dict"] = month_type_dict
                    
                    st.write(temp_bundle_maint_options_dict["L6"])
                    
                    
                    variables, problem, status, objective_value_dict = HierachicalOptimizer(all_params_dict).main()   #階層的最適化
                    
                    if (status != "Optimal") and (status == "Not Solved"):
                        st.warning(f"制約をすべて満たした解が見つかりませんでした。{combination}")
                    
                    
                    if (status == "Optimal") or (status == "Not Solved"):
                        st.success(f"制約をすべて満たした解が見つかりました。{combination}")
                        #st.write(combination)
        
        
        
        
        
    