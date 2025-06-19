import pulp
from datetime import datetime
import pickle
from index_generator import CommonProcess
#from mip_core_2 import MipCore
import streamlit as st
import time

from model_variables import ModelVariables


from constraints_catalog import ConstraintsCatalog
from objective_function_catalog import ObjectiveFunctionCatalog
from direct_opimizer import DirectOptimizer
from feasibility_optimizer import FeasibilityOptimizer

import tempfile
import os
import random
import pandas as pd


import sys
from pathlib import Path


#TODO 結局これはいるの？いらないの？
root_path = Path(__file__).resolve().parent.parent  # 上2階層上に移動してルートに到達
sys.path.append(str(root_path))                     # ルートディレクトリを sys.path に追加

from output_config import SOLUTION_DIR



class HierachicalOptimizer():
    """
    混合整数計画法実装
    階層的最適化実行
    
    
    """
    def __init__(self,all_params_dict):
        
        #TODO 定式化ログファイルそもそも出力するべきか。出力フォーマットどうするか。 
        self.logfile_dir = "./定式化log/"                                         #定式化のログファイル保存先
        
        
        self.all_params_dict = all_params_dict                                     #全パラメータ辞書
        
        self.obj_priority_dict = all_params_dict["obj_priority_dict"]             #目的関数(優先度つき)
        
        self.timelimit = all_params_dict["timelimit"]                             #最適化時間制限
        #self.tolerance_mode = all_params_dict["tolerance_mode"]                   #
        
        self.initial_solution = all_params_dict["initial_solution"]               #初期解
        
        
        
 
        #目的関数名と制約条件名のマッピング
        self.obj_constraint_dict = {"長時間ドープ切り替え回数最小化":{"constraint_name":"長時間ドープ切り替え回数一致制約",
                                                                        "type":"direct",
                                                                        "init_num":-1},
                                        "SAZMA系品種連続生産月数最大化":{"constraint_name":"SAZMA系品種連続生産月数一致制約",
                                                                        "type":"direct",
                                                                        "init_num":12},
                                        "基準在庫月数Min以上制約違反回数最小化":{"constraint_name":"基準在庫月数Min以上制約違反回数一致制約",
                                                                            "type":"direct",
                                                                            "init_num":-1},
                                        "基準在庫月数Max以下制約違反回数最小化":{"constraint_name":"基準在庫月数Max以下制約違反回数一致制約",
                                                                            "type":"direct",
                                                                            "init_num":-1},
                                        "優先SVA品種の合計生産量を最大化":{"constraint_name":"優先SVA品種の合計生産量一致制約",
                                                                        "type":"direct"},
                                        "サブ品種の合計生産量最小化":{"constraint_name":"サブ品種の合計生産量一致制約",
                                                                    "type":"direct"},
                                        "合計生産時間最大化":{"constraint_name":"合計生産時間一致制約",
                                                            "type":"direct"},
                                        "超過月末在庫量最小化":{"constraint_name":"超過月末在庫量一致制約",
                                                                "type":"direct"},
                                        "レア品種の合計生産回数最小化":{"constraint_name":"レア品種の合計生産回数一致制約",
                                                                    "type":"direct",
                                                                    "init_num":-1},
                                        "負荷時間以下制約違反量最小化":{"constraint_name":"負荷時間以下制約違反量一致制約",
                                                                    "type":"direct"},
                                        "保全月合計ドープ数最小化":{"constraint_name":"保全月合計ドープ数一致制約",
                                                                    "type":"direct",
                                                                    "init_num":-1},
                                        "基準在庫月数Min超在庫量最小化（原因調査用）":{"constraint_name":"基準在庫月数Min超在庫量一致制約",
                                                                                    "type":"direct"},
                                        "メインドープによる立上・立下回数最大化":{"constraint_name":"メインドープによる立上・立下回数一致制約",
                                                                                "type":"direct",
                                                                                "init_num":40},
                                        "メイン品種生産量最大化":{"constraint_name":"メイン品種生産量一致制約",
                                                                                "type":"direct",
                                                                                "init_num":40},
                                        
                                        "全工場合計切替時間最小化":{"constraint_name":"全工場合計切替時間一致制約",
                                                                    "type":"direct"},
                                        
                                        "長時間ドープ切替工場合計切替時間最小化":{"constraint_name":"長時間ドープ切替工場合計切替時間一致制約",
                                                                    "type":"direct"},
                                        "合計生産回数最小化":{"constraint_name":"合計生産回数一致制約",
                                                                    "type":"direct"},
                                        
                                        "負荷時間スラック変数合計最小化":{"constraint_name":"負荷時間スラック変数合計一致制約","type":"direct"},
                                        "生産イベント月数最大化":{"constraint_name":"生産イベント月数一致制約","type":"direct"},
                                        "余力時間最小化":{"constraint_name":"余力時間一致制約","type":"direct"},
                                        "負荷時間スラック変数合計最小化2":{"constraint_name":"負荷時間スラック変数合計一致制約","type":"direct"},
                                        "余力時間最小化2":{"constraint_name":"余力時間一致制約2","type":"direct"},
                                        "基準在庫月数違反回数最小化":{"constraint_name":"基準在庫月数違反回数一致制約","type":"direct"},
                                        "7桁在庫月数合計最小化":{"constraint_name":"7桁在庫月数合計一致制約","type":"direct"},
                                        "7桁基準在庫月数Max以下制約違反回数最小化":{"constraint_name":"7桁基準在庫月数Max以下制約違反回数一致制約","type":"direct"},
                                        "7桁基準在庫月数Min以上制約違反回数最小化":{"constraint_name":"7桁基準在庫月数Min以上制約違反回数一致制約","type":"direct"},
                                        "年度末7桁基準在庫月数Min以上制約違反回数最小化":{"constraint_name":"年度末7桁基準在庫月数Min以上制約違反回数一致制約","type":"direct"},
                                        }#TODO Min超えか0以上越えか決める。
        
        
        
        #TODO 基準在庫MinMAxを計算後、何倍くらいまで許容すべきか。
        #TODO gaprelも目的関数に応じて可変にしたいので、ここに追加する？
        self.limit_coeff_dict = {"余力時間最小化":{"min_coeff":0,"max_coeff":1.0000000001},
                                 "余力時間最小化2":{"min_coeff":0,"max_coeff":1.000001},
                                 "保全月合計ドープ数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "長時間ドープ切替工場合計切替時間最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "基準在庫月数Min以上制約違反回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "基準在庫月数Max以下制約違反回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "基準在庫月数違反回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "レア品種の合計生産回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "サブ品種の合計生産量最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "優先SVA品種の合計生産量を最大化":{"min_coeff":0.9,"max_coeff":1000},
                                 "メインドープによる立上・立下回数最大化":{"min_coeff":0.9,"max_coeff":1000},
                                 "メイン品種生産量最大化":{"min_coeff":0.9,"max_coeff":1000},
                                 "合計生産回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "負荷時間スラック変数合計最小化":{"min_coeff":0,"max_coeff":1.000001},
                                 "負荷時間スラック変数合計最小化2":{"min_coeff":0,"max_coeff":1.0},
                                 "7桁在庫月数合計最小化":{"min_coeff":0,"max_coeff":1.1},
                                 "生産イベント月数最大化":{"min_coeff":0.999,"max_coeff":1000},
                                 "7桁基準在庫月数Max以下制約違反回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                "7桁基準在庫月数Min以上制約違反回数最小化":{"min_coeff":0,"max_coeff":1.1},
                                "年度末7桁基準在庫月数Min以上制約違反回数最小化":{"min_coeff":0,"max_coeff":1.1},}
        
        
        
    
    def run_direct_optimization(self,obj_name,constraint_list,
                                additional_constraint_dict,pre_solution=None,
                                timelimit=300,
                                big_M_weight=2.0,mode="normal"):
        """
        直接最適化を実行する関数
        
        mode:initial,normal,relaxing
        initial:最初の最適化実行
        normal:通常の最適化実行
        relaxing:最適解がない場合の最適化実行(負荷時間スラック変数ありで最適化実行)
        
        
        """
        DD = DirectOptimizer(self.all_params_dict,obj_name,
                             constraint_list,
                             additional_constraint_dict,
                             timelimit,
                             pre_solution,
                             big_M_weight,
                             mode)
        
        variables, problem,solver = DD.main()
        
        status = pulp.LpStatus[problem.status]        #LpStatusで状態を文字列に変換
        objective_value = problem.objective.value()   #目的関数値
        
        
        solution = {v.name: v.value() for v in problem.variables()}   #解の保存
        
        # 解の書き出し
        # df = pd.DataFrame(list(solution.items()), columns=["Variable", "Value"])
        # df.to_excel(f"solution_{obj_name}.xlsx", index=False)
        

        return variables, problem, status, objective_value, solution,solver
        
        
        
        
    
    def run_feasibility_optimization(self,obj_name,additional_constraint_dict,pre_solution=None):
        """
        実行可能性判定問題を解く
        
        一番最初でもこっちで解く。解けなかったらその時点で終了。
        
        """
        obj_constraint_name = self.obj_constraint_dict[obj_name]["constraint_name"]
        init_num = self.obj_constraint_dict[obj_name]["init_num"]
        
        FO = FeasibilityOptimizer(self.all_params_dict,additional_constraint_dict,
                                  obj_name,obj_constraint_name,init_num,
                                  self.timelimit,pre_solution)
        variables, problem, obj_num, solver = FO.main()
        
        status = pulp.LpStatus[problem.status]  # LpStatusで状態を文字列に変換
        objective_value = obj_num
        
        
        solution = {v.name: v.value() for v in problem.variables()}   #解の保存
        
        
        return variables, problem, status, objective_value, solution
    
    

        
    
    
    def get_constraint_limit(self,objective_function_name,
                             objective_value,additional_constraint_dict):
        
        
        additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = \
        abs(objective_value)*self.limit_coeff_dict[objective_function_name]["min_coeff"]    #制約条件追加
        
        additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = \
        abs(objective_value)*self.limit_coeff_dict[objective_function_name]["max_coeff"]    #制約条件追加    #制約条件追加
        
        
        
        if objective_function_name == "負荷時間スラック変数合計最小化" and objective_value == 0:
            #10時間余裕を持たせる。
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = 0
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = objective_value*1.1
        
        if objective_function_name == "余力時間最小化":
            #負の値でああったり正の値である可能性があることに注意。
            #どのようにMinMaxの幅をとるか？
            
            if objective_value < 0:
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = \
                objective_value*10000000
            
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = \
                objective_value*0.9
            
            
            if objective_value >= 0:
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = \
                objective_value*0.0
            
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = \
                objective_value*1.1
            
            

        #目的関数が0の場合は、定数倍しても0なので別枠で管理
        if objective_function_name != "負荷時間スラック変数合計最小化" and objective_function_name != "余力時間最小化" and objective_value == 0:
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = 0     #制約条件追加
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = 1     #制約条件追加
        
        
        
    
        
        
        # #スラック変数はめちゃ頑張っても1800時間くらい。上限は3000とする。
        #elif objective_function_name == "負荷時間スラック変数合計最小化":
        #    additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = 0     #制約条件追加
        #    additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = abs(objective_value)*1.1 #制約条件追加
        

        
        
        
        return additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"],\
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"]
    
    
    
    
    
    
    
    
    def output_solution(self,solution,objective_function_name):
        """
        
        解をファイルで出力
        
        """
        # 現在の日付と時間を取得
        current_time = datetime.now()
        # ファイル名に使える形式で文字列を作成
        unique_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        # 解をpickleファイルに保存
        with open(f"{SOLUTION_DIR}/solution_{unique_string}_{objective_function_name}.pkl", "wb") as f:
            pickle.dump(solution, f)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def update_additional_constraint(self,additional_constraint_dict,solution_dict,objective_value_dict,
                                     objective_function_name,objective_value):
        """
        制約条件の更新
        

        Args:
            additional_constraint_dict (_type_): _description_
            solution_dict (_type_): _description_
            objective_value_dict (_type_): _description_
            solution (_type_): _description_
            objective_function_name (_type_): _description_
            objective_value (_type_): _description_

        Returns:
            _type_: _description_
        """
           
        constraint_name = self.obj_constraint_dict[objective_function_name]["constraint_name"]
        additional_constraint_dict[constraint_name] = {}

        
        #目的関数が0の場合は、定数倍しても0なので別枠で管理
        if objective_value == 0:
            additional_constraint_dict[constraint_name]["min"] = 0     #制約条件追加
            additional_constraint_dict[constraint_name]["max"] = 1     #制約条件追加
        else:    
            additional_constraint_dict[constraint_name]["min"],\
            additional_constraint_dict[constraint_name]["max"] = self.get_constraint_limit(objective_function_name,
                                                                                            objective_value,
                                                                                            additional_constraint_dict)
        
            

        #TODO 24/12/06  最小化問題として解く場合はここ変更必要かも
        if objective_function_name == "超過月末在庫量最小化":
            #この目的関数に関しては最小化もしているし、プラスもマイナスも取りうる。符号が逆転しているのはそうなので
            #とりあえずそこだけ実装
            
            additional_constraint_dict[constraint_name]["min"] = -objective_value     #制約条件追加
            additional_constraint_dict[constraint_name]["max"] = -objective_value     #制約条件追加
            
            objective_value_dict[objective_function_name] = -objective_value
        
        
        
        return additional_constraint_dict,solution_dict,objective_value_dict
    
    
    
        
    def insert_item(self,dictionary, key, value, position=0):
        # Convert the dictionary to a list of tuples (key-value pairs)
        items = list(dictionary.items())
        # Insert the new key-value pair at the specified position
        items.insert(position, (key, value))
        # Convert back to a dictionary
        return dict(items)
        
    
    
    def find_optimal_solution_loop(self,objective_function_name,additional_constraint_dict,
                                   pre_solution,mode,max_iter=10):
        """
        statusがoptimalになるまで最適化を繰り返す関数
        

        Args:
            objective_function_name (_type_): _description_
            additional_constraint_dict (_type_): _description_
            pre_solution (_type_): _description_
            mode (_type_): _description_

        Returns:
            _type_: _description_
        """
        
        temp_big_M_weight = 2.0
        temp_timelimit_weight = 1.0
        #TODO このループの最大時間も必要？？15分とか？必要そう。。。
        
        solution = pre_solution
        
        start = time.time()
        for i in range(max_iter):
        
            #直接最適化問題として解く
            variables, problem, status, \
            objective_value,solution,solver = self.run_direct_optimization(obj_name=objective_function_name,
                                                                    constraint_list=self.all_params_dict["constraint_list"],
                                                                    additional_constraint_dict=additional_constraint_dict,
                                                                    big_M_weight=temp_big_M_weight,
                                                                    timelimit=self.timelimit*temp_timelimit_weight,
                                                                    pre_solution=solution,
                                                                    mode=mode)
            
            
            
            
            
            #最適解見つかったら終了
            if status == "Optimal":
                break
            
            if status != "Optimal":                               #infeasible,unbound,not solvedの場合
                temp_big_M_weight = temp_big_M_weight*2           #big_M_weightを2倍にして再計算
                temp_timelimit_weight = temp_timelimit_weight*2   #timelimitを2倍にして再計算
                end = time.time()
                if end - start > 300:
                    break
            
        return variables, problem, status, objective_value, solution
                
                
    
    
    
    def normal_simulation_mode(self,additional_constraint_dict,solution_dict,objective_value_dict,
                               init_solution):
        """
        一番最初の最適化実行で実行した際に、最適解アリになった場合のモード
        
        
        """
        
        solution_list = [init_solution]
        
        for ranking, objective_function_name in self.obj_priority_dict.items():
            progressHolder = st.empty()
            progressHolder.info("【優先度"+str(ranking)+"位】 "+ objective_function_name + " 計算中...")           #計算中の目的関数名を表示
            start = time.time()
            
        
            variables, problem, status, objective_value, solution = self.find_optimal_solution_loop(objective_function_name,
                                                                                                    additional_constraint_dict,
                                                                                                    pre_solution=solution_list[-1],
                                                                                                    mode="normal")
            
            #最適解が見つかったのなら、制約条件化し次の目的関数の最適化へ。
            if status == "Optimal":
                end = time.time()
                progressHolder.success(f'【優先度{str(ranking)}位】 {objective_function_name} 計算終了！！  ＜最適解＞  {str(round(end-start,2))}秒')           #目的関数名を表示
                solution_list.append(solution)                                                         #解の保存（最後尾）
                solution_dict[ranking] = [variables, problem, status, objective_value, solution]       #解の保存
                
                #制約条件の更新
                self.update_additional_constraint(additional_constraint_dict,solution_dict,objective_value_dict,
                                                  objective_function_name,objective_value)
                
                self.output_solution(solution,objective_function_name)             #解のファイル書き出し
                
                
                
            
            
            #最適解見つからなかったら、この目的関数はパスする。制約条件化もしない。
            if status != "Optimal":
                progressHolder.warning(f'【優先度{str(ranking)}位】 {objective_function_name} 計算できませんでした。')
            
            

        return variables, problem, status, objective_value_dict



    



    
    def relaxing_simulation_mode(self,progress):
        """
        一番最初の最適化実行（目的関数は定数）で実行した際に、最適解なしになった場合
        
        """
        
        
        #制約条件の変更
        temp_constraint_list = self.all_params_dict["constraint_list"].copy()
        temp_constraint_list.remove("負荷時間以下制約")             #負荷時間以下制約を外す
        #temp_constraint_list.append('基準在庫月数Min以上制約')      #基準在庫月数Min以上制約を追加
        temp_constraint_list.append("負荷時間以下スラック付き制約")  #負荷時間以下スラック付き制約を追加
        
        
        
        
        #目的関数の追加
        temp_obj_priority_dict = self.obj_priority_dict.copy()
        temp_obj_priority_dict = self.insert_item(temp_obj_priority_dict,
                                                  key=0,
                                                  value="負荷時間スラック変数合計最小化",
                                                  position=0)
        

        
        
        #最初に追加したい。
        #temp_obj_priority_dict[-1] = "基準在庫Min超在庫量最小化"   #最後に追加したい。
        
        
        
        additional_constraint_dict = {}               #以前で目的関数だったものが制約条件になったものの辞書（キー制約名、バリュー：目的関数値(の、絶対値)）
        objective_value_dict = {}
        solution_dict={}
        
        
        solution = self.initial_solution
        
        
        
        
        #まずはそもそも解があるのか確認
        temp_weight = 3.0
        for i in range(50):
            
            print("temp_weight",temp_weight)
            
            obj_name=None
            obj_name = "負荷時間スラック変数合計最小化"
            #obj_name = "保全月合計ドープ数最小化"
            
            
            variables, problem, status, objective_value,solution = self.run_direct_optimization(obj_name=obj_name,
                                                                                                constraint_list=temp_constraint_list,
                                                                                                additional_constraint_dict=additional_constraint_dict,
                                                                                                pre_solution=solution,
                                                                                                big_M_weight=temp_weight,
                                                                                                mode="relaxing")
            #最適解がなかった場合。
            if status != "Optimal":
                temp_weight = temp_weight*2
            
            if status == "Optimal":
                break
            
        
        if status != "Optimal":
            st.write("どんなMでも無理でした。")
        
                
                
        for ranking, objective_function_name in temp_obj_priority_dict.items():
            progressHolder = st.empty()
            progressHolder.info("【優先度"+str(ranking)+"位】 "+ objective_function_name + " 計算中...")           #計算中の目的関数名を表示
            start = time.time()
            
            
            #直接最適化問題として解く
            if self.obj_constraint_dict[objective_function_name]["type"] == "direct":
                variables, problem, status, \
                objective_value,solution = self.run_direct_optimization(obj_name=objective_function_name,
                                                                        constraint_list=temp_constraint_list,
                                                                        additional_constraint_dict=additional_constraint_dict,
                                                                        pre_solution=solution,
                                                                        big_M_weight=temp_weight,
                                                                        mode="relaxing")
            
            additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]] = {}

        
            #解の保存
            solution_dict[ranking] = [variables, problem, status, objective_value]
            
            #TODO 本当はstatus=0だったらもう一度続きから計算して最適解出るまで。。みたいにやりたいが。
            if (status == "Optimal") or (status == "Not Solved"):
                
                
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"],\
                additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = self.get_constraint_limit(objective_function_name,
                                                                                                                                                    objective_value,
                                                                                                                                                    additional_constraint_dict)
                
                
                # 現在の日付と時間を取得
                current_time = datetime.now()
                # ファイル名に使える形式で文字列を作成
                unique_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
                
                # 解をpickleファイルに保存
                with open(f"./solution/solution_{unique_string}_{objective_function_name}.pkl", "wb") as f:
                    pickle.dump(solution, f)
                
                
                objective_value_dict[objective_function_name] = abs(objective_value)       #最小化しているものについては符号が逆転している
                
                
                
                #TODO 24/12/06  最小化問題として解く場合はここ変更必要かも
                if objective_function_name == "超過月末在庫量最小化":
                    #この目的関数に関しては最小化もしているし、プラスもマイナスも取りうる。符号が逆転しているのはそうなので
                    #とりあえずそこだけ実装
                    
                    additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["min"] = -objective_value     #制約条件追加
                    additional_constraint_dict[self.obj_constraint_dict[objective_function_name]["constraint_name"]]["max"] = -objective_value     #制約条件追加
                    
                    objective_value_dict[objective_function_name] = -objective_value
            
            
            #いろいろあって途中でinfeasible,Unbounded Undefinedになった場合
            if (status != "Optimal") and (status == "Not Solved"):
                
                #if status == "Infeasible":
                    
                
                
                
                
                
                
                
                #TODO infeasibleになったときの処理
                progressHolder.warning(f'【優先度{str(ranking)}位】 {objective_function_name} 計算できませんでした。')    #計算中の目的関数名を表示
                progress.update(label="最適化計算終了！", state="complete", expanded=False)
                
                return variables, problem, status, objective_value_dict
            
            
            end = time.time()
            if status == "Optimal":
                progressHolder.success(f'【優先度{str(ranking)}位】 {objective_function_name} 計算終了！！  ＜最適解＞　{str(round(end-start,2))}秒')           #計算中の目的関数名を表示
            if status == "Not Solved":
                progressHolder.success(f'【優先度{str(ranking)}位】 {objective_function_name} 計算終了！！  ＜準最適解＞　{str(round(end-start,2))}秒')      #計算中の目的関数名を表示
                
        
        # 現在時刻と乱数を組み合わせてユニークな文字列を生成
        unique_string = f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        # 解をpickleファイルに保存
        with open(f"{SOLUTION_DIR}/solution_{unique_string}.pkl", "wb") as f:
            pickle.dump(solution, f)

        return variables, problem, status, objective_value_dict
    

    
    
        
    
    
    def initial_simulation_mode(self,objective_function_name,additional_constraint_dict,init_solution):
        """
        そもそも最適解があるかチェックする関数
        
        
        """
        
        variables, problem, status, objective_value, solution = self.find_optimal_solution_loop(objective_function_name,
                                                                                                additional_constraint_dict,
                                                                                                pre_solution=init_solution,
                                                                                                mode="normal",
                                                                                                max_iter=2)
        
        return variables, problem, status, objective_value, solution
    
    
    
    
    
    
    
    
    
    def main(self):
        """
        最初の目的関数で解けたのであれば途中で最適解無しになる可能性はない
        最初の目的関数の状態で解ければOK解けなければ計算終了としたい。
        
        
        定式化に際し重複部分はこちらのクラスに書こうかなと思ったが、ゆくゆく
        基準在庫とかでやりだしたときに冗長な定式化にならざるを得なくなる不安があるため、
        定式化部分はここには書かない。将来的に共通化できない可能性あるから。
        
        ファイルの書き出しにかんするところはここに書いた方がいいかも。
        
        
        """

        
        additional_constraint_dict = {}               #以前で目的関数だったものが制約条件になったものの辞書（キー制約名、バリュー：目的関数値(の、絶対値)）
        objective_value_dict = {}
        solution_dict={}                              #解の保存
        
        
        
        with st.status(f'最適化計算中です。1つの目的関数の計算時間の上限は{self.timelimit}秒程度にしています。', expanded=True) as progress:
            
            #まずはそもそも最適解があるのか確認
            variables, problem, status, objective_value,solution = self.initial_simulation_mode(objective_function_name="生産イベント月数最大化",
                                                                                                additional_constraint_dict=additional_constraint_dict,
                                                                                                init_solution=self.initial_solution)

            
            
            #最適解があった場合
            if status ==  "Optimal":
                progress.info("負荷時間が足りない工場・月はありませんでした。通常通り最適化を実行します。")
                variables, problem, status, objective_value_dict = self.normal_simulation_mode(additional_constraint_dict,solution_dict,
                                                                                               objective_value_dict,solution)
            
            #最適解がなかった場合
            if status != "Optimal":
                progress.info("負荷時間が足りない工場・月がある可能性があります。最小限+αの負荷時間のマイナスを許容し最適化を実行します。")

                variables, problem, status, objective_value_dict = self.relaxing_simulation_mode(progress)
    
            progress.update(label="最適化計算終了！", state="complete", expanded=False)
                    
        return variables, problem, status, objective_value_dict
                
            
            
            
            
            
            
            