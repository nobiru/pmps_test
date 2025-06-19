import pulp
import datetime
import pickle
from index_generator import CommonProcess

class MipCoreFineTuning():
    """
    混合整数計画法実装
    
    
    
    """
    def __init__(self,all_params_dict,timelimit=60):
        
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
        self.basic_stock_max_dict = all_params_dict["basic_stock_max_dict"]
        self.ave_sales_info_dict = all_params_dict["ave_sales_info_dict"]
        
        self.constraint_plant_dict = all_params_dict["constraint_plant_dict"]
        
        
        self.achieve_rate_dict = all_params_dict["achieve_rate_dict"]
        self.all_index = all_params_dict["all_index"]
        self.plant_prod_dict = all_params_dict["plant_prod_dict"]
        self.plant_list = list(self.plant_prod_dict.keys())            #TODO これconstraint_plant_listにすればいける？
        self.prod_plant_dict = all_params_dict["prod_plant_dict"]
        self.all_prod_list = list(self.cs_dict.keys()) 
        #self.objective_func_dict = all_params_dict["objective_func_dict"]    #TODO書き換え
        

        self.ave_month_num = self.ave_sales_info_dict["ave_month_num"]       #在庫月数計算時に販売量何か月平均するか
        self.ave_sales_mode = self.ave_sales_info_dict["ave_sales_mode"]     #平均するときに当月を含むかどうか（含む・含まない）
        
        self.ave_month_dict = self.get_ave_month_dict()
        self.constraint_list = all_params_dict["constraint_list"]                              #今回のシミュで使う制約条件の名前リスト
        

        
        self.constraint_period_dict = all_params_dict["constraint_period_dict"]      #制約期間指定できるものの辞書
        
        self.single_factory_prod_list = all_params_dict["single_factory_prod_list"]
        
        
        
        self.prod_month_list = all_params_dict["prod_month_list"]                     #確定生産量固定月
        self.sales_month_list = all_params_dict["sales_month_list"]                   #確定販売量固定月
        
        
        
        self.logfile_dir = "./定式化log/"
        

        
        self.timelimit = timelimit                     #最適化計算の
        
        
        
    
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
    
    
    
    def fuka_less_constraint(self):
        """
        # 制約条件 (各月各工場の負荷時間以下）(絶対制約)
         
         このまま描いてtryexceptにするか、⇒やめた
         
         monthだけないなんてことはない。
         plantと品種の辞書が欲しい。
        
        """
        
        #ある工場ある月ある品種の生産時間(生産量達成率加味)なんでこれ100かけてるんだっけ？⇒逆数だから
        
        
        #for plant in self.plant_list:

        for plant in self.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
        
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
                        if month in self.sales_month_list:
                            
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
                        if month in self.prod_month_list:
                            #self.problem += self.x[plant,month,prod_name] == self.finalized_prod_dict[prod_name][plant][month]
                     
                            if self.finalized_prod_dict[prod_name][plant][month] > 0:
                                self.problem += self.x[plant,month,prod_name] >= self.finalized_prod_dict[prod_name][plant][month] -1
                                self.problem += self.x[plant,month,prod_name] <= self.finalized_prod_dict[prod_name][plant][month] +1
                            
                            if self.finalized_prod_dict[prod_name][plant][month] ==  0:
                                self.problem += self.x[plant,month,prod_name] == self.finalized_prod_dict[prod_name][plant][month]
    
    
    
    
    def within_range_prod_constraint(self):
        #対象範囲の月に関して、制約追加。
        for prod_name in self.finalized_prod_dict.keys():
                for plant in self.finalized_prod_dict[prod_name].keys():
                    for month in self.finalized_prod_dict[prod_name][plant].keys():
                        if (month not in self.prod_month_list) and (month in self.jissui_month_list):
                            
                            delta_x = (self.x[plant,month,prod_name] - self.finalized_prod_dict[prod_name][plant][month]+1)/(self.finalized_prod_dict[prod_name][plant][month]+1)
                            self.problem += self.del_x_min <= delta_x
                            self.problem += self.del_x_max >= delta_x
    
    
    def within_range_sales_constraint(self):

        for prod_name in self.finalized_sales_dict.keys():
                for plant in self.finalized_sales_dict[prod_name].keys():
                    for month in self.finalized_sales_dict[prod_name][plant].keys():
                        if (month not in self.sales_month_list) and (month in self.jissui_month_list):

                            delta_y = (self.y[plant,month,prod_name] - self.finalized_sales_dict[prod_name][plant][month]+1)/(self.finalized_sales_dict[prod_name][plant][month]+1)
                            self.problem += self.del_y_min <= delta_y
                            self.problem += self.del_y_max >= delta_y
    
    
    
    
    def constraint_function(self):
        
        #TODO なんとか割合でやる方法考える
        self.fuka_less_constraint()               #負荷時間以下制約
        self.sum_sales_constraint()               #合計販売量一致制約
        self.not_minus_stock_constraint()         #月末在庫0以上制約
        self.finalized_prod_constraint()          #確定生産量一致制約
        self.finalized_sales_constraint()         #確定販売量一致制約
        self.within_range_prod_constraint()      #生産量がmin_max範囲内にある制約  
        self.within_range_sales_constraint()      #販売量がmin_max範囲内にある制約
        
        #maxとminの大小関係
        self.problem += self.del_x_max - self.del_x_min >= 0
        self.problem += self.del_y_max - self.del_y_min >= 0
        
    
    def objective_function(self):
        self.problem += - (self.del_x_max - self.del_x_min + self.del_y_max - self.del_y_min)
        
    
    def modeling(self):
        self.problem = pulp.LpProblem(name='anbun', sense=pulp.LpMaximize)        #最大化問題
        
        #決定変数
        #制約条件が無さ過ぎる場合、lowboundやupboundの値になる。upboundはNoneなので、Noneがそのまま答えになるので注意
        self.x = pulp.LpVariable.dicts('x', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種生産量(本当に販売できる分 (生産量達成率をかけた後))
        self.y = pulp.LpVariable.dicts('y', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種販売量

        self.del_x_min = pulp.LpVariable('del_x_min', cat='Continuous')             #確定生産量との差の最小値
        self.del_x_max = pulp.LpVariable('del_x_max', cat='Continuous')             #確定生産量との差の最大値
        self.del_y_min = pulp.LpVariable('del_y_min', cat='Continuous')             #確定販売量との差の最小値
        self.del_y_max = pulp.LpVariable('del_y_max', cat='Continuous')             #確定販売量との差の最大値
        
        
        
        #制約条件
        self.constraint_function()
        
        
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
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    print(plant+" "+month+" "+prod_name+"生産量：",self.x[plant,month,prod_name].value())
                    print(plant+" "+month+" "+prod_name+"販売量：",self.y[plant,month,prod_name].value())

        
        print(pulp.LpStatus[self.status])
        
        
        # 目的関数値の取得
        self.objective_value = self.problem.objective.value()
        
        return self.x, self.y, self.status, self.objective_value
        




#######################################################################################
if __name__ == "__main__":
    with open('./test/all_params_dict.pickle', 'rb') as f:
        all_params_dict = pickle.load(f)
    prod_amount_dict,sales_amount_dict,status = MipCore(all_params_dict).main()
    mip_result_dict = {"prod_amount_dict":prod_amount_dict,"sales_amount_dict":sales_amount_dict}
        
    with open("./結果/mip_result_dict.pickle", mode='wb') as f:
        pickle.dump(mip_result_dict,f)
                
        
        
        

    
        
    
    