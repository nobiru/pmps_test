import pulp
from constraints_catalog import ConstraintsCatalog
from objective_function_catalog import ObjectiveFunctionCatalog
from model_variables import ModelVariables
import time
import random
import streamlit as st
import pandas as pd
from datetime import datetime

from pathlib import Path

import os
import glob

from output_config import SOLVER_TEMP_DIR



class DirectOptimizer():
    """
    ふつうに最適化問題を解くためのクラス（実行可能性判定問題としては解かない）
    
    """
    def __init__(self,all_params_dict,obj_name,
                 constraint_list,
                 additional_constraint_dict,timelimit,
                 pre_solution,
                 big_M_weight=1.0,mode="normal"):
        
        print(mode)
        
        self.constraint_list = constraint_list                                                  #今回のシミュで共通して使う制約条件の名前リスト
        self.additional_constraint_dict = additional_constraint_dict                           #追加制約条件名の辞書(key:制約名、value:目的関数値（これと等しいとして制約条件とする）)
        self.obj_name = obj_name                                                               #目的関数名
        self.timelimit = timelimit                                                             #最適化時間制限
        
        self.all_params_dict = all_params_dict
        
        self.pre_solution = pre_solution                                                       #前階層の解を初期解として使う
        
        
        self.big_M_weight = big_M_weight                                                       #big-M法の重み
        self.mode = mode                                                                       #normal 又は relaxing
        
        
        
        self.base_gaprel = 0.01                                #最適解の許容誤差の基本値(1％)
        
        self.init_gaprel = 0.5                                 #最適解の許容誤差の初期値(100%):最適解がそもそもあるのかチェックする際に使う
        
        
        
        
        
        self.gaprel = 0.01
        if obj_name == "余力時間最小化" or obj_name == "余力時間最小化2":
            self.gaprel = 0.00000000001
            self.timelimit = None
        
        
        if obj_name == "負荷時間スラック変数合計最小化":#負荷時間のスラック変数は本当に小さい方がいいため。
            self.gaprel = 0.00000001
            self.timelimit =None
            
        if obj_name == "優先SVA品種の合計生産量を最大化":   #そもそもの数字がデカいので、gaprelを小さくしても大勢に影響ない。計算高速化の観点
            self.gaprel = 0.01
            
        if obj_name == "長時間ドープ切替工場合計切替時間最小化":
            self.gaprel = 0.01    
        

        
        
        if self.obj_name is None:
            print("解けるかどうかチェック")
            self.timelimit = 10000
        
        
    
    def set_initial_value_common(self,variable,low_bound,binary_flag=False):
        """
        初期解の指定
        
        """
        for key in variable.keys():
            
            
            init_value = self.pre_solution[str(variable[key])]    #strにする必要あり！！！！！
            
            
            if binary_flag==True:
                init_value = int(round(init_value))   
                if init_value > 1:
                    init_value = int(1)
                if init_value < 0:
                    init_value = int(0)
                
            
            if init_value < low_bound:
                init_value = low_bound
            
            
            
                
            
            variable[key].setInitialValue(init_value)
            
            
            
            
            
    
    
    def set_initial_value(self):
        if self.pre_solution is not None:
            self.set_initial_value_common(self.variables.x,0)
            self.set_initial_value_common(self.variables.y,0)
            self.set_initial_value_common(self.variables.z,0)
            self.set_initial_value_common(self.variables.delta,0,True)
            self.set_initial_value_common(self.variables.subdelta,0,True)
            self.set_initial_value_common(self.variables.delta_z,0,True)
            self.set_initial_value_common(self.variables.subdelta_z,0,True)
            self.set_initial_value_common(self.variables.delta_mz,0,True)
            self.set_initial_value_common(self.variables.subdelta_mz,0,True)
            
            
            self.set_initial_value_common(self.variables.delta_7_z,0,True)
            self.set_initial_value_common(self.variables.subdelta_7_z,0,True)
            self.set_initial_value_common(self.variables.delta_7_mz,0,True)
            self.set_initial_value_common(self.variables.subdelta_7_mz,0,True)
            
            
            
            

            
            self.set_initial_value_common(self.variables.switch_time,-50)
            
            self.set_initial_value_common(self.variables.dope1_flag,0,True)
            self.set_initial_value_common(self.variables.dope2_flag,0,True)
            self.set_initial_value_common(self.variables.dope3_flag,0,True)
            
            self.set_initial_value_common(self.variables.group1_flag,0,True)
            self.set_initial_value_common(self.variables.group2_flag,0,True)
         
         
            #if "最大化" in self.obj_name:
            self.set_initial_value_common(self.variables.all_prod_flag,0,True)
            
            self.set_initial_value_common(self.variables.inter_switch_1to2_flag,0,True)
            self.set_initial_value_common(self.variables.inter_switch_2to1_flag,0,True)
            
            self.set_initial_value_common(self.variables.inter_switch_time_head,-0.01)
            self.set_initial_value_common(self.variables.inter_switch_time_tail,-0.01)
            
            
            if self.mode == "relaxing":
                self.set_initial_value_common(self.variables.slack,0)
            


    
    def define_variables(self):
        """
        変数の定義
        
        """
        MV = ModelVariables(self.all_params_dict,
                            big_M_weight=self.big_M_weight,
                            mode=self.mode)
        MV.define_variables()
        self.variables = MV
        
    
    def set_initialvalue(self,pre_solution):
        """
        初期解の設定

        Args:
            pre_solution (_type_): _description_
        """
        for key in self.variables.x:
            self.variables.x[key].setInitialValue(pre_solution)
            
        #solution = {v.name: v.value() for v in problem.variables()}   #解の保存
    
    

    def define_constraints(self):
        """
        制約条件の定義
        
        
        """
        
        CC = ConstraintsCatalog(self.variables,self.problem)
        CC.define_constraints(self.constraint_list,
                              self.additional_constraint_dict)
        self.problem = CC.problem
        
    
    def define_objective_function(self):
        """
        目的関数の定義
        
        """
        OF = ObjectiveFunctionCatalog(self.variables,self.problem)
        OF.define_objective_function(self.obj_name)
        self.problem = OF.problem


    
    def solve_problem(self):
        """
        最適化を実行
        
        """
        
        if self.pre_solution is not None:
            #initial_solution_str = self.get_initial_solution_str()
            options = [
        'feasibilityPump on',     # FeasibilityPumpを有効化
        'set emphasis mip 1',     # 実行可能性重視
        'heuristicsOnOff on',      # 他のヒューリスティクスも有効化
         #f'initialSolve {self.pre_temp_file_name}'   # 初期解を設定
        ]
        
        else:
            options = [
        'feasibilityPump on',     # FeasibilityPumpを有効化
        'set emphasis mip 1',     # 実行可能性重視
        'heuristicsOnOff on',      # 他のヒューリスティクスも有効化
            ]
            #warmstart = False
        
        #options =["presolve off",]
        warmstart=True    #Trueにすると、mstファイルが作成され、初期解が利用される。
        
        
        #self.solver = pulp.PULP_CBC_CMD(timeLimit=self.timelimit,
        #                           gapRel=self.gaprel,
        #                           options=options,
        #                           warmStart=warmstart,
        #                           msg=True,
        #                           keepFiles=True)
        
        self.solver = pulp.SCIP()
        
        
        loaded_solution = {v.name: v.value() for v in self.problem.variables()}   #解の保存
        
        #df = pd.DataFrame(list(loaded_solution.items()), columns=["Variable", "Value"])
        #df.to_excel(f"solution_{self.obj_name}_読み込まれた初期解.xlsx", index=False)
        
        
        
        
        self.status = self.problem.solve(self.solver)
        print(self.status)
        print(pulp.LpStatus[self.status])
    
    
    
    
    
    def opimization_flow(self):
        """
        1回目のシミュレーションで最適化できた場合。
        
        """
        self.define_variables()                                  #変数を定義
        if self.pre_solution is not None:
            self.set_initial_value()
        self.define_constraints()                                #制約条件を定義
        self.define_objective_function()                         #目的関数を定義
        self.solve_problem()                                     #最適化を実行
        self.delete_temp_files()                                 #ソルバーが吐き出すファイルを削除
    
    
    
    
    
    def delete_temp_files(self):
        """
        ソルバーが吐き出すファイルを削除する
        """
        # 削除したい拡張子のリスト
        extensions_to_delete = ['.sol', '.mst', '.mps']
        
        # 指定した拡張子のファイルを削除
        for ext in extensions_to_delete:
            files_to_delete = glob.glob(os.path.join(SOLVER_TEMP_DIR, f'*{ext}'))
            for file_path in files_to_delete:
                os.remove(file_path)

    
    
    def main(self):
        
        
        # 現在の日付と時間を取得
        current_time = datetime.now()
        # ファイル名に使える形式で文字列を作成
        current_string = current_time.strftime("%Y-%m-%d_%H-%M-%S-%f")
        relative_path = os.path.relpath(SOLVER_TEMP_DIR, start=Path.cwd())    #相対パスに変換
        
        
        solver_temp_name =  f"{relative_path}/solver_temp_{current_string}"
        
        
        if self.obj_name is None:
            self.problem = pulp.LpProblem(name=solver_temp_name, sense=pulp.LpMaximize)        #最大化問題
        
        else:
            if "最大化" in self.obj_name:
                self.problem = pulp.LpProblem(name=solver_temp_name, sense=pulp.LpMaximize)        #最大化問題
            if "最小化" in self.obj_name:
                self.problem = pulp.LpProblem(name=solver_temp_name, sense=pulp.LpMinimize)        #最小化問題
        
        
        
        self.opimization_flow()        #変数定義、定式化、求解
        
        
        
        return self.variables, self.problem, self.solver