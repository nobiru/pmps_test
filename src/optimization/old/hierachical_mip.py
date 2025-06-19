import pulp
import datetime
import pickle
from index_generator import CommonProcess
from mip_core_2 import MipCore
import streamlit as st
import time



class HierachicalMip():
    """
    混合整数計画法実装
    
    
    
    """
    def __init__(self,all_params_dict):
        

        
        
        self.logfile_dir = "./定式化log/"
        
        self.all_params_dict = all_params_dict
        
        self.obj_priority_dict = all_params_dict["obj_priority_dict"]             #目的関数(優先度つき)
        
        
        #目的関数と制約条件のマッピング
        self.all_obj_constraint_mapping = {"長時間ドープ切り替え回数最小化":"長時間ドープ切り替え回数一致制約",
                                           "SAZMA系品種連続生産月数最大化":"SAZMA系品種連続生産月数一致制約",
                                           "基準在庫月数Min以上制約違反回数最小化":"基準在庫月数Min以上制約違反回数一致制約",
                                            "基準在庫月数Max以下制約違反回数最小化":"基準在庫月数Max以下制約違反回数一致制約",
                                           "優先SVA品種の合計生産量を最大化":"優先SVA品種の合計生産量一致制約",
                                           "サブ品種の合計生産量最小化":"サブ品種の合計生産量一致制約",
                                           "合計生産時間最大化":"合計生産時間一致制約",
                                           "超過月末在庫量最小化":"超過月末在庫量一致制約",
                                           "レア品種の合計生産回数最小化":"レア品種の合計生産回数一致制約",
                                           "負荷時間以下制約違反量最小化":"負荷時間以下制約違反量一致制約",
                                           "保全月合計ドープ数最小化":"保全月合計ドープ数一致制約",
                                           "基準在庫月数Min超在庫量最小化（原因調査用）":"基準在庫月数Min超在庫量一致制約",
                                           "メインドープによる立上・立下回数最大化":"メインドープによる立上・立下回数一致制約"}  #TODO Min超えか0以上越えか決める。
        
        self.timelimit = all_params_dict["timelimit"]
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
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
        solution_dict={}
        
        
        
        with st.status(f'最適化計算中です。1つの目的関数の計算時間の上限は{self.timelimit}秒程度にしています。', expanded=True) as progress:
            for ranking, objective_function_name in self.obj_priority_dict.items():
                
                progressHolder = st.empty()
                progressHolder.info("【優先度"+str(ranking)+"位】 "+ objective_function_name + " 計算中...")           #計算中の目的関数名を表示
                
                start = time.time()
                
                prod_amount_dict,sales_amount_dict,status,objective_value,switch_time_dict,inter_switch_time_head_dict, inter_switch_time_tail_dict= MipCore(self.all_params_dict,
                                                                                    objective_function_name,
                                                                                    additional_constraint_dict,
                                                                                    timelimit=self.timelimit).main()    #最適化実施
                
                
                #解の保存
                solution_dict[ranking] = [prod_amount_dict,sales_amount_dict,status,objective_value,switch_time_dict,
                                          inter_switch_time_head_dict, inter_switch_time_tail_dict]
                
                
                
                #一個目の目的関数で最適解なかったら(infeasible)その時点で終了。#TODOステータスは-3~1まであるのですべて捕捉できるように。
                if ((ranking==1) & (status == -1)) or ((ranking==1) & (status == -3)) or ((ranking==1) & (status == -2)):
                    progressHolder.warning("【優先度"+str(ranking)+"位】 "+ objective_function_name + " 最適解なし")           #計算中の目的関数名を表示
                    progress.update(label="最適解無し", state="error", expanded=False)
                    return prod_amount_dict,sales_amount_dict,status,objective_value,objective_value_dict,switch_time_dict,inter_switch_time_head_dict, inter_switch_time_tail_dict
                
                
                
                #TODO 本当はstatus=0だったらもう一度続きから計算して最適解出るまで。。みたいにやりたいが。
                if (status == 1) or (status == 0):
                    additional_constraint_dict[self.all_obj_constraint_mapping[objective_function_name]] = abs(objective_value)     #制約条件追加
                    
                    objective_value_dict[objective_function_name] = abs(objective_value)       #最小化しているものについては符号が逆転している
                    
                    if objective_function_name == "超過月末在庫量最小化":
                        #この目的関数に関しては最小化もしているし、プラスもマイナスも取りうる。符号が逆転しているのはそうなので
                        #とりあえずそこだけ実装
                        
                        
                        additional_constraint_dict[self.all_obj_constraint_mapping[objective_function_name]] = -objective_value     #制約条件追加
                        objective_value_dict[objective_function_name] = -objective_value
                
                
                #いろいろあって途中でinfeasibleになった場合
                if ((ranking!=1) & (status == -1)) or ((ranking!=1) & (status == -3)) or ((ranking!=1) & (status == -2)):
                    solution = solution_dict[ranking-1]
                    prod_amount_dict = solution[0]
                    sales_amount_dict = solution[1]
                    status = solution[2]
                    objective_value = solution[3]
                    switch_time_dict = solution[4]
                    inter_switch_time_head_dict = solution[5]
                    inter_switch_time_tail_dict = solution[6]
                    
                    progressHolder.warning(f'【優先度{str(ranking)}位】 {objective_function_name} 計算できませんでした。')           #計算中の目的関数名を表示
                    progress.update(label="最適化計算終了！", state="complete", expanded=False)
                    return prod_amount_dict,sales_amount_dict,status,objective_value,objective_value_dict,switch_time_dict,inter_switch_time_head_dict, inter_switch_time_tail_dict
                
                
                
                
                end = time.time()
                if status == 1:
                    progressHolder.success(f'【優先度{str(ranking)}位】 {objective_function_name} 計算終了！！  ＜最適解＞　{str(round(end-start,2))}秒')           #計算中の目的関数名を表示
                if status == 0:
                    progressHolder.success(f'【優先度{str(ranking)}位】 {objective_function_name} 計算終了！！  ＜準最適解＞　{str(round(end-start,2))}秒')           #計算中の目的関数名を表示
                    
            progress.update(label="最適化計算終了！", state="complete", expanded=False)
                    
                    
        #st.write(status)
        return prod_amount_dict,sales_amount_dict,status,objective_value,objective_value_dict, switch_time_dict,inter_switch_time_head_dict, inter_switch_time_tail_dict
                
            
            
            
            
            
            
            