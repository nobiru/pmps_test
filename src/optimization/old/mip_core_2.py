import pulp
import datetime
import pickle
from index_generator import CommonProcess

class MipCore():
    """
    混合整数計画法実装
    
    
    
    """
    def __init__(self,all_params_dict,obj_name,additional_constraint_dict,timelimit=60):
        
        self.jissui_month_list = all_params_dict["jissui_month_list"]
        self.split_month_list = self.get_split_month_list(self.jissui_month_list)
        
        
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
        self.basic_stock_max_dict = all_params_dict["basic_stock_max_dict"]
        self.ave_sales_info_dict = all_params_dict["ave_sales_info_dict"]
        
        self.constraint_plant_dict = all_params_dict["constraint_plant_dict"]
        
        self.month_type_dict = all_params_dict["month_type_dict"]
        self.maint_hour_dict = all_params_dict["maint_hour_dict"]   #保全時間の辞書
        self.maint_month_list = all_params_dict["maint_month_list"]  #保全月のリスト
        
        
        self.achieve_rate_dict = all_params_dict["achieve_rate_dict"]
        self.all_index = all_params_dict["all_index"]
        self.M = self.get_big_M()
        self.m = self.get_small_m()                                #生産量としてありえない小さい値(本当は計算で求めたい。ちょっと大きすぎるケースあるかも)
        self.plant_prod_dict = all_params_dict["plant_prod_dict"]
        self.plant_list = list(self.plant_prod_dict.keys())            #TODO これconstraint_plant_listにすればいける？
        self.prod_plant_dict = all_params_dict["prod_plant_dict"]
        self.all_prod_list = list(self.cs_dict.keys()) 
        #self.objective_func_dict = all_params_dict["objective_func_dict"]    #TODO書き換え
        
        self.switch_coeff_dict = all_params_dict["switch_coeff_dict"]
        self.inter_switch_coeff_dict = all_params_dict["inter_switch_coeff_dict"] #注目している月に生産品種しかないケース
        
        self.inter_switch_maint_head_coeff_dict = all_params_dict["inter_switch_maint_head_coeff_dict"] #注目している月に保全前期があるケース
        self.inter_switch_maint_tail_coeff_dict = all_params_dict["inter_switch_maint_tail_coeff_dict"] #注目している月に保全後期があるケース
        
        
        self.main_dope_prod_dict = all_params_dict["main_dope_prod_dict"]   #メインドープ、メイン品種の辞書
        
                  
        self.plant_month_index = all_params_dict["plant_month_index"]
        

        self.ave_month_num = self.ave_sales_info_dict["ave_month_num"]       #在庫月数計算時に販売量何か月平均するか
        self.ave_sales_mode = self.ave_sales_info_dict["ave_sales_mode"]     #平均するときに当月を含むかどうか（含む・含まない）
        
        self.ave_month_dict = self.get_ave_month_dict()
        self.constraint_list = all_params_dict["constraint_list"]                              #今回のシミュで使う制約条件の名前リスト
        
        self.all_constraint_functions = {#"負荷時間一致制約":self.fuka_equal_constraint,
                                         "負荷時間以下制約":self.fuka_less_constraint_5,
                                         #"負荷時間以下制約":self.fuka_less_constraint_2,
                                         "合計販売量一致制約":self.sum_sales_constraint,
                                         "月末在庫0以上制約":self.not_minus_stock_constraint,
                                         "最低生産回数以上制約":self.num_production_constraint_min,
                                         "最大生産回数以下制約":self.num_production_constraint_max,
                                         "基準在庫月数Min以上制約":self.within_basic_stock_constraint_min,
                                         "基準在庫月数Max以下制約":self.within_basic_stock_constraint_max,
                                         "最低連続生産時間以上制約":self.min_continuous_constraint,
                                         "確定生産量一致制約":self.finalized_prod_constraint,
                                         "確定販売量一致制約": self.finalized_sales_constraint,
                                         }
        
        self.constraint_period_dict = all_params_dict["constraint_period_dict"]      #制約期間指定できるものの辞書
        
        self.single_factory_prod_list = all_params_dict["single_factory_prod_list"]
        
        
        self.rare_prod_list = all_params_dict["rare_prod_list"]
        self.sub_prod_list = all_params_dict["sub_prod_list"]
        self.priority_sva_prod_list = all_params_dict["priority_sva_prod_list"]
        
        
        self.prod_capacity_dict = all_params_dict["prod_capacity_dict"]      #生産キャパシティ
        
        
        self.logfile_dir = "./定式化log/"
        
        
        
        self.obj_name = obj_name                 #目的関数の名前
        self.additional_constraint_dict = additional_constraint_dict   #追加の制約条件
        
        #もともとは目的関数だが、階層的最適化をするにあたり、制約条件として使うとき
        self.all_obj_constraint_functions = {"長時間ドープ切り替え回数一致制約":self.long_dope_switch_constraint,
                                             "SAZMA系品種連続生産月数一致制約":self.sazma_continuous_constraint,
                                            "基準在庫月数Min以上制約違反回数一致制約":self.shortage_stock_constraint,
                                            "基準在庫月数Max以下制約違反回数一致制約":self.over_stock_constraint,
                                             "優先SVA品種の合計生産量一致制約":self.w_sw_constraint,
                                             "サブ品種の合計生産量一致制約":self.sub_prod_constraint,
                                             "合計生産時間一致制約":self.prod_time_constraint,
                                             "超過月末在庫量一致制約":self.over_stock_amount_constraint,
                                             "レア品種の合計生産回数一致制約":self.prod_num_constraint,
                                             "負荷時間以下制約違反量一致制約":self.over_fuka_constraint,
                                             "保全月合計ドープ数一致制約":self.maintenance_dope_num_constraint,
                                             "基準在庫月数Min超在庫量一致制約":self.almost_touch_min_stock_constraint,
                                             "メインドープによる立上・立下回数一致制約":self.main_dope_num_constraint}
        
        
        self.timelimit = timelimit                     #最適化計算の
        
        
        
        ##switch_coeff_dictのキー用
        self.columns_name_dict = {"L1":{"CT品種数":["2CT1W"],
                                        "SANUQI品種数":["2SANSWL","4USQW","SWP原反"]},
                                  "L2":{"CT品種数":["2CT1W","4CT1W"],
                                        "UA品種数":["2UAW","4UAW"],
                                        "UY品種数":["4UYW"],},
                                  "L3":{"UA品種数":["2UAW","4UAW","8UAW","4UASW"],
                                        "SVA品種数":["3XR-1"]},
                                  "L4":{"SVA品種数":["3XR-1","3XR-1SS","3XR-1SW"]},
                                  "L5":{"SANUQI品種数":["6VQ-1-1840","6VQ-1-1840GX7000","7SWP-Ge-SWD-1500"]},
                                  "L6":{"SVA品種数":["3PR-1","3PR-1SW","3XR-1","3XR-1SW","3XR-1SWD","3XR-1UWD","3XR-1UWS",],
                                        "SAZMA品種数":["SAZMA-S原反(W_EXB)","SAZMA原反(W_EXB)"]},
                                  "L7":{"SVA品種数":["3PR-1EUW","3XR-1EUW","3XR-1UWD"]}
                             }
        
        
        
        
        self.dope_dict = {"L1":{"dope1":"CT",
                                "dope2":"SANUQI"},
                          "L2":{"dope1":"CT",
                                "dope2":"UA",
                                "dope3":"UY"},
                          "L3":{"dope1":"UA",
                                "dope2":"SVA"},
                          "L4":{"dope1":"SVA"},
                          "L5":{"dope1":"SANUQI"},
                          "L6":{"dope1":"SVA",
                                "dope2":"SAZMA"},
                          "L7":{"dope1":"SVA"}}
        
        #TODO 実際のドープ種と、ドープグループに分ける。
        
    
    
    
    def get_split_month_list(self,months):
        """
        末の月から3か月ごと区切ったリストをかえす
        クォーターごとの月が子リストになる
        
        """
        result = []
        i = len(months)
        while i > 0:
            start = max(0, i - 3)
            result.insert(0, months[start:i])
            i -= 3
        return result
    
    
    
        
    
    def too_much_init_stock_prod(self):
        """
        
        単一工場品種で、年間の販売量(推定期間の販売量) < 期首在庫 な品種のリスト
        
        """
        
        exclusion_list = []
        for prod_name in self.single_factory_prod_list:
            plant_list = self.prod_plant_dict[prod_name]
            plant = plant_list[0]
            if self.init_stock_dict[prod_name][plant] > sum([self.sales_dict[month][prod_name] for month in self.jissui_month_list]):
                exclusion_list.append(prod_name)
        
        
        return exclusion_list
    
    
    def get_ave_month_dict(self):
        """
        販売量の平均をとる月のリストを辞書で。
        {4月:[5月,6月,7月],
        5月:[6月,7月,8月]}

        """
        
        ave_month_dict = {}
        
        if self.ave_sales_mode == "含む":
            diff = 0
        if self.ave_sales_mode == "含まない":
            diff = 1
        
        for i in range(len(self.jissui_month_list)):
            
            #最終月に関して
            if i == len(self.jissui_month_list) - 1:
                month_list = [self.jissui_month_list[i]]    #最終月は最終月自身で。
            
            #最終月以外
            else:
                try:
                    month_list = self.jissui_month_list[i+diff:i+diff+self.ave_month_num]
                except:
                    month_list = self.jissui_month_list[i+diff:]
            
            
            ave_month_dict[self.jissui_month_list[i]] = month_list

        
        return ave_month_dict
    
    
    def get_big_M(self):
        """
        くそでかM
        
        """
        max_list=[]
        for month in self.jissui_month_list:
            max_list.append(max(self.sales_dict[month].values()))
        M = max(max_list)*10
        return M
    
    def get_small_m(self):
        """
        クソちびm
        
        生産時間0.5時間、CS10、幅1.15 で作った時の平米とする。
        単位は千平米
        """
        
        m = 0.5*10*60*1.15/1000
        return m
        
        

    #転記おわり
    def delta_subdelta_constraint(self):
        """
        δ（とサブδ）のための制約条件。
        
        """
        
        for index in self.all_index:
            self.problem += self.x[index]-self.M*self.delta[index] <= 0
            self.problem += self.x[index] - self.m >= -self.M*self.subdelta[index]
            self.problem += self.delta[index]+self.subdelta[index] == 1
    
    
    
    
    def z_variable_constraint(self):
        """
        変数zを各工場各月各品種の月末在庫にするための制約
        
        """
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    index = self.jissui_month_list.index(month)   
                    #z=月末在庫とするための制約
                    self.problem += self.z[plant,month,prod_name] == self.init_stock_dict[prod_name][plant] + \
                                    pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - \
                                    pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])

    
    def delta_subdelta_constraint_z(self):
        """
        δ（とサブδ）のための制約条件。
        
        """
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        over_stock = self.z[plant,month,prod_name] - ave_sales*(self.basic_stock_max_dict[prod_name][plant][month])
                        
                        #TODO over_stockがぴったり0のときどうなっている？？調べたい ←ピッタリゼロのときにカウントしないようにmが必要。
                        self.problem += over_stock-self.M*self.delta_z[plant,month,prod_name] <= 0
                        self.problem += over_stock - self.m >= -self.M*self.subdelta_z[plant,month,prod_name]
                        self.problem += self.delta_z[plant,month,prod_name]+self.subdelta_z[plant,month,prod_name] == 1
    
    def delta_subdelta_constraint_mz(self):
        """
        δ（とサブδ）のための制約条件。
        
        """
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        shortage_stock = ave_sales*(self.basic_stock_min_dict[prod_name][plant][month]) - self.z[plant,month,prod_name]
                        
                        self.problem += shortage_stock-self.M*self.delta_mz[plant,month,prod_name] <= 0
                        self.problem += shortage_stock - self.m >= -self.M*self.subdelta_mz[plant,month,prod_name]
                        self.problem += self.delta_mz[plant,month,prod_name]+self.subdelta_mz[plant,month,prod_name] == 1
            
    
    
    def fuka_equal_constraint(self):
        """
        # 制約条件 (各月各工場の負荷時間ぴったり）(絶対制約)
         
         このまま描いてtryexceptにするか、⇒やめた
         
         monthだけないなんてことはない。
         plantと品種の辞書が欲しい。
        
        """
        
        #ある工場ある月ある品種の生産時間(生産量達成率加味)なんでこれ100かけてるんだっけ？⇒逆数だから
        
        
        for plant in self.plant_list:
            for month in self.constraint_period_dict["負荷時間一致制約"]:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) == (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])

    
    
    # def fuka_less_constraint(self):
    #     """
    #     # 制約条件 (各月各工場の負荷時間以下）(絶対制約)
         
    #      このまま描いてtryexceptにするか、⇒やめた
         
    #      monthだけないなんてことはない。
    #      plantと品種の辞書が欲しい。
        
    #     """
        
    #     #ある工場ある月ある品種の生産時間(生産量達成率加味)なんでこれ100かけてるんだっけ？⇒逆数だから
        
        
    #     #for plant in self.plant_list:

    #     for plant in self.constraint_plant_dict["負荷時間以下制約"]:
    #         for month in self.constraint_period_dict["負荷時間以下制約"]:
    #             month_hour_dict = {}
    #             for prod_name in self.plant_prod_dict[plant]:
    #                 prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
    #                 month_hour_dict[prod_name] = prod_time
    #             #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
    #             self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
        
    
    

    
    
    
    # def fuka_less_constraint_2(self):
    #     """
    #     #TODO なんかエラーにはならんが、生産時間の合計＋切り替え時間 = 負荷時間　になっていない⇒いやなってるぽい。結果出力プログラムの書き換えが必要。
        
        
    #     """
                
    #     for plant in self.constraint_plant_dict["負荷時間以下制約"]:
    #         for month in self.constraint_period_dict["負荷時間以下制約"]:
    #             month_hour_dict = {}
    #             for prod_name in self.plant_prod_dict[plant]:
    #                 prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
    #                 month_hour_dict[prod_name] = prod_time
                    
    #             total_switch_time = pulp.lpSum(self.delta[plant,month,prod_name] for prod_name in self.plant_prod_dict[plant])*self.switch_coeff_dict[plant]['生産品種数係数'] + self.switch_coeff_dict[plant]['切片'] 
                
    #             self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-total_switch_time)
        
    
    def fuka_less_constraint_3(self):
        for plant in self.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.switch_time[plant,month])
        
    
    def fuka_less_constraint_4(self):
        for plant in self.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month] 
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                
                
                fuka_time = self.prod_capacity_dict[plant][month]["暦日時間"] - (self.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["保全/工事"]+
                                                                             self.prod_capacity_dict[plant][month]["計画停止"])
                
                
                
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (fuka_time - self.switch_time[plant,month])
    
    
    
    
    
    def fuka_less_constraint_5(self):
        """
        TODO 保全も生産品種もないときに、切り替え時間どうなっちゃう？（月中切替のぱらめーたに、全部0のケースも含めるべきかどうか。）変な値になったとしても行けるのか？
        
        """
        for plant in self.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                
                
                fuka_time = self.prod_capacity_dict[plant][month]["暦日時間"] - (self.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["保全/工事"]+
                                                                             self.prod_capacity_dict[plant][month]["計画停止"])
                
                
                
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (fuka_time - 
                                                                                                                        self.switch_time[plant,month] -
                                                                                                                        self.inter_switch_time_head[plant,month] -
                                                                                                                        self.inter_switch_time_tail[plant,month])
    
    def sum_sales_constraint(self):
        """
        # 各品種の販売量の各月合計が合計販売量に一致（絶対制約）
        
        """

        for prod_name in self.all_prod_list:
            for month in self.constraint_period_dict["合計販売量一致制約"]:
                plant_dict = {}
                for plant in self.prod_plant_dict[prod_name]:
                    plant_dict[plant] = self.y[plant,month,prod_name]
                
                
                self.problem += pulp.lpSum(plant_dict[plant] for plant in self.prod_plant_dict[prod_name]) == self.sales_dict[month][prod_name]
                
                #self.problem += pulp.lpSum(plant_dict[plant] for plant in self.prod_plant_dict[prod_name]) >= self.sales_dict[month][prod_name] -100
                #self.problem += pulp.lpSum(plant_dict[plant] for plant in self.prod_plant_dict[prod_name]) <= self.sales_dict[month][prod_name] +100
                
                
                
                
        
        
    def not_minus_stock_constraint(self):
        """
        各月各品種月末在庫が0以上 (絶対制約)
        もしかしたらjissui_month_listでやらないほうがいいかも。(確定済み生産計画の方で確定した在庫がマイナスになっている可能性があるため)
        
        """
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["月末在庫0以上制約"]:
            for month in self.constraint_period_dict["月末在庫0以上制約"]:
                for prod_name in self.plant_prod_dict[plant]:
                    index = self.jissui_month_list.index(month)      #その月のindex
                    self.problem += self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) >= 0
                
    
    
    def within_basic_stock_constraint_min(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        もしかしたらあとで0.1下駄吐かせた方が良いかもしれない
        
        あとは平均販売量のところだけ！
        
        推定期間で合計販売量がずっと0の品種は除外しないとヤバイ。
        
        特に、基準在庫Min以上を満たすのが難しい。0以上なら多分イイんだけども。。。分けるか。
        
        
        
        """
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["基準在庫月数Min以上制約"]:
            for month in self.constraint_period_dict["基準在庫月数Min以上制約"]:
                for prod_name in self.plant_prod_dict[plant]:
                    index = self.jissui_month_list.index(month)
                    
                    #月末在庫
                    stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
                    self.problem += stock >= ave_sales*(self.basic_stock_min_dict[prod_name][plant][month])
                    #self.problem += stock >= ave_sales*(self.basic_stock_dict[prod_name][plant]["min"]/30)
                    #self.problem += stock <= ave_sales*(self.basic_stock_dict[prod_name][plant]["max"]/30)
                    
                
        
    
    
    def within_basic_stock_constraint_max(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        単一工場品種で、年間の販売量(推定期間の販売量) < 期首在庫 な品種は除く
        
        TODO ↑除かない方がいいかも？生産キャパに余裕がある場合に、この品種が生産されまくってしまいそう。
        除くのではなく、在庫月数の計算を先に行って、その結果で基準在庫Maxの値を書き換えるのがいいかも。
        
        """
        exclusion_list = self.too_much_init_stock_prod()   #除去品種リスト
        
        
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["基準在庫月数Max以下制約"]:
            for month in self.constraint_period_dict["基準在庫月数Max以下制約"]:
                for prod_name in self.plant_prod_dict[plant]:
                    
                    if prod_name not in exclusion_list:
                    
                        index = self.jissui_month_list.index(month)
                        
                        #月末在庫
                        stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                        
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        
                        self.problem += stock <= ave_sales*(self.basic_stock_max_dict[prod_name][plant][month])      #例えば期首在庫が異常に多すぎると違反する。
                        
                        #self.problem += stock >= ave_sales*(self.basic_stock_dict[prod_name][plant]["min"]/30)
                        #self.problem += stock <= ave_sales*(self.basic_stock_dict[prod_name][plant]["max"]/30)      #例えば期首在庫が異常に多すぎると違反する。
    
    
    
    
    def min_continuous_constraint(self):
        """
        最低連続生産時間制約
        
        
        """
        # 最低連続生産時間
        #これは確定済み生産計画のところは除いた方がイイので、month_listが0抜いている。
        #確定済み生産計画の扱いをどうするか。     
            
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["最低連続生産時間以上制約"]:
            for month in self.constraint_period_dict["最低連続生産時間以上制約"]:
                for prod_name in self.plant_prod_dict[plant]:
                    self.problem += self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month] >= self.delta[plant,month,prod_name]*self.min_continuous_dict[prod_name][plant][month]

    
    def num_production_constraint_min(self):
        """
        生産回数制約
        
        """
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["最低生産回数以上制約"]:
            for prod_name in self.plant_prod_dict[plant]:
                #self.problem +=  pulp.lpSum(self.delta[plant,month,prod_name] for month in self.jissui_month_list) <= self.prod_num_times_dict[prod_name][plant]["max"]
                self.problem +=  pulp.lpSum(self.delta[plant,month,prod_name] for month in self.jissui_month_list) >= self.prod_num_times_dict[prod_name][plant]["min"]

    
    def num_production_constraint_max(self):
        """
        生産回数制約
        
        """
        #for plant in self.plant_list:
        for plant in self.constraint_plant_dict["最大生産回数以下制約"]:
            for prod_name in self.plant_prod_dict[plant]:
                self.problem +=  pulp.lpSum(self.delta[plant,month,prod_name] for month in self.jissui_month_list) <= self.prod_num_times_dict[prod_name][plant]["max"]
                #self.problem +=  pulp.lpSum(self.delta[plant,month,prod_name] for month in self.jissui_month_list) >= self.prod_num_times_dict[prod_name][plant]["min"]

    
    
    def finalized_sales_constraint(self):
        """
        確定販売量
        
        {'3XR-1': {'L4': {'12月': 90.0}},
        '2UAW': {'L2': {'8月': 80.0}, 'L3': {'4月': 20.0, '7月': 20.0, '1月': 20.0}},
        '4UASW': {'L3': {'9月': 40.0}}}
 
        self.x[plant,month,prod_name]
        
        
        確定生産量のところと同様の懸念のため、イコールではなく
        
        """
        
        if self.finalized_sales_dict is not None:
            for prod_name in self.finalized_sales_dict.keys():
                for plant in self.finalized_sales_dict[prod_name].keys():
                    for month in self.finalized_sales_dict[prod_name][plant].keys():
                        if month in self.jissui_month_list:
                            
                            if self.finalized_sales_dict[prod_name][plant][month] > 0:
                                self.problem += self.y[plant,month,prod_name] >= self.finalized_sales_dict[prod_name][plant][month] -1
                                self.problem += self.y[plant,month,prod_name] <= self.finalized_sales_dict[prod_name][plant][month] +1
                            
                            if self.finalized_sales_dict[prod_name][plant][month] == 0:
                                self.problem += self.y[plant,month,prod_name] == self.finalized_sales_dict[prod_name][plant][month]
        
    
    def finalized_prod_constraint(self):
        """
        確定生産量
        
        {'3XR-1': {'L4': {'12月': 90.0}},
        '2UAW': {'L2': {'8月': 80.0}, 'L3': {'4月': 20.0, '7月': 20.0, '1月': 20.0}},
        '4UASW': {'L3': {'9月': 40.0}}}
        
        確定生産量を、一個前の結果の一部をそのまま使いたい場合、小数点以下を切り捨てていることによって、負荷時間を守れなかっり
        特に単一工場品種は基準在庫0以上制約をまもれなかったりするので、不等号で多少幅持たせないとやばい。ということが判明。
        
        とりあえず、プラスマイナス1余裕をもたすこととする。（つまり、確定生産量といいつつ、最大で1000平米異なる答えが出る可能性あり。しかし、
        1000平米は、巻一本分以下なため、別にいいと思う。）
        
        とはいえ、確定生産量0は、作りたくないという明確な意思な気もするので、別枠でイコール0になるようにする
        
        """
        
        if self.finalized_prod_dict is not None:
            for prod_name in self.finalized_prod_dict.keys():
                for plant in self.finalized_prod_dict[prod_name].keys():
                    for month in self.finalized_prod_dict[prod_name][plant].keys():
                        if month in self.jissui_month_list:
                            #self.problem += self.x[plant,month,prod_name] == self.finalized_prod_dict[prod_name][plant][month]
                            
                            if self.finalized_prod_dict[prod_name][plant][month] > 0:
                                self.problem += self.x[plant,month,prod_name] >= self.finalized_prod_dict[prod_name][plant][month] -1
                                self.problem += self.x[plant,month,prod_name] <= self.finalized_prod_dict[prod_name][plant][month] +1
                            
                            if self.finalized_prod_dict[prod_name][plant][month] ==  0:
                                self.problem += self.x[plant,month,prod_name] == self.finalized_prod_dict[prod_name][plant][month]
    

    
    def get_basic_stock_num(self):
        """
        在庫の下限本数上限本数計算メイン関数。
        
        
        """
        
        ave_month_dict = self.get_ave_month_dict()      #
        
        basic_stock_num = {}
        for name in self.name_list:
            
            first_dict = {}
            for month in ave_month_dict.keys():
                
                rot_per_day = self.get_rot_per_day(name,ave_month_dict[month])
                min_num, max_num = self.get_basic_rot_num(name,rot_per_day)
                first_dict[month] = {"基準在庫本数 Min":min_num,
                                     "基準在庫本数 Max":max_num}
            
            basic_stock_num[name] = first_dict
                
        
        return basic_stock_num
    
    
    
    # def get_fuka_obj(self):
    #     """
    #     推定期間の全工場全月合計負荷時間を最小化
        
    #     発想の転換で、元々の負荷時間との差を最大化！
        
    #     """
        
    #     #実際の生産時間から求めた負荷時間
    #     jissui_month_hour_dict = {}
    #     for plant in self.plant_list:
    #         total_month_hour_dict = {}
    #         for month in self.jissui_month_list:
    #             month_hour_dict = {}
    #             for prod_name in self.plant_prod_dict[plant]:
    #                 prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
    #                 month_hour_dict[prod_name] = prod_time
                
                
    #             total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間
            
    #         jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計
        
        
        
    #     # #パラメータファイルで設定した負荷時間
    #     # params_plant_hour = {}
    #     # for plant in self.plant_list:
    #     #     month_hour = {}
    #     #     for month in self.jissui_month_list:
    #     #         month_hour[month] = self.fuka_dict[plant][month]
    #     #     params_plant_hour[plant] = pulp.lpSum(list(month_hour.values()))
         
        
    #     #定数から引く意味ないかも
    #     #obj2 = pulp.lpSum(params_plant_hour[plant] for plant in self.plant_list) - pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list)
    #     obj2 =  - pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list)
        
    #     return obj2
    
    

        
        
    def w_sw_prod_obj_function(self):
        """
        L4 3XRW と L6 3XRSW の合計生産量を最大化
        優先SVA品種の合計生産量最大化s
        
        """
        # self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
        #                 pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list])
                        
        all_list = []
        for prod_tuple in self.priority_sva_prod_list:
            sum_prod_amount = pulp.lpSum([self.x[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_amount)
            
        self.problem += pulp.lpSum(all_list)
        
        
    def sub_prod_obj_function(self):
        """
        サブ品種（L2 4UAW、L3 2UAW、L6 3XR-UWD、L3 3XR-1）の推定期間での合計生産量を最小化
        
        基本は最大化問題として解きたい（これは好み）ので、符号を逆転させる
        
        """
        
        # self.problem += -(pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list])+\
        #                    pulp.lpSum([self.x["L3",month,"3XR-1"] for month in self.jissui_month_list]))
        
        
        all_list = []
        for prod_tuple in self.sub_prod_list:
            sum_prod_amount = pulp.lpSum([self.x[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_amount)
        
        self.problem += - pulp.lpSum(all_list)
        
        
        
                       
        
    
    def prod_time_obj_function(self):
        """
        推定期間の全工場合計生産時間を最大化
        
        単純にxを全部足せばよくねと思ったが、xは生産量であって、時間の変換時に品種情報が必要なので
        わざわざ品種ごとの生産時間もとめてから全部足す必要あり。
        

        
        """
        jissui_month_hour_dict = {}
        for plant in self.plant_list:
            total_month_hour_dict = {}
            for month in self.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list)
        
    
    def over_stock_obj_function(self):
        
        # jissui_month_hour_dict = {}
        # for plant in self.plant_list:
        #     total_month_hour_dict = {}
        #     for month in self.jissui_month_list:
        #         month_hour_dict = {}
        #         for prod_name in self.plant_prod_dict[plant]:
        #             month_hour_dict[prod_name] = pulp.lpSum(self.delta_z)
        
        
        self.problem += -(pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
                                for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]))
    
    def shortage_stock_obj_function(self):
        
        
        self.problem += -(pulp.lpSum(self.delta_mz[plant,month,prod_name] for plant in self.plant_list
                                for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]))
    
    
    
    def over_stock_amount_obj_function(self):
        """
        "超過月末在庫月数最小化"
        
        無限大の発散を防ぐため、平均販売量に0.01を足して0にならんようにする。⇒変数同士の割り算なので非線形でそもそもNG。変数変換で行けるのかもしれんが。
        仕方ないので単純に超過量を合計することに。本当は月数でやりたいけどなー。7桁でやる手もあるが。
        
        """
        over_stock_amount_list = []
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        over_stock = self.z[plant,month,prod_name] - ave_sales*(self.basic_stock_max_dict[prod_name][plant][month])
                        
                        # month_num = over_stock/(ave_sales+0.01)
                        # month_num_list.append(month_num)
                        
                        over_stock_amount_list.append(over_stock)
        
        
        self.problem += -pulp.lpSum(over_stock_amount_list)
        
        
                    
    def prod_num_obj_function(self):
        """
        レア品種のみにした方がいいかも
        
        
        """
        # self.problem += -(pulp.lpSum(self.delta[plant,month,prod_name] for plant in self.plant_list
        #                         for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]))
        
        
        # self.problem += -(pulp.lpSum([self.delta["L1",month,"4USQW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.delta["L2",month,"4UYW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.delta["L3",month,"8UAW"] for month in self.jissui_month_list]))
        
        all_list = []
        for prod_tuple in self.rare_prod_list:
            sum_prod_num = pulp.lpSum([self.delta[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_num)
        
        self.problem +=  - pulp.lpSum(all_list)
        
        
        
                        
    def over_fuka_obj_function(self):
        """
        負荷時間以下制約違反量最小化
        (実際には使用生産時間最小化をしている。)
        
        """
        jissui_month_hour_dict = {}
        for plant in self.plant_list:
            total_month_hour_dict = {}
            for month in self.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        exclusion_plant_list = list(set(self.plant_list) - set(self.constraint_plant_dict["負荷時間以下制約"]))

        #使用生産時間
        self.problem += -(pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list))
        
        
        #基準在庫Minの制約を付ける(該当工場のみ？なくてもよい。（0以上制約で満足なら。）)
        # for plant in exclusion_plant_list:
        #     for month in self.jissui_month_list:
        #         for prod_name in self.plant_prod_dict[plant]:
        #             index = self.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
        #             self.problem += stock >= ave_sales*(self.basic_stock_min_dict[prod_name][plant][month])
        
        #①在庫 - 基準在庫Min > 0 になる月数最小化（定式化上いけるのか？？マイナスつけるだけ？　複数品種複数工場で負荷時間足りていない時これでなにかおつりないか？）
        #翌月の月数との差最小化（3月末在庫月数でそろうことを期待。これは微妙かも）
        #
        
        
        
        
        #余力時間は0以下にしたいよってやつ(制約条件)
        #よく考えたら、必ずしも0以下にならんかも。販売量によっては。むしろ、
        #在庫月数がMinでずっと行く方が大事か。
        # for plant in exclusion_plant_list:
        #     total_month_hour_dict = {}
        #     for month in self.jissui_month_list:
        #         month_hour_dict = {}
        #         for prod_name in self.plant_prod_dict[plant]:
        #             prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
        #             month_hour_dict[prod_name] = prod_time
                
        #         total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
                
        #         self.problem += (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month]) - total_month_hour_dict[month] <= 0
            
        
        
        
        
        
        
        
        # #TODO:各月各品種の基準在庫Minとの差を最小化。（複数工場またがり品種・工場でもいけるか？？）
        # for plant in exclusion_plant_list:
        #     for month in self.jissui_month_list:
        #         for prod_name in self.plant_prod_dict[plant]:
        #             index = self.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
        #             self.problem += -(stock - ave_sales*(self.basic_stock_min_dict[prod_name][plant][month]))
        
        
    
    
    def maintenance_dope_num_obj_function(self):
        """
        TODO 3ドープ以上ある工場や、
        
        """
        dope_num_list = []
        for plant in self.plant_list:
            for month in self.maint_month_list[plant]:
                dope_num_list.append(pulp.lpSum([self.dope1_flag[plant,month],self.dope2_flag[plant,month]]))
        
        self.problem += -pulp.lpSum(dope_num_list)
    
    
    
        
        
    def almost_touch_min_stock_obj_function(self):
        """
        なるべく基準在庫Minすれすれにするため。
        
        """
        
        
        #TODO 確定生産量とか確定販売量との兼ね合いでこの基準在庫Minの制約守られない危険性あり。（解無し）このように新たに制約を増やすのはよくないかも。目的関数経由がいいか。
        exclusion_plant_list = list(set(self.plant_list) - set(self.constraint_plant_dict["負荷時間以下制約"]))
        # #基準在庫Minの制約を付ける(該当工場のみ？なくてもよい。（0以上制約で満足なら。）)
        # for plant in exclusion_plant_list:
        #     for month in self.jissui_month_list:
        #         for prod_name in self.plant_prod_dict[plant]:
        #             index = self.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
        #             self.problem += stock >= ave_sales*(self.basic_stock_min_dict[prod_name][plant][month])
        
        
        #TODO:各月各品種の基準在庫Minとの差を最小化。（複数工場またがり品種・工場でもいけるか？？）
        
        diff_list = []
        for plant in exclusion_plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    index = self.jissui_month_list.index(month)
                    
                    #月末在庫
                    stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
                    diff = stock - ave_sales*(self.basic_stock_min_dict[prod_name][plant][month])    #Min在庫からどれだけ離れているか。
                    diff_list.append(diff)
                    
        
        
        self.problem += -(pulp.lpSum(diff_list))
    
    
    def long_dope_switch_obj_function(self):
        """
        長時間ドープ切り替え回数最小化
        
        """
        self.problem += -(pulp.lpSum(self.dope_switch_flag[month] for month in self.jissui_month_list))
    
    
    def sazma_continuous_obj_function(self):
        #self.problem += pulp.lpSum(self.sazma_continuous_flag[month] for month in self.jissui_month_list)
        
        self.problem += -(pulp.lpSum(self.sazma_to_sva_flag[month] for month in self.jissui_month_list)+\
                          pulp.lpSum(self.sva_to_sazma_flag[month] for month in self.jissui_month_list))
        
    
    
    def main_dope_num_obj_function(self):
        """
        メインドープによる立上、立下回数を最大化する。
        
        self.dope_dict = {"L1":{"dope1":"CT",
                                "dope2":"SANUQI"},
                          "L2":{"dope1":"CT",
                                "dope2":"UA",
                                "dope3":"UY"},
                          "L3":{"dope1":"UA",
                                "dope2":"SVA"},
                          "L4":{"dope1":"SVA"},
                          "L5":{"dope1":"SANUQI"},
                          "L6":{"dope1":"SVA",
                                "dope2":"SAZMA"},
                          "L7":{"dope1":"SVA"}}
        
        #TODO 何とかしたい。メインドープが必ずdope1になるようにするとか？
        
        本当は保全のある月と同義ではないが、一旦これでいく
        
        """
        
        num_list = []
        for plant in self.plant_list:
            for key in self.dope_dict[plant].keys():
                if self.dope_dict[plant][key] == self.main_dope_prod_dict[plant]["メインドープ"]:
                    if key == "dope1":
                        print(plant)
                        dope_flag = self.dope1_flag
                    if key == "dope2":
                        print(plant)
                        dope_flag = self.dope2_flag
                    if key == "dope3":
                        print(plant)
                        dope_flag = self.dope3_flag
            
            

            num_list.append(pulp.lpSum(dope_flag[plant,month] for month in self.maint_month_list[plant]))
        
        self.problem += pulp.lpSum(num_list)
            
                
        
    def objective_function(self):
        """
        目的関数部分
        #TODO やり方やばいのでいいかんじにしたい。if文無しで実装したい。
        
        
        """
        
        # print(self.obj_name)
        # import time
        # time.sleep(5)
        if self.obj_name == "優先SVA品種の合計生産量を最大化":
            self.w_sw_prod_obj_function()
        
        if self.obj_name == "サブ品種の合計生産量最小化":
            self.sub_prod_obj_function()
        
        
        if self.obj_name == "合計生産時間最大化":
            self.prod_time_obj_function()
        
        if self.obj_name == "基準在庫月数Max以下制約違反回数最小化":
            self.over_stock_obj_function()
        
        if self.obj_name == "超過月末在庫量最小化":
            self.over_stock_amount_obj_function()
        
        if self.obj_name == "レア品種の合計生産回数最小化":
            self.prod_num_obj_function()
            
        if self.obj_name == "基準在庫月数Min以上制約違反回数最小化":
            self.shortage_stock_obj_function()
        
        if self.obj_name == "負荷時間以下制約違反量最小化":
            self.over_fuka_obj_function()
        
        if self.obj_name == "基準在庫月数Min超在庫量最小化（原因調査用）":
            self.almost_touch_min_stock_obj_function()
        
        if self.obj_name == "長時間ドープ切り替え回数最小化":
            self.long_dope_switch_obj_function()
        
        if self.obj_name == "SAZMA系品種連続生産月数最大化":
            self.sazma_continuous_obj_function()
        
        if self.obj_name == "保全月合計ドープ数最小化":
            self.maintenance_dope_num_obj_function()
        
        if self.obj_name == "メインドープによる立上・立下回数最大化":
            self.main_dope_num_obj_function()
        
        
    
    def w_sw_constraint(self):
        # self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
        #                 pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) == self.additional_constraint_dict["L4 3XRW と L6 3XRSW の合計生産量一致制約"]
    
        # self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
        #                 pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) <= self.additional_constraint_dict["優先SVA品種の合計生産量一致制約"]+0.1
    
        # self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
        #                 pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) >= self.additional_constraint_dict["優先SVA品種の合計生産量一致制約"]-0.1


        all_list = []
        for prod_tuple in self.priority_sva_prod_list:
            sum_prod_amount = pulp.lpSum([self.x[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_amount)
        
        self.problem +=  pulp.lpSum(all_list) <= self.additional_constraint_dict["優先SVA品種の合計生産量一致制約"]+0.1
        self.problem +=  pulp.lpSum(all_list) >= self.additional_constraint_dict["優先SVA品種の合計生産量一致制約"]-0.1
    
    
    
    
    def sub_prod_constraint(self):
        """
        目的関数の値はマイナス付きなので、ここは絶対値しとかないといけない。
        
        """
        
        # print(-self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L3 3XR-1、L6 3XR-1UWD）の合計生産量一致制約"])
        # import time
        # time.sleep(10)
        
        
        # self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list]) == abs(self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L3 3XR-1、L6 3XR-1UWD）の合計生産量一致制約"])
                       
        # self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list])+\
        #                    pulp.lpSum([self.x["L3",month,"3XR-1"] for month in self.jissui_month_list]) <= abs(self.additional_constraint_dict["サブ品種の合計生産量一致制約"])+0.1
        
        # self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list])+\
        #                    pulp.lpSum([self.x["L3",month,"3XR-1"] for month in self.jissui_month_list]) >= abs(self.additional_constraint_dict["サブ品種の合計生産量一致制約"])-0.1
    
    
        all_list = []
        for prod_tuple in self.sub_prod_list:
            sum_prod_amount = pulp.lpSum([self.x[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_amount)
            
        self.problem += pulp.lpSum(all_list) <= abs(self.additional_constraint_dict["サブ品種の合計生産量一致制約"])+0.1
        self.problem += pulp.lpSum(all_list) >= abs(self.additional_constraint_dict["サブ品種の合計生産量一致制約"])-0.1
    
    
    
    def prod_time_constraint(self):
        """
        #TODO
        """
        jissui_month_hour_dict = {}
        for plant in self.plant_list:
            total_month_hour_dict = {}
            for month in self.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        #self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) == self.additional_constraint_dict["合計生産時間一致制約"]
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) >= self.additional_constraint_dict["合計生産時間一致制約"] -0.1
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) <= self.additional_constraint_dict["合計生産時間一致制約"] +0.1
    
    def over_stock_constraint(self):
        # self.problem += pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) <= self.additional_constraint_dict["基準在庫月数Max以下制約違反回数一致制約"] + 46
        
        
        # self.problem += pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) >= self.additional_constraint_dict["基準在庫月数Max以下制約違反回数一致制約"] - 100
    
    
        self.problem += pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
                        for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) == abs(self.additional_constraint_dict["基準在庫月数Max以下制約違反回数一致制約"])
    
    def shortage_stock_constraint(self):
        # self.problem += pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) <= self.additional_constraint_dict["基準在庫月数Max以下制約違反回数一致制約"] + 46
        
        
        # self.problem += pulp.lpSum(self.delta_z[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) >= self.additional_constraint_dict["基準在庫月数Max以下制約違反回数一致制約"] - 100
    
    
        self.problem += pulp.lpSum(self.delta_mz[plant,month,prod_name] for plant in self.plant_list
                        for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) == abs(self.additional_constraint_dict["基準在庫月数Min以上制約違反回数一致制約"])
    
    
    
    
    
    

    
    def over_stock_amount_constraint(self):
        """
        超過月末在庫量一致制約。
        マイナスの値も全然とるので注意
        
        """
        over_stock_amount_list = []
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        over_stock = self.z[plant,month,prod_name] - ave_sales*(self.basic_stock_max_dict[prod_name][plant][month])
                        
                        # month_num = over_stock/(ave_sales+0.01)
                        # month_num_list.append(month_num)
                        
                        over_stock_amount_list.append(over_stock)
        
       
        self.problem += pulp.lpSum(over_stock_amount_list) >= self.additional_constraint_dict["超過月末在庫量一致制約"] - 0.1
        self.problem += pulp.lpSum(over_stock_amount_list) <= self.additional_constraint_dict["超過月末在庫量一致制約"] + 0.1
        
        
    def prod_num_constraint(self):
        """
        合計生産回数を、レア品種（）生産回数に直す。
        
        """
    
        # self.problem += pulp.lpSum(self.delta[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) >= abs(self.additional_constraint_dict["レア品種（L1 4USQW、L2 4UYW、L3 8UAW）の合計生産回数一致制約"]) -10
    
        # self.problem += pulp.lpSum(self.delta[plant,month,prod_name] for plant in self.plant_list
        #                 for month in self.jissui_month_list for prod_name in self.plant_prod_dict[plant]) <= abs(self.additional_constraint_dict["レア品種（L1 4USQW、L2 4UYW、L3 8UAW）の合計生産回数一致制約"]) +10
        
        # self.problem += (pulp.lpSum([self.delta["L1",month,"4USQW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.delta["L2",month,"4UYW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.delta["L3",month,"8UAW"] for month in self.jissui_month_list])) == abs(self.additional_constraint_dict["レア品種の合計生産回数一致制約"])
        
        
        all_list = []
        for prod_tuple in self.rare_prod_list:
            sum_prod_num = pulp.lpSum([self.delta[prod_tuple[0],month,prod_tuple[1]] for month in self.jissui_month_list])
            all_list.append(sum_prod_num)
        
        self.problem += pulp.lpSum(all_list)  == abs(self.additional_constraint_dict["レア品種の合計生産回数一致制約"])
    
    
    def over_fuka_constraint(self):
        """
        負荷時間以下制約違反量一致制約
        
        """
        jissui_month_hour_dict = {}
        for plant in self.plant_list:
            total_month_hour_dict = {}
            for month in self.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        exclusion_plant_list = list(set(self.plant_list) - set(self.constraint_plant_dict["負荷時間以下制約"]))

        #生産可能時間
        #total = pulp.lpSum(self.fuka_dict[plant][month] for plant in exclusion_plant_list for month in self.jissui_month_list) - pulp.lpSum(self.ave_switch_dict[plant][month] for plant in exclusion_plant_list for month in self.jissui_month_list)
        #st.write(sum([self.fuka_dict[plant][month] for plant in self.plant_list for month in self.jissui_month_list])-sum([self.ave_switch_dict[plant][month] for plant in self.plant_list for month in self.jissui_month_list]))
        
        self.problem += (pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list)) >= abs(self.additional_constraint_dict["負荷時間以下制約違反量一致制約"])-0.1
        self.problem += (pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list)) <= abs(self.additional_constraint_dict["負荷時間以下制約違反量一致制約"])+0.1
    
    
    def almost_touch_min_stock_constraint(self):
        #TODO 確定生産量とか確定販売量との兼ね合いでこの基準在庫Minの制約守られない危険性あり。（解無し）このように新たに制約を増やすのはよくないかも。目的関数経由がいいか。
        exclusion_plant_list = list(set(self.plant_list) - set(self.constraint_plant_dict["負荷時間以下制約"]))

        diff_list = []
        for plant in exclusion_plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    index = self.jissui_month_list.index(month)
                    
                    #月末在庫
                    stock = self.init_stock_dict[prod_name][plant] + pulp.lpSum(self.x[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1]) - pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.jissui_month_list[:index+1])
                    
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.y[plant,month2,prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                    
                    diff = stock - ave_sales*(self.basic_stock_min_dict[prod_name][plant][month])    #Min在庫からどれだけ離れているか。
                    diff_list.append(diff)
                    
        
        
        self.problem += (pulp.lpSum(diff_list)) >= abs(self.additional_constraint_dict["基準在庫月数Min超在庫量一致制約"])-0.1
        self.problem += (pulp.lpSum(diff_list)) <= abs(self.additional_constraint_dict["基準在庫月数Min超在庫量一致制約"])+0.1
    
    
    def maintenance_dope_num_constraint(self):
        """
        #TODO 2ドープ以上に対応する
        
        """
        dope_num_list = []
        for plant in self.plant_list:
            for month in self.maint_month_list[plant]:
                dope_num_list.append(pulp.lpSum([self.dope1_flag[plant,month],self.dope2_flag[plant,month]]))
        
        self.problem += pulp.lpSum(dope_num_list) == abs(self.additional_constraint_dict["保全月合計ドープ数一致制約"])
    
    
    
    def main_dope_num_constraint(self):
        num_list = []
        for plant in self.plant_list:
            for key in self.dope_dict[plant].keys():
                if self.dope_dict[plant][key] == self.main_dope_prod_dict[plant]["メインドープ"]:
                    if key == "dope1":
                        dope_flag = self.dope1_flag
                    if key == "dope2":
                        dope_flag = self.dope2_flag
                    if key == "dope3":
                        dope_flag = self.dope3_flag
            
            

            num_list.append(pulp.lpSum(dope_flag[plant,month] for month in self.maint_month_list[plant]))
        
        self.problem += pulp.lpSum(num_list) == abs(self.additional_constraint_dict["メインドープによる立上・立下回数一致制約"]) 
    
    
    
    
    
    
    
    
    def long_dope_switch_constraint(self):
        """
        長時間ドープ切り替え回数最小化
        
        """
        self.problem += (pulp.lpSum(self.dope_switch_flag[month] for month in self.jissui_month_list)) == abs(self.additional_constraint_dict["長時間ドープ切り替え回数一致制約"])

    
    
    def sazma_continuous_constraint(self):
        """
        sazma系はなるべく連続生産する
        
        """
        #self.problem += (pulp.lpSum(self.sazma_continuous_flag[month] for month in self.jissui_month_list)) == abs(self.additional_constraint_dict["SAZMA系品種連続生産月数一致制約"])
        
        self.problem += (pulp.lpSum(self.sazma_to_sva_flag[month] for month in self.jissui_month_list)+\
                        pulp.lpSum(self.sva_to_sazma_flag[month] for month in self.jissui_month_list)) == abs(self.additional_constraint_dict["SAZMA系品種連続生産月数一致制約"])
    
    
    
    
    
    
    def long_dope_switch_variable_constraint(self):
        """
        長時間のドープ切り替えを検知するための変数をただしく動かすための制約
        とりあえずL6のみ
        
        """
        
        #TAC群にひとつでも1があったら1、すべてが0のときに0を返すバイナリ変数
        for month in self.jissui_month_list:
            for prod_name in self.plant_prod_dict["L6"]:
                if "SAZMA" not in prod_name:
                    self.problem += self.tac_prod_flag[month] >= self.delta["L6",month,prod_name]
            
            self.problem += self.tac_prod_flag[month] <= pulp.lpSum(self.delta["L6",month,prod_name] for prod_name in self.plant_prod_dict["L6"] 
                                                    if "SAZMA" not in prod_name)
        
        
        
        #sazma群にひとつでも1があったら1、すべてが0のときに0を返すバイナリ変数
        for month in self.jissui_month_list:
            for prod_name in self.plant_prod_dict["L6"]:
                if "SAZMA" in prod_name:
                    self.problem += self.sazma_prod_flag[month] >= self.delta["L6",month,prod_name]
            
            self.problem += self.sazma_prod_flag[month] <= pulp.lpSum(self.delta["L6",month,prod_name] for prod_name in self.plant_prod_dict["L6"]
                                                    if "SAZMA" in prod_name)
        
        
        for month in self.jissui_month_list:
            self.problem += self.dope_switch_flag[month] <= self.tac_prod_flag[month]
            self.problem += self.dope_switch_flag[month] <= self.sazma_prod_flag[month]
            self.problem += self.dope_switch_flag[month] >= self.tac_prod_flag[month] + self.sazma_prod_flag[month] - 1
    
    def sazma_continuous_variable_constraint(self):
        """
        sazma系品種の連続生産フラグを設定するための制約
        
        """
        for i in range(len(self.jissui_month_list)-1):
            self.problem += self.sazma_continuous_flag[self.jissui_month_list[i]] <= self.sazma_prod_flag[self.jissui_month_list[i]]
            self.problem += self.sazma_continuous_flag[self.jissui_month_list[i]] <= self.sazma_prod_flag[self.jissui_month_list[i+1]]
            self.problem += self.sazma_continuous_flag[self.jissui_month_list[i]] >= self.sazma_prod_flag[self.jissui_month_list[i]] + self.sazma_prod_flag[self.jissui_month_list[i+1]] -1
        
        
    def sazma_to_sva_constraint(self):
        """
        sazma_prod_flag が 1⇒0 のとき1、それ以外のとき0 
        
        """
        for i in range(len(self.jissui_month_list)-1):
            self.problem += self.sazma_to_sva_flag[self.jissui_month_list[i]] <= self.sazma_prod_flag[self.jissui_month_list[i]]
            self.problem += self.sazma_to_sva_flag[self.jissui_month_list[i]] <= 1 - self.sazma_prod_flag[self.jissui_month_list[i+1]]
            self.problem += self.sazma_to_sva_flag[self.jissui_month_list[i]] >= self.sazma_prod_flag[self.jissui_month_list[i]] - self.sazma_prod_flag[self.jissui_month_list[i+1]]
        
    def sva_to_sazma_constraint(self):
        """
        sazma_prod_flag が 0⇒1 のとき1、それ以外のとき0 
        
        """
        for i in range(len(self.jissui_month_list)-1):
            self.problem += self.sva_to_sazma_flag[self.jissui_month_list[i]] <= self.sazma_prod_flag[self.jissui_month_list[i+1]]
            self.problem += self.sva_to_sazma_flag[self.jissui_month_list[i]] <= 1 - self.sazma_prod_flag[self.jissui_month_list[i]]
            self.problem += self.sva_to_sazma_flag[self.jissui_month_list[i]] >= self.sazma_prod_flag[self.jissui_month_list[i+1]] - self.sazma_prod_flag[self.jissui_month_list[i]]
        
    
    
    
    def dope_flag_constraint(self):
        """
        ドープが大きく異なる品種がある工場について、その月の異種ドープ数を得るための制約
        
        
        #TODO おそらく本来であればdope1 dope2とフラグを変数別々にせず、dope_flagとして一つにして、添え字で区別するのがいいのだろう。。
        つまり、添え字を[工場,月]→[ドープ種名,工場,月]のように変更。
        dope1,dope2,dope3でやる場合の変数の数は、3*7*12 = 252 
        dope_flagとした場合は(2*12+3*12+2*12+1*12+1*12+2*12+1*12)=12(2+3+2+1+1+2+1) = 144
        
        また、1ドープ工場は実質ドープ関係の変数・制約いらないので、もっと削減できる。(2*12+3*12+2*12+2*12) = 108
        
        -----
        2024年度の場合
        L1   dope1:CT dope2:SANUQI
        L2   dope1:CT dope2:UA dope3:UY
        L3   dope1:UA dope2:SVA
        L4   dope1:SVA
        L5   dope1:SANUQI
        L6   dope1:SVA dope2:SAZMA
        L7   dope7:SVA
    
        """
        for plant in self.plant_list:
            if plant in ["L1","L3","L6"]:
                #dope1群にひとつでも1があったら1、すべてが0のときに0を返すバイナリ変数
                for month in self.jissui_month_list:
                    columns_list = list(self.columns_name_dict[plant].keys())
                    
                    
                    #ドープ1に関して
                    column_name = columns_list[0]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope1_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope1_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
                    
                    #ドープ2に関して
                    column_name = columns_list[1]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope2_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope2_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
    
            if plant in ["L4","L5","L7"]:
                #ドープが一つだけの工場
                for month in self.jissui_month_list:
                    columns_list = list(self.columns_name_dict[plant].keys())
                    
                    
                    #ドープ1に関して
                    column_name = columns_list[0]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope1_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope1_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
            
            if plant in ["L2"]:
                #ドープが3つの工場
                for month in self.jissui_month_list:
                    columns_list = list(self.columns_name_dict[plant].keys())
                    
                    
                    #ドープ1に関して
                    column_name = columns_list[0]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope1_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope1_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
                    
                    #ドープ2に関して
                    column_name = columns_list[1]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope2_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope2_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
                    
                    
                    #ドープ3に関して
                    column_name = columns_list[2]
                    for prod_name in self.columns_name_dict[plant][column_name]:
                        self.problem += self.dope3_flag[plant,month] >= self.delta[plant,month,prod_name]
                    
                    
                    self.problem += self.dope3_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name]
                                                                    for prod_name in self.columns_name_dict[plant][column_name])
    
    
    
    
    
                    
                
    def all_prod_flag_constraint(self):
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    self.problem += self.all_prod_flag[plant,month] >= self.delta[plant,month,prod_name]
                
                self.problem += self.all_prod_flag[plant,month] <= pulp.lpSum(self.delta[plant,month,prod_name] for prod_name in self.plant_prod_dict[plant])
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def switch_time_constraint_common(self,plant,month,month_type):
        """
        月内切替時間の制約の、共通部分切り出し
        TODO 2ドープではない工場イケてるのか？これ要確認 ⇒ 1ドープの工場どうしよdope2_flagのところ 
        
        
        """
        switch_time_list = [self.switch_coeff_dict[plant][month_type]["intercept"]*self.all_prod_flag[plant,month]]     #切替時間のリスト(先に切片いれとく) 。生産品種が一つもない時は0になる。
                    
        #ドープ毎の品種数の分
        for column_name in self.columns_name_dict[plant].keys():
            switch_time_list.append(self.switch_coeff_dict[plant][month_type][column_name]*pulp.lpSum(self.delta[plant,month,prod_name] 
                                                            for prod_name in self.columns_name_dict[plant][column_name]))   #ドープ毎
        
        #ドープ数の分
        switch_time_list.append(self.switch_coeff_dict[plant][month_type]["ドープ数"]*pulp.lpSum([self.dope1_flag[plant,month],
                                                                                self.dope2_flag[plant,month]]))
        
        
        #単独品種の分
        for prod_name in self.plant_prod_dict[plant]:
            switch_time_list.append(self.switch_coeff_dict[plant][month_type][prod_name]*self.delta[plant,month,prod_name])  #品種ごとの切替時間(係数と変数の積)をリストに追加
        
        
        #合計品種数
        switch_time_list.append(self.switch_coeff_dict[plant][month_type]["全品種数"]*pulp.lpSum(self.delta[plant,month,prod_name] 
                                                                                for prod_name in self.plant_prod_dict[plant]))
        
        
        self.problem += self.switch_time[plant,month] == pulp.lpSum(switch_time_list)
        
    
    def switch_time_constraint(self):
        """
        変数switch_timeが線形回帰式で表現されるようにするための制約
        
        
        #switch_coeff_dict[L1]の中身（保全なしケース）
        {
            "保全なし":{
            "intercept":-181.00000000000014
            "SANUQI品種数":11.999999999999973
            "CT品種数":7.999999999999993
            "2CT1W":8.000000000000034
            "全品種数":20.000000000000014
            "SWP原反":4.0000000000000355
            "2SANSWL":4.000000000000018
            "4USQW":4.000000000000032
            "ドープ数":145.00000000000009
            }
        
        
        
        
        self.colmuns_name_dict = {"L1":{"CT品種数":["2CT1W"],
                                   "SANUQI品種数":["2SANSWL","4USQW","SWP原反"]},
                             "L3":{"UA品種数":["2UAW","4UAW","8UAW","4UASW"],
                                   "SVA品種数":["3XR-1"]},
                             "L6":{"TAC品種数":["3PR-1","3PR-1SW","3XR-1","3XR-1SW","3XR-1SWD","3XR-1UWD","3XR-1UWS",],
                                   "SAZMA品種数":["SAZMA-S原反(W_EXB)","SAZMA原反(W_EXB)"]}
                             }
        
        
        """
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                if ((self.month_type_dict[plant][month]["保全前期"] == "なし") and (self.month_type_dict[plant][month]["保全後期"] == "なし")):
                    self.switch_time_constraint_common(plant,month,"保全前期なし保全後期なし")
                
                if ((self.month_type_dict[plant][month]["保全前期"] == "あり") and (self.month_type_dict[plant][month]["保全後期"] == "なし")):
                    self.switch_time_constraint_common(plant,month,"保全前期あり保全後期なし")
                
                if ((self.month_type_dict[plant][month]["保全前期"] == "なし") and (self.month_type_dict[plant][month]["保全後期"] == "あり")):
                    self.switch_time_constraint_common(plant,month,"保全前期なし保全後期あり")
                
                if ((self.month_type_dict[plant][month]["保全前期"] == "あり") and (self.month_type_dict[plant][month]["保全後期"] == "あり")):
                    self.switch_time_constraint_common(plant,month,"保全前期あり保全後期あり")
                    
    
    ######## 月間切替に関する制約 ##############################################################################
    
    def inter_switch_flag_constraint(self):
        for plant in self.plant_list:
            for i in range(len(self.jissui_month_list)-1):
                
                #TODO本当は工場毎に場合分けした方が制約減らせるが。。少なくともL2は3ドープなので何とかしないと。。
                                    
                #ドープ1について止める場合1、それ以外0
                self.problem += self.dope1_stop_flag[plant,self.jissui_month_list[i+1]] >= self.dope1_flag[plant,self.jissui_month_list[i]] - self.dope1_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.dope1_stop_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_flag[plant,self.jissui_month_list[i]]
                self.problem += self.dope1_stop_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope1_flag[plant,self.jissui_month_list[i+1]]
                
                
                #ドープ2について止める場合1、それ以外0
                self.problem += self.dope2_stop_flag[plant,self.jissui_month_list[i+1]] >= self.dope2_flag[plant,self.jissui_month_list[i]] - self.dope2_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.dope2_stop_flag[plant,self.jissui_month_list[i+1]] <= self.dope2_flag[plant,self.jissui_month_list[i]]
                self.problem += self.dope2_stop_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope2_flag[plant,self.jissui_month_list[i+1]]
            
                #やめるドープがある場合1、ない場合0
                self.problem += self.stop_flag[plant,self.jissui_month_list[i+1]] >= self.dope1_stop_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.stop_flag[plant,self.jissui_month_list[i+1]] >= self.dope2_stop_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.stop_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_stop_flag[plant,self.jissui_month_list[i+1]] + self.dope2_stop_flag[plant,self.jissui_month_list[i+1]]
        
                
                
                #ドープ1について開始する場合1、それ以外0
                self.problem += self.dope1_start_flag[plant,self.jissui_month_list[i+1]] >= self.dope1_flag[plant,self.jissui_month_list[i+1]] - self.dope1_flag[plant,self.jissui_month_list[i]]
                self.problem += self.dope1_start_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.dope1_start_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope1_flag[plant,self.jissui_month_list[i]]
                
                
                #ドープ2について開始する場合1、それ以外0
                self.problem += self.dope2_start_flag[plant,self.jissui_month_list[i+1]] >= self.dope2_flag[plant,self.jissui_month_list[i+1]] - self.dope2_flag[plant,self.jissui_month_list[i]]
                self.problem += self.dope2_start_flag[plant,self.jissui_month_list[i+1]] <= self.dope2_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.dope2_start_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope2_flag[plant,self.jissui_month_list[i]]
            
                #開始するドープがある場合1、ない場合0
                self.problem += self.start_flag[plant,self.jissui_month_list[i+1]] >= self.dope1_start_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.start_flag[plant,self.jissui_month_list[i+1]] >= self.dope2_start_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.start_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_start_flag[plant,self.jissui_month_list[i+1]] + self.dope2_stop_flag[plant,self.jissui_month_list[i+1]]
                
                
                
                #月間品種切替フラグ
                
                self.problem += self.inter_switch_flag[plant,self.jissui_month_list[i+1]] <= self.stop_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.inter_switch_flag[plant,self.jissui_month_list[i+1]] <= self.start_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.inter_switch_flag[plant,self.jissui_month_list[i+1]] >= self.stop_flag[plant,self.jissui_month_list[i+1]] + self.start_flag[plant,self.jissui_month_list[i+1]] - 1
                
    
    
    def inter_switch_time_constraint(self):
        """
        変数inter_switch_timeが線形回帰式で表現されるようにするための制約
        
        
        #inter_switch_coeff_dict[L1]の中身
        {
            "intercept":2.1316282072803006e-14
            "CT生産終了":-3.5546068472486344e-14
            "CT生産開始":4.973799150320701e-14
            "SANUQI生産開始":2.6645352591003757e-15
            "SANUQI生産終了":-6.128431095930864e-14
            "ドープ切替":180.99999999999997
            }
        
        
        2024年度の場合
        L1   dope1:CT dope2:SANUQI
        L2   dope1:CT dope2:UA dope3:UY
        L3   dope1:UA dope2:SVA
        L4   dope1:SVA
        L5   dope1:SANUQI
        L6   dope1:SVA dope2:SAZMA
        L7   dope7:SVA
        
        
        self.dope_dict = {"L1":{"dope1":"CT",
                                "dope2":"SANUQI"},
                          "L2":{"dope1":"CT",
                                "dope2":"UA",
                                "dope3":"UY"},
                          "L3":{"dope1":"UA",
                                "dope2":"SVA"},
                          "L4":{"dope1":"SVA"},
                          "L5":{"dope1":"SANUQI"},
                          "L6":{"dope1":"SVA",
                                "dope2":"SAZMA"},
                          "L7":{"dope1":"SVA"}}
        
        
        """
        

    
        
        #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
        for plant in self.plant_list:
            #TODO本当はL2は3ドープ
            if plant in ["L1","L3","L6","L2"]:      
                
                self.problem += self.inter_switch_time_head[plant,self.jissui_month_list[0]] == 0    #初月はinter_switch_time_headは0にする。
                self.problem += self.inter_switch_time_tail[plant,self.jissui_month_list[len(self.jissui_month_list)-1]] == 0  #最終月のinter_switch_tailは0にする
                          
                for i in range(len(self.jissui_month_list)-1):
                    inter_switch_time_list = [self.inter_switch_coeff_dict[plant]["intercept"]]     #切片
                    
                    #dope1生産終了
                    dope_name = self.dope_dict[plant]["dope1"]    #dope1
                    inter_switch_time_list.append(self.dope1_stop_flag[plant,self.jissui_month_list[i+1]]*
                                                self.inter_switch_coeff_dict[plant][f"{dope_name}生産終了"])
                    
                    #dope1生産開始
                    inter_switch_time_list.append(self.dope1_start_flag[plant,self.jissui_month_list[i+1]]*
                                                self.inter_switch_coeff_dict[plant][f"{dope_name}生産開始"])
                    
                    #dope2生産終了
                    dope_name = self.dope_dict[plant]["dope2"]    #dope2
                    inter_switch_time_list.append(self.dope2_stop_flag[plant,self.jissui_month_list[i+1]]*
                                                self.inter_switch_coeff_dict[plant][f"{dope_name}生産終了"])
                    
                    #dope2生産開始
                    inter_switch_time_list.append(self.dope2_start_flag[plant,self.jissui_month_list[i+1]]*
                                                self.inter_switch_coeff_dict[plant][f"{dope_name}生産開始"])
                    
                    
                    #ドープ切替
                    inter_switch_time_list.append(self.inter_switch_coeff_dict[plant]["ドープ切替"]*
                                                self.inter_switch_flag[plant,self.jissui_month_list[i+1]])
                    
                    
                    #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
                    self.problem += self.inter_switch_time_head[plant,self.jissui_month_list[i+1]] + \
                        self.inter_switch_time_tail[plant,self.jissui_month_list[i]] == pulp.lpSum(inter_switch_time_list)
        
            if plant in ["L4","L5","L7"]:
                for i in range(len(self.jissui_month_list)):
                     self.problem += self.inter_switch_time_head[plant,self.jissui_month_list[i]] == 0
                     self.problem += self.inter_switch_time_tail[plant,self.jissui_month_list[i]] == 0

    
    
    def inter_switch_flag_constraint2(self):
        """
        月間切替に関わるフラグの制約
        
        """
        for plant in self.plant_list:
            for i in range(len(self.jissui_month_list)-1):
                #TODO本当は工場毎に場合分けした方が制約減らせるが。。
                
                #ドープ1⇒ドープ2のドープ切替フラグのための制約     #TODO inter_switch_1to2_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_flag[plant,self.jissui_month_list[i]]
                self.problem += self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope1_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope2_flag[plant,self.jissui_month_list[i]]
                self.problem += self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]] <= self.dope2_flag[plant,self.jissui_month_list[i+1]]
                
                self.problem +=  self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]] >= self.dope1_flag[plant,self.jissui_month_list[i]] + \
                    (1 - self.dope1_flag[plant,self.jissui_month_list[i+1]]) +\
                    (1 - self.dope2_flag[plant,self.jissui_month_list[i]]) + self.dope2_flag[plant,self.jissui_month_list[i+1]] -3
                
                
                #ドープ2⇒ドープ1のドープ切替フラグのための制約     #TODO inter_switch_2to1_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope1_flag[plant,self.jissui_month_list[i]]
                self.problem += self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]] <= self.dope1_flag[plant,self.jissui_month_list[i+1]]
                self.problem += self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]] <= self.dope2_flag[plant,self.jissui_month_list[i]]
                self.problem += self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]] <= 1 - self.dope2_flag[plant,self.jissui_month_list[i+1]]
                
                
                self.problem +=  self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]] >= (1 - self.dope1_flag[plant,self.jissui_month_list[i]]) + \
                    self.dope1_flag[plant,self.jissui_month_list[i+1]] +\
                    self.dope2_flag[plant,self.jissui_month_list[i]] + (1 - self.dope2_flag[plant,self.jissui_month_list[i+1]]) -3
                
    
    
    
    def inter_switch_time_constraint2_common(self,coeff_dict,plant,dope1_name,dope2_name,
                                             case_name,i):
        """
        共通要素
        """
        inter_switch_time_list = [coeff_dict[plant]["intercept"]]     #切片
        
        #i月にdope1を作るかどうか
        inter_switch_time_list.append(self.dope1_flag[plant,self.jissui_month_list[i]]*
                                coeff_dict[plant][f"前月_{dope1_name}"])
        
        #i+1月にdope1を作るかどうか
        inter_switch_time_list.append(self.dope1_flag[plant,self.jissui_month_list[i+1]]*
                                coeff_dict[plant][f"当月_{dope1_name}"])
        
        
        #ドープが2つの工場
        if plant in ["L1","L3","L6","L2"]:
            #i月にdope2を作るかどうか
            inter_switch_time_list.append(self.dope2_flag[plant,self.jissui_month_list[i]]*
                                    coeff_dict[plant][f"前月_{dope2_name}"])
            
            
            #i+1月にdope2を作るかどうか
            inter_switch_time_list.append(self.dope2_flag[plant,self.jissui_month_list[i+1]]*
                                    coeff_dict[plant][f"当月_{dope2_name}"])
            
            
            #dope1⇒dope2のドープ切替があるかどうか
            inter_switch_time_list.append(self.inter_switch_1to2_flag[plant,self.jissui_month_list[i+1]]*
                                    coeff_dict[plant][f"{dope1_name}⇒{dope2_name}"])
            
            #dope2⇒dope1のドープ切替があるかどうか
            inter_switch_time_list.append(self.inter_switch_2to1_flag[plant,self.jissui_month_list[i+1]]*
                                    coeff_dict[plant][f"{dope2_name}⇒{dope1_name}"])
        
        
        if case_name == "前月に保全後期" or case_name == "当月に保全前期":
            
            #i月に生産あるか
            inter_switch_time_list.append(self.all_prod_flag[plant,self.jissui_month_list[i]]*
                                            coeff_dict[plant]["前月_生産"])
            
            #i+1月に生産あるか
            inter_switch_time_list.append(self.all_prod_flag[plant,self.jissui_month_list[i+1]]*
                                            coeff_dict[plant]["当月_生産"])
            
        
        return inter_switch_time_list
    
    
    
    
    
    
    def inter_switch_time_constraint2(self):
        #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
        for plant in self.plant_list:
            #本当はL2は3ドープ⇒2ドープ群としてとらえることにした。
            if plant in ["L1","L3","L6","L2"]:
                dope1_name = self.dope_dict[plant]["dope1"]    #dope1
                dope2_name = self.dope_dict[plant]["dope2"]    #dope2
                if plant in ["L2"]:
                    dope1_name = "UA-CT"
                    dope2_name = "UY"
            
            if plant in ["L4","L5","L7"]:
                dope1_name = self.dope_dict[plant]["dope1"]    #dope1
                dope2_name =None
                    
            self.problem += self.inter_switch_time_head[plant,self.jissui_month_list[0]] == 0    #初月はinter_switch_time_headは0にする。
            self.problem += self.inter_switch_time_tail[plant,self.jissui_month_list[len(self.jissui_month_list)-1]] == 0  #最終月のinter_switch_tailは0にする
                                
            
            for i in range(len(self.jissui_month_list)-1):
                
                #i月に保全後期がある場合
                if ((self.month_type_dict[plant][self.jissui_month_list[i]]["保全後期"] == "あり") ):
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.inter_switch_maint_tail_coeff_dict,
                                                                                    plant,dope1_name,dope2_name,"前月に保全後期",i)

                #i+1月に保全前期がある場合
                if ((self.month_type_dict[plant][self.jissui_month_list[i]]["保全前期"] == "あり") ):
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.inter_switch_maint_head_coeff_dict,
                                                                                    plant,dope1_name,dope2_name,"当月に保全前期",i)
                
                else:
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.inter_switch_coeff_dict,
                                                                                    plant,dope1_name,dope2_name,"その他",i)
                    
                    
            
                #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
                self.problem += self.inter_switch_time_head[plant,self.jissui_month_list[i+1]] + \
                    self.inter_switch_time_tail[plant,self.jissui_month_list[i]] == pulp.lpSum(inter_switch_time_list)
                
                
                
                
                
                
##############################################################################################
    
    def modeling(self):
        self.problem = pulp.LpProblem(name='anbun', sense=pulp.LpMaximize)        #最大化問題
        
        #決定変数
        #制約条件が無さ過ぎる場合、lowboundやupboundの値になる。upboundはNoneなので、Noneがそのまま答えになるので注意
        self.x = pulp.LpVariable.dicts('x', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種生産量(本当に販売できる分 (生産量達成率をかけた後))
        self.y = pulp.LpVariable.dicts('y', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種販売量
        self.z = pulp.LpVariable.dicts('z', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種在庫量
        self.delta = pulp.LpVariable.dicts('delta', self.all_index, cat='Binary')                    #各工場各月各品種生産量が0のとき0 0でない時1をとるバイナリ変数
        self.subdelta = pulp.LpVariable.dicts('subdelta', self.all_index, cat='Binary')              #⇑を確実に実施するために必要 
        
        self.delta_z = pulp.LpVariable.dicts('delta_z', self.all_index, cat='Binary')                    #各工場各月各品種在庫量が基準在庫Max以下のとき0 超過のとき1をとるバイナリ変数
        
        
        self.subdelta_z = pulp.LpVariable.dicts('subdelta_z', self.all_index, cat='Binary')              #⇑を確実に実施するために必要
        
        self.delta_mz = pulp.LpVariable.dicts('delta_mz', self.all_index, cat='Binary')                    #各工場各月各品種在庫量が基準在庫Min以下のとき1 超過のとき0をとるバイナリ変数
        self.subdelta_mz = pulp.LpVariable.dicts('subdelta_mz', self.all_index, cat='Binary')              #⇑を確実に実施するために必要
        
        
        ##長時間のドープ切り替えをなるべく入らないようにする件
        #ひとまずL6の件のみ対象にする。
        self.tac_prod_flag = pulp.LpVariable.dicts('tac_prod_flag', self.jissui_month_list, cat='Binary')   #TAC品種がその月生産ある場合は1、ない場合は0
        self.sazma_prod_flag = pulp.LpVariable.dicts('sazma_prod_flag', self.jissui_month_list, cat='Binary')  #sazma品種がその月生産ある場合は1、ない場合は0
        
        #ドープ切り替えがその月ある場合は1、ない場合は0（つまり、TAC系とsazma両方生産するときに1をとる。）
        self.dope_switch_flag = pulp.LpVariable.dicts('dope_switch_flag', self.jissui_month_list, cat='Binary')
        
        #sazma系品種の連続生産フラグ:
        self.sazma_to_sva_flag = pulp.LpVariable.dicts('sazma_to_sva_flag', self.jissui_month_list, cat='Binary')
        self.sva_to_sazma_flag = pulp.LpVariable.dicts('sva_to_sazma_flag', self.jissui_month_list, cat='Binary')
        
        
        #月内切替時間を格納するための変数
        self.switch_time = pulp.LpVariable.dicts('switch_time', self.plant_month_index, cat='Continuous')   #回帰から得られる値的に、負の値も取りうるのでlowBoundは設けない。
        
        #dope1:L1:CT,L3:UA,L6:TAC     #dope2:L1:SANUQI,L3:SVA,L6:SAZMA
        self.dope1_flag = pulp.LpVariable.dicts('dope1_flag', self.plant_month_index, cat='Binary')   #ドープ1がその月生産ある場合は1、ない場合は0
        self.dope2_flag = pulp.LpVariable.dicts('dope2_flag', self.plant_month_index, cat='Binary')   #ドープ2がその月生産ある場合は1、ない場合は0
        self.dope3_flag = pulp.LpVariable.dicts('dope3_flag', self.plant_month_index, cat='Binary')   #ドープ3がその月生産ある場合は1、ない場合は0
        
        #その月に品種の生産自体があるかどうかを示すフラグ
        self.all_prod_flag = pulp.LpVariable.dicts('all_prod_flag', self.plant_month_index, cat='Binary')   #その月に品種の生産自体があるかどうかを示すフラグ
        
        
        
        #self.dope1_stop_flag = pulp.LpVariable.dicts('dope1_stop_flag', self.plant_month_index, cat='Binary')   #月間でドープ1の生産を終える場合1、それ以外0
        #self.dope1_start_flag = pulp.LpVariable.dicts('dope1_start_flag', self.plant_month_index, cat='Binary')   #月間でドープ1の生産を開始する場合1、それ以外0
        #self.dope2_stop_flag = pulp.LpVariable.dicts('dope2_stop_flag', self.plant_month_index, cat='Binary')   #月間でドープ2の生産を終える場合1、それ以外0
        #self.dope2_start_flag = pulp.LpVariable.dicts('dope2_start_flag', self.plant_month_index, cat='Binary')   #月間でドープ2の生産を開始する場合1、それ以外0
        #self.dope3_stop_flag = pulp.LpVariable.dicts('dope3_stop_flag', self.plant_month_index, cat='Binary')   #月間でドープ3の生産を終える場合1、それ以外0
        #self.dope3_start_flag = pulp.LpVariable.dicts('dope3_start_flag', self.plant_month_index, cat='Binary')   #月間でドープ3の生産を開始する場合1、それ以外0
        
        
        #self.stop_flag = pulp.LpVariable.dicts('stop_flag', self.plant_month_index, cat='Binary')   #月間で生産を終える品種がある場合1、それ以外0
        #self.start_flag = pulp.LpVariable.dicts('start_flag', self.plant_month_index, cat='Binary')  #月間で生産を開始する品種がある場合1、それ以外0
        
        self.inter_switch_1to2_flag = pulp.LpVariable.dicts('inter_switch_1to2_flag', self.plant_month_index, cat='Binary')   #月間にドープ1⇒ドープ2の切替が発生する場合1、しない場合0
        self.inter_switch_2to1_flag = pulp.LpVariable.dicts('inter_switch_2to1_flag', self.plant_month_index, cat='Binary')   #月間にドープ2⇒ドープ1の切替が発生する場合1、しない場合0
        
        
        #月間切替時間を格納するための変数 #TODO回帰の結果得られる値が絶対に負にならないようにしておかないと解無し。
        #いや、意外と大丈夫かも。月間誤差、月内誤差のこと踏まえると、low_bound=-48しとく？
        self.inter_switch_time_head = pulp.LpVariable.dicts('inter_switch_time_head', self.plant_month_index, 
                                                         cat='Continuous',lowBound=-0.01)   #今月の頭に按分された切替時間
        self.inter_switch_time_tail = pulp.LpVariable.dicts('inter_switch_time_tail', self.plant_month_index, 
                                                         cat='Continuous',lowBound=-0.01)   #今月のお尻に按分された切替時間

        
        
        #制約条件
        self.z_variable_constraint()           #zを月末在庫にするための制約
        self.delta_subdelta_constraint()               #これは必要
        self.delta_subdelta_constraint_z()            #基準在庫Max超過検出用
        self.delta_subdelta_constraint_mz()           #基準在庫Min不足検出用
        self.long_dope_switch_variable_constraint()    #長時間のドープ切り替えをなるべく入らないようにする件
        #self.sazma_continuous_variable_constraint()
        self.sazma_to_sva_constraint()
        self.sva_to_sazma_constraint()
        
        #切替時間のための制約条件
        self.switch_time_constraint()
        self.dope_flag_constraint()
        self.all_prod_flag_constraint()
        
        
        #月間切替のための制約条件
        self.inter_switch_flag_constraint2()
        self.inter_switch_time_constraint2()
        
        

        
        
        for constraint_name in self.constraint_list:
            self.all_constraint_functions[constraint_name]()
        
        
        #追加の制約条件(昔目的関数だったもの)    
        for additional_constraint_name, value in self.additional_constraint_dict.items():
            self.all_obj_constraint_functions[additional_constraint_name]()
        
        
        #目的関数
        self.objective_function()
        


        now = datetime.datetime.now()
        file_name = "problem_"+now.strftime('%Y%m%d_%H%M%S')+".txt"
        with open(self.logfile_dir + file_name, mode='w') as f:
            f.write(str(self.problem))
        
    
    def solve(self):
        
        solver = pulp.PULP_CBC_CMD(timeLimit=self.timelimit)  # timeLimitの値を秒数で指定します。ここでは60秒。
        self.status = self.problem.solve(solver)
        #self.status = self.problem.solve()
        print(self.status)
        print(pulp.LpStatus[self.status])
        
        
    
    
    def main(self):
        self.modeling()
        self.solve()
        
        # 計算結果の表示
        
        with open("result.txt", "w") as f:
            for plant in self.plant_list:
                for month in self.jissui_month_list:
                    for prod_name in self.plant_prod_dict[plant]:
                        print(plant+" "+month+" "+prod_name+"生産量：",self.x[plant,month,prod_name].value())
                        print(plant+" "+month+" "+prod_name+"販売量：",self.y[plant,month,prod_name].value())
                        print(plant+" "+month+" "+prod_name+"在庫量：",self.z[plant,month,prod_name].value())
                        print(plant+" "+month+" "+prod_name+"デルタ：",self.delta[plant,month,prod_name].value())


                    
                    f.write(f"{plant} {month} {self.dope1_flag[plant,month].value()} \n")
                    f.write(f"{plant} {month} {self.dope2_flag[plant,month].value()} \n")

        
        
        print(pulp.LpStatus[self.status])
        
        
        # 目的関数値の取得
        self.objective_value = self.problem.objective.value()
        
        
        
        return self.x, self.y, self.status, self.objective_value, self.switch_time, self.inter_switch_time_head, self.inter_switch_time_tail
        




#######################################################################################
if __name__ == "__main__":
    with open('./test/all_params_dict.pickle', 'rb') as f:
        all_params_dict = pickle.load(f)
    prod_amount_dict,sales_amount_dict,status = MipCore(all_params_dict).main()
    mip_result_dict = {"prod_amount_dict":prod_amount_dict,"sales_amount_dict":sales_amount_dict}
        
    with open("./結果/mip_result_dict.pickle", mode='wb') as f:
        pickle.dump(mip_result_dict,f)
                
        
        
        

    
        
    
    