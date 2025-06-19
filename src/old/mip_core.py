import pulp
import datetime
import pickle
from index_generator import CommonProcess

class MipCore():
    """
    混合整数計画法実装
    
    
    
    """
    def __init__(self,all_params_dict,obj_name,additional_constraint_dict):
        
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
        self.M = self.get_big_M()
        self.m = self.get_small_m()                                #生産量としてありえない小さい値(本当は計算で求めたい。ちょっと大きすぎるケースあるかも)
        self.plant_prod_dict = all_params_dict["plant_prod_dict"]
        self.plant_list = list(self.plant_prod_dict.keys())            #TODO これconstraint_plant_listにすればいける？
        self.prod_plant_dict = all_params_dict["prod_plant_dict"]
        self.all_prod_list = list(self.cs_dict.keys()) 
        #self.objective_func_dict = all_params_dict["objective_func_dict"]    #TODO書き換え
        

        self.ave_month_num = self.ave_sales_info_dict["ave_month_num"]       #在庫月数計算時に販売量何か月平均するか
        self.ave_sales_mode = self.ave_sales_info_dict["ave_sales_mode"]     #平均するときに当月を含むかどうか（含む・含まない）
        
        self.ave_month_dict = self.get_ave_month_dict()
        self.constraint_list = all_params_dict["constraint_list"]                              #今回のシミュで使う制約条件の名前リスト
        
        self.all_constraint_functions = {#"負荷時間一致制約":self.fuka_equal_constraint,
                                         "負荷時間以下制約":self.fuka_less_constraint,
                                         "合計販売量一致制約":self.sum_sales_constraint,
                                         "月末在庫0以上制約":self.not_minus_stock_constraint,
                                         "最低生産回数以上制約":self.num_production_constraint_min,
                                         "最大生産回数以下制約":self.num_production_constraint_max,
                                         "基準在庫月数Min以上制約":self.within_basic_stock_constraint_min,
                                         "基準在庫月数Max以下制約":self.within_basic_stock_constraint_max,
                                         "最低連続生産時間以上制約":self.min_continuous_constraint,
                                         "確定生産量一致制約":self.finalized_prod_constraint,
                                         "確定販売量一致制約": self.finalized_sales_constraint}
        
        self.constraint_period_dict = all_params_dict["constraint_period_dict"]      #制約期間指定できるものの辞書
        
        self.single_factory_prod_list = all_params_dict["single_factory_prod_list"]
        
        
        self.logfile_dir = "./定式化log/"
        
        
        
        self.obj_name = obj_name                 #目的関数の名前
        self.additional_constraint_dict = additional_constraint_dict   #追加の制約条件
        
        #もともとは目的関数だが、階層的最適化をするにあたり、制約条件として使うとき
        self.all_obj_constraint_functions = {"L4 3XRW と L6 3XRSW の合計生産量一致制約":self.w_sw_constraint,
                                             "サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量一致制約":self.sub_prod_constraint,
                                             "合計生産時間一致制約":self.prod_time_constraint}
    
    
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
        
        

    
    def delta_subdelta_constraint(self):
        """
        δ（とサブδ）のための制約条件。
        
        """
        
        for index in self.all_index:
            self.problem += self.x[index]-self.M*self.delta[index] <= 0
            self.problem += self.x[index] - self.m >= -self.M*self.subdelta[index]
            self.problem += self.delta[index]+self.subdelta[index] == 1
            
    
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
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) <= (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant]) == (self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month])

    
    
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
                    self.problem += self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100 >= self.delta[plant,month,prod_name]*self.min_continuous_dict[prod_name][plant][month]

    
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
        
        """
        self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
                        pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list])
        
        
    def sub_prod_obj_function(self):
        """
        サブ品種（L2 4UAW、L3 2UAW、L6 3XR-UWD）の推定期間での合計生産量を最小化
        
        基本は最大化問題として解きたい（これは好み）ので、符号を逆転させる
        
        """
        
        self.problem += -(pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list]))
                       
        
    
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
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list)
        
        
            
    
    def objective_function(self):
        """
        目的関数部分
        #TODO やり方やばいのでいいかんじにしたい。if文無しで実装したい。
        
        
        """
        
        # print(self.obj_name)
        # import time
        # time.sleep(5)
        if self.obj_name == "L4 3XRW と L6 3XRSW の合計生産量を最大化":
            self.w_sw_prod_obj_function()
        
        if self.obj_name == "サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量を最小化":
            self.sub_prod_obj_function()
        
        
        if self.obj_name == "合計生産時間最大化":
            self.prod_time_obj_function()
        
    
    
    def w_sw_constraint(self):
        # self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
        #                 pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) == self.additional_constraint_dict["L4 3XRW と L6 3XRSW の合計生産量一致制約"]
    
        self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
                        pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) <= self.additional_constraint_dict["L4 3XRW と L6 3XRSW の合計生産量一致制約"]+0.1
    
        self.problem += pulp.lpSum([self.x["L4",month,"3XR-1"] for month in self.jissui_month_list]) + \
                        pulp.lpSum([self.x["L6",month,"3XR-1SW"] for month in self.jissui_month_list]) >= self.additional_constraint_dict["L4 3XRW と L6 3XRSW の合計生産量一致制約"]-0.1
    
    
    
    
    
    
    def sub_prod_constraint(self):
        """
        目的関数の値はマイナス付きなので、ここは絶対値しとかないといけない。
        
        """
        
        # print(-self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量一致制約"])
        # import time
        # time.sleep(10)
        
        
        # self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
        #                pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list]) == abs(self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量一致制約"])
                       
        self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list]) <= abs(self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量一致制約"])+0.1
        
        self.problem += pulp.lpSum([self.x["L2",month,"4UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L3",month,"2UAW"] for month in self.jissui_month_list]) + \
                       pulp.lpSum([self.x["L6",month,"3XR-1UWD"] for month in self.jissui_month_list]) >= abs(self.additional_constraint_dict["サブ品種（L2 4UAW、L3 2UAW、L6 3XR-1UWD）の合計生産量一致制約"])-0.1
    
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
                    prod_time = self.x[plant,month,prod_name]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        #self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) == self.additional_constraint_dict["合計生産時間一致制約"]
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) >= self.additional_constraint_dict["合計生産時間一致制約"] -0.1
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.plant_list) <= self.additional_constraint_dict["合計生産時間一致制約"] +0.1
    
    

    
    def modeling(self):
        self.problem = pulp.LpProblem(name='anbun', sense=pulp.LpMaximize)        #最大化問題
        
        #決定変数
        #制約条件が無さ過ぎる場合、lowboundやupboundの値になる。upboundはNoneなので、Noneがそのまま答えになるので注意
        self.x = pulp.LpVariable.dicts('x', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種生産量(本当に販売できる分 (生産量達成率をかけた後))
        self.y = pulp.LpVariable.dicts('y', self.all_index, lowBound=0,cat='Continuous')             #各工場各月各品種販売量
        self.delta = pulp.LpVariable.dicts('delta', self.all_index, cat='Binary')                    #各工場各月各品種生産量が0のとき0 0でない時1をとるバイナリ変数
        self.subdelta = pulp.LpVariable.dicts('subdelta', self.all_index, cat='Binary')              #⇑を確実に実施するために必要 

        
        
        #制約条件
        self.delta_subdelta_constraint()               #これは必要
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
        self.status = self.problem.solve()
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
                    print(plant+" "+month+" "+prod_name+"デルタ：",self.delta[plant,month,prod_name].value())
        
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
                
        
        
        

    
        
    
    