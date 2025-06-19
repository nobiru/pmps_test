import pulp




class ModelVariablesRelaxation:
    """
    最適化問題における変数を定義するクラス
    
    特に制約緩和問題を解くための変数定義。
    
    
    
    """
    def __init__(self,all_params_dict):
        
        self.jissui_month_list = all_params_dict["jissui_month_list"]
        self.split_month_list = self.get_split_month_list(self.jissui_month_list)
        
        
        #self.fuka_dict = all_params_dict["fuka_dict"]
        #self.ave_switch_dict = all_params_dict["ave_switch_dict"]
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
        
        self.prod_capacity_dict = all_params_dict["prod_capacity_dict"]      #生産キャパシティ
        self.achieve_rate_dict = all_params_dict["achieve_rate_dict"]
        self.all_index = all_params_dict["all_index"]
        
        
        
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
        
        self.constraint_period_dict = all_params_dict["constraint_period_dict"]      #制約期間指定できるものの辞書
        
        self.single_factory_prod_list = all_params_dict["single_factory_prod_list"]
        
        
        self.rare_prod_list = all_params_dict["rare_prod_list"]
        self.sub_prod_list = all_params_dict["sub_prod_list"]
        self.priority_sva_prod_list = all_params_dict["priority_sva_prod_list"]
        
        
        self.prod_capacity_dict = all_params_dict["prod_capacity_dict"]      #生産キャパシティ
        
        
        self.logfile_dir = "./定式化log/"
        
        
        
        self.M = self.get_big_M()
        self.M_prod = self.get_big_M_prod()
        
        self.m = self.get_small_m()                                #生産量としてありえない小さい値(本当は計算で求めたい。ちょっと大きすぎるケースあるかも)
        self.M_stock_min = self.get_big_M_stock_min()
        self.M_stock_max = self.get_big_M_stock_max()
        self.m_stock_min = -0.1
        self.m_stock_max = -0.1
        
        
        
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
    
    
    def get_big_M_prod(self):
        """
        生産フラグ用
        
        負荷時間をもとにMを決めているので、
        負荷時間足りないようなケースで不適。
        
        
        """
        M_prod = {}
        for index in self.all_index:
            plant = index[0]
            month = index[1]
            prod = index[2]
            
            #負荷時間
            fuka_time = self.prod_capacity_dict[plant][month]["暦日時間"] - (self.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.prod_capacity_dict[plant][month]["保全"]+
                                                                             self.prod_capacity_dict[plant][month]["計画停止"])
            
            #最大生産量
            max_prod_amount = fuka_time*(self.width_dict[prod]*self.cs_dict[prod][plant][month]*60*self.achieve_rate_dict[prod][plant][month])
            
            #M_prod[index] = (10 + max_prod_amount*1.2/1000)*2   #1.2は安全係数、1000で割って千平米に。10足すのは一か月丸ごと生産しない場合があるから
            M_prod[index] = (10 + max_prod_amount*1.01/1000)
        
        return M_prod
    
    
            
    
    def get_big_M_stock_min(self):
        """
        年間通してどの工場でも全く生産しなかった場合が在庫の理論限界
        
        """
        
        M_stock_min = {}
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = sum(self.sales_dict[month2][prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        index = self.jissui_month_list.index(month)   
                        #何も生産しなかったとしたときの在庫（しかも複数工場から出荷できる品種も単一工場から販売されると仮定）
                        min_stock = self.init_stock_dict[prod_name][plant] - \
                            sum(self.sales_dict[month2][prod_name] for month2 in self.jissui_month_list[:index+1])
                        
                        #正方向の最大値
                        shortage_stock_max = 10 + (ave_sales*(self.basic_stock_min_dict[prod_name][plant][month]) - min_stock)  #全部が0の可能性あるので10つけとく
                        
                        #####################
                        
                        #累積最大生産量
                        cum_prod_amount = sum(self.M_prod[(plant,month2,prod_name)] for month2 in self.jissui_month_list[:index+1])
                        max_stock = self.init_stock_dict[prod_name][plant] + cum_prod_amount     #最大の在庫量
                        
                        
                        shortage_stock_min = (ave_sales*(self.basic_stock_min_dict[prod_name][plant][month]) - max_stock) -10
                        
                        
                        M_stock_min[(plant,month,prod_name)] = max(abs(shortage_stock_max),abs(shortage_stock_min))
                        
        return M_stock_min
        
        
        
        
    
    def get_big_M_stock_max(self):
        M_stock_max = {}
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                for prod_name in self.plant_prod_dict[plant]:
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = sum(self.sales_dict[month2][prod_name] for month2 in self.ave_month_dict[month])/len(self.ave_month_dict[month])
                        
                        index = self.jissui_month_list.index(month)   
                        #何も生産しなかったとしたときの在庫（しかも複数工場から出荷できる品種も単一工場から販売されると仮定）
                        min_stock = self.init_stock_dict[prod_name][plant] - \
                            sum(self.sales_dict[month2][prod_name] for month2 in self.jissui_month_list[:index+1])
                        
                        #負方向の最大値
                        over_stock_max = min_stock - ave_sales*(self.basic_stock_max_dict[prod_name][plant][month])  -10
                        
                        #####################
                        
                        #累積最大生産量
                        cum_prod_amount = sum(self.M_prod[(plant,month2,prod_name)] for month2 in self.jissui_month_list[:index+1])
                        max_stock = self.init_stock_dict[prod_name][plant] + cum_prod_amount     #最大の在庫量
                        
                        #正方向の最大値
                        over_stock_min = 10+(max_stock - ave_sales*(self.basic_stock_min_dict[prod_name][plant][month]))  #全部が0の可能性あるので10つけとく
                        
                        
                        M_stock_max[(plant,month,prod_name)] = max(abs(over_stock_max),abs(over_stock_min))
        
        return M_stock_max
    
    
    
    
    
    
    
    
    
    def get_small_m(self):
        """
        クソちびm
        
        生産時間0.5時間、CS10、幅1.15 で作った時の平米とする。
        単位は千平米
        """
        
        m = 0.5*10*60*1.15/1000
        return m
    
    
    
    
    
    
    

    def define_variables(self):
        """
        決定変数の定義
        
        """
        #決定変数
        #制約条件が無さ過ぎる場合、lowboundやupboundの値になる。upboundはNoneなので、Noneがそのまま答えになるので注意
        self.x = pulp.LpVariable.dicts('x', self.all_index, lowBound=0,cat='Continuous',upBound=10000)             #各工場各月各品種生産量(本当に販売できる分 (生産量達成率をかけた後))
        self.y = pulp.LpVariable.dicts('y', self.all_index, lowBound=0,cat='Continuous',upBound=100000)             #各工場各月各品種販売量
        self.z = pulp.LpVariable.dicts('z', self.all_index, lowBound=0,cat='Continuous',upBound=100000)             #各工場各月各品種在庫量
        self.delta = pulp.LpVariable.dicts('delta', self.all_index, cat='Binary')                    #各工場各月各品種生産量が0のとき0 0でない時1をとるバイナリ変数
        self.subdelta = pulp.LpVariable.dicts('subdelta', self.all_index, cat='Binary')              #⇑を確実に実施するために必要 
        
        self.delta_z = pulp.LpVariable.dicts('delta_z', self.all_index, cat='Binary')                    #各工場各月各品種在庫量が基準在庫Max以下のとき0 超過のとき1をとるバイナリ変数
        
        
        self.subdelta_z = pulp.LpVariable.dicts('subdelta_z', self.all_index, cat='Binary')              #⇑を確実に実施するために必要
        
        self.delta_mz = pulp.LpVariable.dicts('delta_mz', self.all_index, cat='Binary')                    #各工場各月各品種在庫量が基準在庫Min以下のとき1 超過のとき0をとるバイナリ変数
        self.subdelta_mz = pulp.LpVariable.dicts('subdelta_mz', self.all_index, cat='Binary')              #⇑を確実に実施するために必要
        
        #その月に品種の生産自体があるかどうかを示すフラグ
        self.all_prod_flag = pulp.LpVariable.dicts('all_prod_flag', self.plant_month_index, cat='Binary')   #その月に品種の生産自体があるかどうかを示すフラグ
        
        #月内切替時間を格納するための変数
        self.switch_time = pulp.LpVariable.dicts('switch_time', self.plant_month_index, cat='Continuous',
                                                 lowBound=-100,upBound=1000)   #回帰から得られる値的に、負の値も取りうるのでlowBoundは設けない。
        
        #dope1:L1:CT,L3:UA,L6:TAC     #dope2:L1:SANUQI,L3:SVA,L6:SAZMA
        self.dope1_flag = pulp.LpVariable.dicts('dope1_flag', self.plant_month_index, cat='Binary')   #ドープ1がその月生産ある場合は1、ない場合は0
        self.dope2_flag = pulp.LpVariable.dicts('dope2_flag', self.plant_month_index, cat='Binary')   #ドープ2がその月生産ある場合は1、ない場合は0
        #self.dope3_flag = pulp.LpVariable.dicts('dope3_flag', self.plant_month_index, cat='Binary')   #ドープ3がその月生産ある場合は1、ない場合は0
        

        

        self.inter_switch_1to2_flag = pulp.LpVariable.dicts('inter_switch_1to2_flag', self.plant_month_index, cat='Binary')   #月間にドープ1⇒ドープ2の切替が発生する場合1、しない場合0
        self.inter_switch_2to1_flag = pulp.LpVariable.dicts('inter_switch_2to1_flag', self.plant_month_index, cat='Binary')   #月間にドープ2⇒ドープ1の切替が発生する場合1、しない場合0
        
        
        #月間切替時間を格納するための変数 #TODO回帰の結果得られる値が絶対に負にならないようにしておかないと解無し。
        #いや、意外と大丈夫かも。月間誤差、月内誤差のこと踏まえると、low_bound=-48しとく？
        self.inter_switch_time_head = pulp.LpVariable.dicts('inter_switch_time_head', self.plant_month_index, 
                                                         cat='Continuous',lowBound=-0.01,upBound=1000)   #今月の頭に按分された切替時間
        self.inter_switch_time_tail = pulp.LpVariable.dicts('inter_switch_time_tail', self.plant_month_index, 
                                                         cat='Continuous',lowBound=-0.01,upBound=1000)   #今月のお尻に按分された切替時間


        ##slack変数（負荷時間違反しているのがどのくらいか。）
        #self.slack = pulp.LpVariable.dicts('slack', self.plant_month_index, lowBound=0,cat='Continuous')             #各工場各月の負荷時間のスラック変数
        self.slack = pulp.LpVariable.dicts('slack', self.plant_month_index,cat='Continuous',lowBound=0,upBound=2000)             #各工場各月の負荷時間のスラック変数
        