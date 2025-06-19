from allocation_web import AllocationWeb
import streamlit as st
from index_generator import CommonProcess
from contradiction_detector import ContradictionDetector
import itertools
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent  # 上2階層上に移動してルートに到達
sys.path.append(str(root_path))  # ルートディレクトリを sys.path に追加
from setup_paths import add_project_paths
add_project_paths()

from mip_core_fine_tuning import MipCoreFineTuning

from result_outputter import ResultOutputter
from seq_params_outputter import SeqParamsOutputter
import os
from xl_decorator import XlDecorator
from xl_navigation_maker import XlNavigationMaker
from new_params_getter import NewParamsGetter


class FineTuningWeb(AllocationWeb):
    """
    生産キャパ自動調査

    いろいろめんどいのでAllocationWebを継承する。

    """
    def __init__(self):
        super().__init__()



    def get_max_month(self,params_dict,prod_or_sales):
        def month_to_number(month):
            month_mapping = {
                "1月": 13, "2月": 14, "3月": 15, "4月": 4, "5月": 5, "6月": 6,
                "7月": 7, "8月": 8, "9月": 9, "10月": 10, "11月": 11, "12月": 12
            }
            return month_mapping.get(month, 0)

        max_month_num = 0
        max_month = ""
        data = params_dict[prod_or_sales]
        for variety, factories in data.items():
            for factory, months in factories.items():
                for month in months.keys():
                    if month.endswith("月"):  # 月の名称かどうかを確認
                        month_num = month_to_number(month)  # 月を数値に変換して比較
                        if month_num > max_month_num:
                            max_month_num = month_num
                            max_month = month

        return max_month


    def get_constraint_period_dict(self,constraint_list,params_dict):
        constraint_period_dict = {}
        for constraint_name in constraint_list:
            if constraint_name in self.adjustable_constraint_list:
                constraint_period_dict[constraint_name] = params_dict["jissui_month_list"]

        return constraint_period_dict


    def get_constraint_plant_dict(self,constraint_list,temp_plant_list):
        constraint_plant_dict = {}
        for constraint_name in constraint_list:
            if constraint_name in self.selectable_constraint_list:
                if constraint_name == "負荷時間以下制約":
                    constraint_plant_dict[constraint_name] = temp_plant_list
                else:
                    constraint_plant_dict[constraint_name] = self.plant_list

        return constraint_plant_dict

    def get_stock_setting(self,params_dict):

        ave_month_list = [i+1 for i in range(len(params_dict["jissui_month_list"]))]
        ave_month_num = ave_month_list[len(params_dict["jissui_month_list"])-1]

        ave_sales_mode = "含む"
        ave_sales_info_dict = {"ave_month_num":ave_month_num,
                                "ave_sales_mode":ave_sales_mode}

        return ave_sales_info_dict


    def main(self):
        st.title("確定量の微調整")
        st.write("確定生産量・確定販売量の制約を付けた時に最適解がない時に、微調整するための専用シミュレータ")
        st.write("------------------------------------")
        st.subheader("■ パラメータ入力")
        file = st.file_uploader("パラメータファイルアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        #ファイルがアップロードされたら
        if file is not None:
            params_dict,df_dict = super().get_params_dict(file)
            params_dict["jissui_month_list"] = super().scenario_select_block(params_dict)        #シナリオ選択ブロック
            params_dict["timelimit"] = 300


            max_month_prod = self.get_max_month(params_dict,"finalized_prod_dict")
            max_month_sales = self.get_max_month(params_dict,"finalized_sales_dict")




            st.subheader("■ 工場の選択")
            temp_plant_list = st.multiselect("工場を選択してください。(負荷時間以下制約を守れない工場は除いて下さい。)",
                                             self.plant_list,default=self.plant_list)



            #TODO この固定月の選択のところ、自動化できるか？？
            st.subheader("■ 固定月の選択")


            prod_all_month_list = params_dict["jissui_month_list"][:params_dict["jissui_month_list"].index(max_month_prod)+1]
            prod_month_list = st.multiselect("絶対に固定したい確定生産量の月",prod_all_month_list)



            sales_all_month_list = params_dict["jissui_month_list"][:params_dict["jissui_month_list"].index(max_month_sales)+1]
            sales_month_list = st.multiselect("絶対に固定したい確定販売量の月",sales_all_month_list)


            params_dict["prod_month_list"] = prod_month_list
            params_dict["sales_month_list"] = sales_month_list

            st.write("負荷時間以下制約、合計販売量一致制約、月末在庫0以上制約は考慮されます。")



            if "result_file_name" not in st.session_state:
                st.session_state["result_file_name"] = None

            if "new_params_dir" not in st.session_state:
                st.session_state["new_params_dir"] = None



            ##シミュレーション実行
            button = st.button("確定量の微調整実行")

            if button ==True:

                self.result_file_name,self.new_params_dir = self.get_filename()               #結果ファイル
                st.session_state["result_file_name"] = self.result_file_name
                st.session_state["new_params_dir"] = self.new_params_dir

                #共通要素
                all_index, plant_prod_dict, prod_plant_dict,single_factory_prod_list = CommonProcess(params_dict["jissui_month_list"],
                                                                                                        params_dict["cs_dict"]).main()



                constraint_list = self.common_constraint_list
                constraint_period_dict = self.get_constraint_period_dict(constraint_list,
                                                                                    params_dict)                 #制約条件の適用期間の辞書
                constraint_plant_dict = self.get_constraint_plant_dict(constraint_list,temp_plant_list)     #制約条件の適用工場の辞書


                obj_priority_dict = {1:None}                                       #目的関数
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
                    prod_amount_dict,sales_amount_dict,status,objective_value = MipCoreFineTuning(all_params_dict,
                                                                                timelimit=params_dict["timelimit"]).main()    #最適化実施


                    if (status == -1) or (status == -2) or (status == -3):
                        st.warning("制約をすべて満たした最適解が見つかりませんでした。")

                    if (status == 1) or (status == 0):
                        placeholder = st.empty()
                        placeholder.success("制約をすべて満たした最適解が見つかりました。結果ファイル生成中です。操作しないでください。")


                        placeholder.empty()

                        st.write("-----------------------")
                        st.subheader("■ 微調整結果")
                        st.write("直前に実行した計算結果です。（計算未実行の場合は何も表示されません。）")



                        #パラメータを更新する、それをダウンロードできるようにする。
                        new_file = NewParamsGetter(prod_amount_dict,sales_amount_dict,all_params_dict,file).main()

                        # btn = st.download_button(label="新パラメータダウンロード",
                        #                             data=new_file,
                        #                             file_name="新パラメータやで.xlsx",
                        #                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        #             key="params_new")







