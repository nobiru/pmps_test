import pulp
from model_variables import ModelVariables

class ConstraintsCatalog:
    """
    制約条件のカタログクラス。
    解きたい問題に応じて制約条件を選択する。
    
    
    """
    def __init__(self,variables: ModelVariables,problem):
        self.variables: ModelVariables = variables       #変数を格納したインスタンス
        self.problem = problem                           #最適化問題を格納したインスタンス
        
        
        self.all_constraint_functions = {#"負荷時間一致制約":self.fuka_equal_constraint,
                                         "負荷時間以下制約":self.fuka_less_constraint_5,
                                         #"負荷時間以下制約":self.fuka_less_constraint_2,
                                         "合計販売量一致制約":self.sum_sales_constraint,
                                         "月末在庫0以上制約":self.not_minus_stock_constraint,
                                         "最低生産回数以上制約":self.num_production_constraint_min,
                                         "最大生産回数以下制約":self.num_production_constraint_max,
                                         "基準在庫月数Min以上制約":self.within_basic_stock_constraint_min2,
                                         "基準在庫月数Max以下制約":self.within_basic_stock_constraint_max2,
                                         "最低連続生産時間以上制約":self.min_continuous_constraint,
                                         "確定生産量一致制約":self.finalized_prod_constraint,
                                         "確定販売量一致制約": self.finalized_sales_constraint,
                                         "負荷時間以下スラック付き制約":self.fuka_less_constraint_slack,
                                         }
        
        
        #もともとは目的関数だが、階層的最適化をするにあたり、制約条件として使うとき
        self.all_obj_constraint_functions = {#"長時間ドープ切り替え回数一致制約":self.long_dope_switch_constraint,
                                             #"SAZMA系品種連続生産月数一致制約":self.sazma_continuous_constraint,
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
                                             "メインドープによる立上・立下回数一致制約":self.main_dope_num_constraint,
                                             "メイン品種生産量一致制約":self.main_prod_amount_constraint,
                                             "合計切替時間一致制約":self.total_switch_time_constraint,
                                             "長時間ドープ切替工場合計切替時間一致制約":self.long_dope_total_switch_time_constraint,
                                             "合計生産回数一致制約":self.total_prod_num_constraint,
                                             "負荷時間スラック変数合計一致制約":self.slack_sum_constraint,
                                             "生産イベント月数一致制約":self.prod_month_constraint,
                                             "余力時間一致制約":self.spare_time_constraint,
                                             "余力時間一致制約2":self.spare_time_constraint2,
                                             "基準在庫月数違反回数一致制約":self.stock_range_constraint,
                                             "7桁在庫月数合計一致制約":self.stock_num_7_constraint,
                                             "7桁基準在庫月数Min以上制約違反回数一致制約":self.shortage_stock_7_constraint,
                                            "7桁基準在庫月数Max以下制約違反回数一致制約":self.over_stock_7_constraint,
                                            "年度末7桁基準在庫月数Min以上制約違反回数一致制約":self.end_shortage_stock_7_constraint,
                                             }
        
    
    
    def delta_subdelta_constraint(self):
        """
        生産フラグ δ（とサブδ）のための制約条件。
        delta:生産フラグ
        
        """
        
        for index in self.variables.all_index:
            # self.problem += self.variables.x[index]-self.variables.M*self.variables.delta[index] <= 0
            # self.problem += self.variables.x[index] - self.variables.m >= -self.variables.M*self.variables.subdelta[index]
            # self.problem += self.variables.delta[index]+self.variables.subdelta[index] == 1
            
            ##24/11/26変更
            # self.problem += self.variables.x[index] <= self.variables.M*(1-self.variables.subdelta[index])
            # self.problem += self.variables.x[index] >= self.variables.m - self.variables.M*self.variables.subdelta[index]
            # self.problem += self.variables.delta[index]+self.variables.subdelta[index] == 1
            
            ##24/11/26変更
            self.problem += self.variables.x[index] <= self.variables.M_prod[index]*(1-self.variables.subdelta[index])
            self.problem += self.variables.x[index] >= self.variables.m - self.variables.M_prod[index]*self.variables.subdelta[index]
            self.problem += self.variables.delta[index]+self.variables.subdelta[index] == 1
            
            
    def z_variable_constraint(self):
        """
        変数zを各工場各月各品種の月末在庫にするための制約
        
        """
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    index = self.variables.jissui_month_list.index(month)   
                    #z=月末在庫とするための制約
                    self.problem += self.variables.z[plant,month,prod_name] == self.variables.init_stock_dict[prod_name][plant] + \
                                    pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - \
                                    pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])

    
    def delta_subdelta_constraint_z(self):
        """
        delta_z:在庫MAXと比較して、超過していれば1、超過していなければ0を返すフラグ
        δ（とサブδ）のための制約条件。
        
        
        over_stock > 0 → delta_z = 1, subdelta_z = 0
        over_stock < m → delta_z = 0, subdelta_z = 1
        m ≤ over_stock ≤ 0 → delta_z = 0, subdelta_z = 1
        
        """
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    if (plant,month,prod_name) in self.variables.multi_plant_prod_index:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                        
                        over_stock = self.variables.z[plant,month,prod_name] - ave_sales*(self.variables.basic_stock_max_dict[prod_name][plant][month])
                        
                        #TODO over_stockがぴったり0のときどうなっている？？調べたい ←ピッタリゼロのときにカウントしないようにmが必要。
                        # self.problem += over_stock-self.variables.M*self.variables.delta_z[plant,month,prod_name] <= 0
                        # self.problem += over_stock - self.variables.m >= -self.variables.M*self.variables.subdelta_z[plant,month,prod_name]
                        # self.problem += self.variables.delta_z[plant,month,prod_name]+self.variables.subdelta_z[plant,month,prod_name] == 1
                        
                        ##24/11/26変更
                        self.problem += over_stock <= self.variables.M_stock_max[(plant,month,prod_name)]*(1-self.variables.subdelta_z[plant,month,prod_name])
                        self.problem += over_stock >= self.variables.m_stock_max - self.variables.M_stock_max[(plant,month,prod_name)]*self.variables.subdelta_z[plant,month,prod_name]
                        self.problem += self.variables.delta_z[plant,month,prod_name]+self.variables.subdelta_z[plant,month,prod_name] == 1
                        
    
    def delta_subdelta_constraint_mz(self):
        """
        δ（とサブδ）のための制約条件。
        
        shortage_stock > 0 → delta_mz = 1, subdelta_mz = 0
        shortage_stock < m → delta_mz = 0, subdelta_mz = 1
        m ≤ shortage_stock ≤ 0 → delta_mz = 0, subdelta_mz = 1
        
        
        """
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    if (plant,month,prod_name) in self.variables.multi_plant_prod_index:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                        
                        #shortage_stock：下限を割っているときに正の値。下限を割っていないときに負の値。
                        shortage_stock = ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month]) - self.variables.z[plant,month,prod_name]
                        
                        # self.problem += shortage_stock-self.variables.M*self.variables.delta_mz[plant,month,prod_name] <= 0
                        # self.problem += shortage_stock - self.variables.m >= -self.variables.M*self.variables.subdelta_mz[plant,month,prod_name]
                        # self.problem += self.variables.delta_mz[plant,month,prod_name]+self.variables.subdelta_mz[plant,month,prod_name] == 1
                        
                        ##24/11/26変更
                        self.problem += shortage_stock <= self.variables.M_stock_min[(plant,month,prod_name)]*(1-self.variables.subdelta_mz[plant,month,prod_name])
                        self.problem += shortage_stock >= self.variables.m_stock_min - self.variables.M_stock_min[(plant,month,prod_name)]*self.variables.subdelta_mz[plant,month,prod_name]
                        self.problem += self.variables.delta_mz[plant,month,prod_name]+self.variables.subdelta_mz[plant,month,prod_name] == 1
            
    
    
    
    
    
    def delta_subdelta_constraint_7_z(self):
        """
        delta_7_z:7桁在庫MAXと比較して、超過していれば1、超過していなければ0を返すフラグ
        δ（とサブδ）のための制約条件。
        
        
        over_stock > 0 → delta_z = 1, subdelta_z = 0
        over_stock < m → delta_z = 0, subdelta_z = 1
        m ≤ over_stock ≤ 0 → delta_z = 0, subdelta_z = 1
        
        """
        for month in self.variables.jissui_month_list:
            for prod_name in self.variables.all_prod_list:
                #翌月以降〇ヶ月の7桁平均販売量（ひと月当たり）
                ave_sales = pulp.lpSum(self.variables.sales_dict[month2][prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                
                #7桁在庫量
                stock_7 = pulp.lpSum(self.variables.z[plant,month,prod_name] for plant in self.variables.prod_plant_dict[prod_name])
                
                #7桁在庫月数最大値（複数工場の場合は小さいほうにする（#TODO 田村さんに確認必要））
                basic_stock_max_7 = min([self.variables.basic_stock_max_dict[prod_name][plant][month] for plant in self.variables.prod_plant_dict[prod_name]])
                
                
                over_stock = stock_7 - ave_sales*basic_stock_max_7
                
                #TODO M_stock_maxの7桁版が必要
                
                M_stock_max_7 = pulp.lpSum(self.variables.M_stock_max[(plant,month,prod_name)] for plant in self.variables.prod_plant_dict[prod_name])
                
                #TODO m_stock_maxの7桁版が必要
                
                
                
                self.problem += over_stock <= M_stock_max_7*(1-self.variables.subdelta_7_z[prod_name,month])
                self.problem += over_stock >= self.variables.m_stock_max - M_stock_max_7*self.variables.subdelta_7_z[prod_name,month]
                self.problem += self.variables.delta_7_z[prod_name,month]+self.variables.subdelta_7_z[prod_name,month] == 1
    
    
    
    def delta_subdelta_constraint_7_mz(self):
        """
        δ（とサブδ）のための制約条件。
        
        shortage_stock > 0 → delta_mz = 1, subdelta_mz = 0
        shortage_stock < m → delta_mz = 0, subdelta_mz = 1
        m ≤ shortage_stock ≤ 0 → delta_mz = 0, subdelta_mz = 1
        
        
        """
        for month in self.variables.jissui_month_list:
            for prod_name in self.variables.all_prod_list:
                
                
                #翌月以降〇ヶ月の7桁平均販売量（ひと月当たり）
                ave_sales = pulp.lpSum(self.variables.sales_dict[month2][prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                
                
                #7桁在庫量
                stock_7 = pulp.lpSum(self.variables.z[plant,month,prod_name] for plant in self.variables.prod_plant_dict[prod_name])
                
                
                
                #7桁在庫月数最大値（複数工場の場合は小さいほうにする（#TODO 田村さんに確認必要））
                basic_stock_min_7 = min([self.variables.basic_stock_min_dict[prod_name][plant][month] for plant in self.variables.prod_plant_dict[prod_name]])
                
                
                #shortage_stock：下限を割っているときに正の値。下限を割っていないときに負の値。
                shortage_stock = ave_sales*basic_stock_min_7 - stock_7
                
                # self.problem += shortage_stock-self.variables.M*self.variables.delta_mz[plant,month,prod_name] <= 0
                # self.problem += shortage_stock - self.variables.m >= -self.variables.M*self.variables.subdelta_mz[plant,month,prod_name]
                # self.problem += self.variables.delta_mz[plant,month,prod_name]+self.variables.subdelta_mz[plant,month,prod_name] == 1
                
                M_stock_min_7 = pulp.lpSum(self.variables.M_stock_min[(plant,month,prod_name)] for plant in self.variables.prod_plant_dict[prod_name])
                
                
                self.problem += shortage_stock <= M_stock_min_7*(1-self.variables.subdelta_7_mz[prod_name,month])
                self.problem += shortage_stock >= self.variables.m_stock_min - M_stock_min_7*self.variables.subdelta_7_mz[prod_name,month]
                self.problem += self.variables.delta_7_mz[prod_name,month]+self.variables.subdelta_7_mz[prod_name,month] == 1
    
    
    def dope_flag_constraint_common(self,plant,month,dope_flag_variable,dope_name):
        """
        ドープフラグの制約の共通部分を切り出し
        
        そのドープに属する品種のうち、1品種でも生産する場合は、1、そうでない場合は0
        にするための制約
        
        """
        
        prod_name_list = self.variables.dope_prod_dict[plant][dope_name]                  #そのドープに属する品種リスト
        
        for prod_name in prod_name_list:
            self.problem += dope_flag_variable[plant,month] >= self.variables.delta[plant,month,prod_name]
        
        
        self.problem += dope_flag_variable[plant,month] <= pulp.lpSum(self.variables.delta[plant,month,prod_name]
                                                        for prod_name in prod_name_list)
        
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
        L7   dope1:SVA
    
        """
        for plant in self.variables.plant_list:
            
            dope_num_list = list(self.variables.dopenum_dope_dict[plant].keys())     #その工場のドープ番号リスト
            total_dope_num = len(dope_num_list)                                      #その工場の総ドープ数
            
            
            for month in self.variables.jissui_month_list:
                
                if total_dope_num == 1:
                    self.dope_flag_constraint_common(plant,month,self.variables.dope1_flag,self.variables.dopenum_dope_dict[plant]["dope1"])
                    
                    self.problem += self.variables.dope2_flag[plant,month] == 0
                    self.problem += self.variables.dope3_flag[plant,month] == 0
                
                
                if total_dope_num == 2:
                    #ドープ1のフラグに関する制約
                    self.dope_flag_constraint_common(plant,month,self.variables.dope1_flag,self.variables.dopenum_dope_dict[plant]["dope1"])
                    #print(plant,"dope1",self.variables.dopenum_dope_dict[plant]["dope1"])
                    
                    #ドープ2のフラグに関する制約
                    self.dope_flag_constraint_common(plant,month,self.variables.dope2_flag,self.variables.dopenum_dope_dict[plant]["dope2"])
                    #print(plant,"dope2",self.variables.dopenum_dope_dict[plant]["dope2"])
                    
                    self.problem += self.variables.dope3_flag[plant,month] == 0
                
                if total_dope_num == 3:
                    #ドープ1のフラグに関する制約
                    self.dope_flag_constraint_common(plant,month,self.variables.dope1_flag,self.variables.dopenum_dope_dict[plant]["dope1"])
                    #print(plant,"dope1",self.variables.dopenum_dope_dict[plant]["dope1"])
                    #ドープ2のフラグに関する制約
                    self.dope_flag_constraint_common(plant,month,self.variables.dope2_flag,self.variables.dopenum_dope_dict[plant]["dope2"])
                    #print(plant,"dope2",self.variables.dopenum_dope_dict[plant]["dope2"])
                    #ドープ3のフラグに関する制約
                    self.dope_flag_constraint_common(plant,month,self.variables.dope3_flag,self.variables.dopenum_dope_dict[plant]["dope3"])
                    #print(plant,"dope3",self.variables.dopenum_dope_dict[plant]["dope3"])
                

            

 
    
                   
    def all_prod_flag_constraint(self):
        """
        その月その工場で生産品種が1品種でもある場合は1、ない場合は0
        
        big-Mで定式化するよりもこのように定式化した方がいいらしい。
        
        
        """
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    self.problem += self.variables.all_prod_flag[plant,month] >= self.variables.delta[plant,month,prod_name]
                
                self.problem += self.variables.all_prod_flag[plant,month] <= pulp.lpSum(self.variables.delta[plant,month,prod_name] for 
                                                                                        prod_name in self.variables.plant_prod_dict[plant])
    
    
    
    
    def switch_time_constraint_common(self,plant,month,month_type):
        """
        月中切替時間の制約の、共通部分切り出し
        TODO 2ドープではない工場イケてるのか？これ要確認 ⇒ 1ドープの工場どうしよdope2_flagのところ 
        
        
        """
        switch_time_list = [self.variables.switch_coeff_dict[plant][month][month_type]["intercept"]*
                            self.variables.all_prod_flag[plant,month]]     #切替時間のリスト(先に切片いれとく) 。生産品種が一つもない時は0になる。
                    
        #ドープ毎の品種数の分
        for dope_name in self.variables.dope_prod_dict[plant].keys():
            column_name = dope_name+"品種数"
            switch_time_list.append(self.variables.switch_coeff_dict[plant][month][month_type][column_name]*
                                    pulp.lpSum(self.variables.delta[plant,month,prod_name] 
                                               for prod_name in self.variables.dope_prod_dict[plant][dope_name]))   #ドープ毎

            
            
            
        #ドープ数の分
        switch_time_list.append(self.variables.switch_coeff_dict[plant][month][month_type]["ドープ数"]*
                                pulp.lpSum([self.variables.dope1_flag[plant,month],
                                            self.variables.dope2_flag[plant,month],
                                            self.variables.dope3_flag[plant,month]]))
        
        
        #単独品種の分
        for prod_name in self.variables.plant_prod_dict[plant]:
            switch_time_list.append(self.variables.switch_coeff_dict[plant][month][month_type][prod_name]*
                                    self.variables.delta[plant,month,prod_name])  #品種ごとの切替時間(係数と変数の積)をリストに追加
        
        
        #合計品種数
        switch_time_list.append(self.variables.switch_coeff_dict[plant][month][month_type]["全品種数"]*
                                pulp.lpSum(self.variables.delta[plant,month,prod_name] 
                                           for prod_name in self.variables.plant_prod_dict[plant]))
        
        
        
        
        self.problem += self.variables.switch_time[plant,month] == pulp.lpSum(switch_time_list)
        
    
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
        """
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                if ((self.variables.month_type_dict[plant][month]["保全前期"] == "なし") and (self.variables.month_type_dict[plant][month]["保全後期"] == "なし")):
                    self.switch_time_constraint_common(plant,month,"保全前期なし保全後期なし")
                
                if ((self.variables.month_type_dict[plant][month]["保全前期"] == "あり") and (self.variables.month_type_dict[plant][month]["保全後期"] == "なし")):
                    self.switch_time_constraint_common(plant,month,"保全前期あり保全後期なし")
                
                if ((self.variables.month_type_dict[plant][month]["保全前期"] == "なし") and (self.variables.month_type_dict[plant][month]["保全後期"] == "あり")):
                    self.switch_time_constraint_common(plant,month,"保全前期なし保全後期あり")
                
                if ((self.variables.month_type_dict[plant][month]["保全前期"] == "あり") and (self.variables.month_type_dict[plant][month]["保全後期"] == "あり")):
                    self.switch_time_constraint_common(plant,month,"保全前期あり保全後期あり")
                    
    
    ######## 月間切替に関する制約 ##############################################################################
    
    # def inter_switch_flag_constraint(self):
    #     for plant in self.variables.plant_list:
    #         for i in range(len(self.variables.jissui_month_list)-1):
                
    #             #TODO本当は工場毎に場合分けした方が制約減らせるが。。少なくともL2は3ドープなので何とかしないと。。
                                    
    #             #ドープ1について止める場合1、それ以外0
    #             self.problem += self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]] - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]
    #             self.problem += self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]
                
                
    #             #ドープ2について止める場合1、それ以外0
    #             self.problem += self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]] - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]
    #             self.problem += self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]
            
    #             #やめるドープがある場合1、ない場合0
    #             self.problem += self.variables.stop_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.stop_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.stop_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]] + self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]]
        
                
                
    #             #ドープ1について開始する場合1、それ以外0
    #             self.problem += self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]] - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]
    #             self.problem += self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]
                
                
    #             #ドープ2について開始する場合1、それ以外0
    #             self.problem += self.variables.dope2_start_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]] - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]
    #             self.problem += self.variables.dope2_start_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.dope2_start_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]
            
    #             #開始するドープがある場合1、ない場合0
    #             self.problem += self.variables.start_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.start_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope2_start_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.start_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]] + self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]]
                
                
                
    #             #月間品種切替フラグ
                
    #             self.problem += self.variables.inter_switch_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.stop_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.inter_switch_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.start_flag[plant,self.variables.jissui_month_list[i+1]]
    #             self.problem += self.variables.inter_switch_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.stop_flag[plant,self.variables.jissui_month_list[i+1]] + self.variables.start_flag[plant,self.variables.jissui_month_list[i+1]] - 1
                
    
    
    # def inter_switch_time_constraint(self):
    #     """
    #     変数inter_switch_timeが線形回帰式で表現されるようにするための制約
        
        
    #     #inter_switch_coeff_dict[L1]の中身
    #     {
    #         "intercept":2.1316282072803006e-14
    #         "CT生産終了":-3.5546068472486344e-14
    #         "CT生産開始":4.973799150320701e-14
    #         "SANUQI生産開始":2.6645352591003757e-15
    #         "SANUQI生産終了":-6.128431095930864e-14
    #         "ドープ切替":180.99999999999997
    #         }
        
        
    #     2024年度の場合
    #     L1   dope1:CT dope2:SANUQI
    #     L2   dope1:CT dope2:UA dope3:UY
    #     L3   dope1:UA dope2:SVA
    #     L4   dope1:SVA
    #     L5   dope1:SANUQI
    #     L6   dope1:SVA dope2:SAZMA
    #     L7   dope7:SVA
        
        
    #     self.variables.dope_dict = {"L1":{"dope1":"CT",
    #                             "dope2":"SANUQI"},
    #                       "L2":{"dope1":"CT",
    #                             "dope2":"UA",
    #                             "dope3":"UY"},
    #                       "L3":{"dope1":"UA",
    #                             "dope2":"SVA"},
    #                       "L4":{"dope1":"SVA"},
    #                       "L5":{"dope1":"SANUQI"},
    #                       "L6":{"dope1":"SVA",
    #                             "dope2":"SAZMA"},
    #                       "L7":{"dope1":"SVA"}}
        
        
    #     """
        

    
        
    #     #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
    #     for plant in self.variables.plant_list:
    #         #TODO本当はL2は3ドープ
    #         if plant in ["L1","L3","L6","L2"]:      
                
    #             self.problem += self.variables.inter_switch_time_head[plant,self.variables.jissui_month_list[0]] == 0    #初月はinter_switch_time_headは0にする。
    #             self.problem += self.variables.inter_switch_time_tail[plant,self.variables.jissui_month_list[len(self.variables.jissui_month_list)-1]] == 0  #最終月のinter_switch_tailは0にする
                          
    #             for i in range(len(self.variables.jissui_month_list)-1):
    #                 inter_switch_time_list = [self.variables.inter_switch_coeff_dict[plant]["intercept"]]     #切片
                    
    #                 #dope1生産終了
    #                 dope_name = self.variables.dope_dict[plant]["dope1"]    #dope1
    #                 inter_switch_time_list.append(self.variables.dope1_stop_flag[plant,self.variables.jissui_month_list[i+1]]*
    #                                             self.variables.inter_switch_coeff_dict[plant][f"{dope_name}生産終了"])
                    
    #                 #dope1生産開始
    #                 inter_switch_time_list.append(self.variables.dope1_start_flag[plant,self.variables.jissui_month_list[i+1]]*
    #                                             self.variables.inter_switch_coeff_dict[plant][f"{dope_name}生産開始"])
                    
    #                 #dope2生産終了
    #                 dope_name = self.variables.dope_dict[plant]["dope2"]    #dope2
    #                 inter_switch_time_list.append(self.variables.dope2_stop_flag[plant,self.variables.jissui_month_list[i+1]]*
    #                                             self.variables.inter_switch_coeff_dict[plant][f"{dope_name}生産終了"])
                    
    #                 #dope2生産開始
    #                 inter_switch_time_list.append(self.variables.dope2_start_flag[plant,self.variables.jissui_month_list[i+1]]*
    #                                             self.variables.inter_switch_coeff_dict[plant][f"{dope_name}生産開始"])
                    
                    
    #                 #ドープ切替
    #                 inter_switch_time_list.append(self.variables.inter_switch_coeff_dict[plant]["ドープ切替"]*
    #                                             self.variables.inter_switch_flag[plant,self.variables.jissui_month_list[i+1]])
                    
                    
    #                 #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
    #                 self.problem += self.variables.inter_switch_time_head[plant,self.variables.jissui_month_list[i+1]] + \
    #                     self.variables.inter_switch_time_tail[plant,self.variables.jissui_month_list[i]] == pulp.lpSum(inter_switch_time_list)
        
    #         if plant in ["L4","L5","L7"]:
    #             for i in range(len(self.variables.jissui_month_list)):
    #                  self.problem += self.variables.inter_switch_time_head[plant,self.variables.jissui_month_list[i]] == 0
    #                  self.problem += self.variables.inter_switch_time_tail[plant,self.variables.jissui_month_list[i]] == 0

    
    
    
    
    
    
    def dope_group_flag_constraint(self):
        """
        ドープとグループの関係性に関する制約
        
        そのグループに該当するドープが1つでも生産されれば1、されなければ0
        
        よく考えたらgroup2はいらないかも。基本的にgroup2は1ドープだし。
        すくなくとも2025年度の場合はgroup2はいらない。
        
        """
        
        
        for plant in self.variables.plant_list:
            total_dope_num = len(self.variables.dope_prod_dict[plant].keys())       #その工場の総ドープ数
            for month in self.variables.jissui_month_list:
                
                
                #単一ドープのみ
                if total_dope_num == 1:
                    self.problem += self.variables.group1_flag[plant,month] == self.variables.dope1_flag[plant,month]   #ドープ1が生産されていれば1
                    self.problem += self.variables.group2_flag[plant,month] == 0           #ドープ数一個しかないので。
                    
                #2ドープ:group1とgroup2のフラグはdope1dope2のフラグと一致
                if total_dope_num == 2:
                    self.problem += self.variables.group1_flag[plant,month] == self.variables.dope1_flag[plant,month]   #ドープ1が生産されていれば1
                    self.problem += self.variables.group2_flag[plant,month] == self.variables.dope2_flag[plant,month]   #ドープ1が生産されていれば1
                
                #3dope: #TODO group1にdope1とdope2、group2にdope3である前提
                if total_dope_num == 3:
                    self.problem += self.variables.group1_flag[plant,month] >= self.variables.dope1_flag[plant,month]   #ドープ1が生産されていれば1
                    self.problem += self.variables.group1_flag[plant,month] >= self.variables.dope2_flag[plant,month]   #ドープ2が生産されていれば1
                    self.problem += self.variables.group1_flag[plant,month] <= pulp.lpSum([self.variables.dope1_flag[plant,month],
                                                                                           self.variables.dope2_flag[plant,month]])
                    
                    
                    self.problem += self.variables.group2_flag[plant,month] == self.variables.dope3_flag[plant,month]   #ドープ3が生産されていれば1
                    
    
    def inter_switch_flag_constraint2(self):
        """
        月間切替に関わるフラグの制約
        
        どのドープがgroup1でどのドープがgroupe2なのかなどの情報はここではいらない
        
        
        """
        for plant in self.variables.plant_list:
            for i in range(len(self.variables.jissui_month_list)-1):
                #TODO本当は工場毎に場合分けした方が制約減らせるが。。
                
                #ドープ1⇒ドープ2のドープ切替フラグのための制約     #TODO inter_switch_1to2_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]
                self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]
                self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]
                self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]
                
                self.problem +=  self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]] >= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]] + \
                    (1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]) +\
                    (1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]) + self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]] -3
                
                
                #ドープ2⇒ドープ1のドープ切替フラグのための制約     #TODO inter_switch_2to1_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]
                self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]
                self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]] <= self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]
                self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]] <= 1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]
                
                
                self.problem +=  self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]] >= (1 - self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]) + \
                    self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]] +\
                    self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]] + (1 - self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]) -3
            
            #初期解を保持するためには制約咬ませとかないとソルバーの仕様で消されるため。
            self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[0]] == 0
            self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[0]] == 0
    
    
    
    
    
    
    
    def inter_switch_flag_constraint3(self):
        """
        月間切替に関わるフラグの制約
        
        dopeにしていたところをgroupに変更
        
        
        
        """
        for plant in self.variables.plant_list:
            for i in range(len(self.variables.jissui_month_list)-1):
                #TODO本当は工場毎に場合分けした方が制約減らせるが。。
                
                this_month = self.variables.jissui_month_list[i]
                next_month = self.variables.jissui_month_list[i+1]
                
                #グループ1⇒グループ2のドープ切替フラグのための制約     #TODO inter_switch_1to2_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.variables.inter_switch_1to2_flag[plant,next_month] <= self.variables.group1_flag[plant,this_month]
                self.problem += self.variables.inter_switch_1to2_flag[plant,next_month] <= 1 - self.variables.group1_flag[plant,next_month]
                self.problem += self.variables.inter_switch_1to2_flag[plant,next_month] <= 1 - self.variables.group2_flag[plant,this_month]
                self.problem += self.variables.inter_switch_1to2_flag[plant,next_month] <= self.variables.group2_flag[plant,next_month]
                
                self.problem +=  self.variables.inter_switch_1to2_flag[plant,next_month] >= self.variables.group1_flag[plant,this_month] + \
                    (1 - self.variables.group1_flag[plant,next_month]) +\
                    (1 - self.variables.group2_flag[plant,this_month]) + self.variables.group2_flag[plant,next_month] -3
                
                
                #グループ2⇒グループ1のドープ切替フラグのための制約     #TODO inter_switch_2to1_flagの添え字をiにすべきか、i+1にすべきかは要検討
                self.problem += self.variables.inter_switch_2to1_flag[plant,next_month] <= 1 - self.variables.group1_flag[plant,this_month]
                self.problem += self.variables.inter_switch_2to1_flag[plant,next_month] <= self.variables.group1_flag[plant,next_month]
                self.problem += self.variables.inter_switch_2to1_flag[plant,next_month] <= self.variables.group2_flag[plant,this_month]
                self.problem += self.variables.inter_switch_2to1_flag[plant,next_month] <= 1 - self.variables.group2_flag[plant,next_month]
                
                
                self.problem +=  self.variables.inter_switch_2to1_flag[plant,next_month] >= (1 - self.variables.group1_flag[plant,this_month]) + \
                    self.variables.group1_flag[plant,next_month] +\
                    self.variables.group2_flag[plant,this_month] + (1 - self.variables.group2_flag[plant,next_month]) -3
            
            #初期解を保持するためには制約咬ませとかないとソルバーの仕様で消されるため。
            self.problem += self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[0]] == 0
            self.problem += self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[0]] == 0
    
    
    
    
    
    
    def inter_switch_time_constraint2_common(self,coeff_dict,plant,group1_name,group2_name,
                                             case_name,i):
        """
        共通要素
        
        
        #TODO dope1とgroup1
        dope2とgroup2が対応してなければならない？
        
        
        
        
        """
        month = self.variables.jissui_month_list[i]
        
        inter_switch_time_list = [coeff_dict[plant][month]["intercept"]]     #切片
        
        #i月にgroup1を作るかどうか
        inter_switch_time_list.append(self.variables.dope1_flag[plant,self.variables.jissui_month_list[i]]*
                                coeff_dict[plant][month][f"前月_{group1_name}"])
        
        #i+1月にgroup1を作るかどうか
        inter_switch_time_list.append(self.variables.dope1_flag[plant,self.variables.jissui_month_list[i+1]]*
                                coeff_dict[plant][month][f"当月_{group1_name}"])
        
        
        #ドープグループが2つの工場
        if group2_name is not None:
            #i月にdope2を作るかどうか
            inter_switch_time_list.append(self.variables.dope2_flag[plant,self.variables.jissui_month_list[i]]*
                                    coeff_dict[plant][month][f"前月_{group2_name}"])
            
            
            #i+1月にdope2を作るかどうか
            inter_switch_time_list.append(self.variables.dope2_flag[plant,self.variables.jissui_month_list[i+1]]*
                                    coeff_dict[plant][month][f"当月_{group2_name}"])
            
            
            #dope1⇒dope2のドープ切替があるかどうか
            inter_switch_time_list.append(self.variables.inter_switch_1to2_flag[plant,self.variables.jissui_month_list[i+1]]*
                                    coeff_dict[plant][month][f"{group1_name}⇒{group2_name}"])
            
            #dope2⇒dope1のドープ切替があるかどうか
            inter_switch_time_list.append(self.variables.inter_switch_2to1_flag[plant,self.variables.jissui_month_list[i+1]]*
                                    coeff_dict[plant][month][f"{group2_name}⇒{group1_name}"])
        
        
        if case_name == "前月に保全後期" or case_name == "当月に保全前期":
            
            #i月に生産あるか
            inter_switch_time_list.append(self.variables.all_prod_flag[plant,self.variables.jissui_month_list[i]]*
                                            coeff_dict[plant][month]["前月_生産"])
            
            #i+1月に生産あるか
            inter_switch_time_list.append(self.variables.all_prod_flag[plant,self.variables.jissui_month_list[i+1]]*
                                            coeff_dict[plant][month]["当月_生産"])
            
        
        return inter_switch_time_list
    
    
    
    
    
    
    def inter_switch_time_constraint2(self):
        #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
        for plant in self.variables.plant_list:
            group1_name = self.variables.dope_group_dict[plant]["group1"]
            group2_name = self.variables.dope_group_dict[plant]["group2"]   #ドープグループが一個だけの場合はNone
            
            #初月はinter_switch_time_headは0にする。
            self.problem += self.variables.inter_switch_time_head[plant,
                            self.variables.jissui_month_list[0]] == 0 
            #最終月のinter_switch_tailは0にする
            self.problem += self.variables.inter_switch_time_tail[plant,
                            self.variables.jissui_month_list[len(self.variables.jissui_month_list)-1]] == 0 
                                
            
            for i in range(len(self.variables.jissui_month_list)-1):
                
                #i月に保全後期がある場合
                if ((self.variables.month_type_dict[plant][self.variables.jissui_month_list[i]]["保全後期"] == "あり") ):
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.variables.inter_switch_maint_tail_coeff_dict,
                                                                                    plant,group1_name,group2_name,"前月に保全後期",i)

                #i+1月に保全前期がある場合
                if ((self.variables.month_type_dict[plant][self.variables.jissui_month_list[i]]["保全前期"] == "あり") ):
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.variables.inter_switch_maint_head_coeff_dict,
                                                                                    plant,group1_name,group2_name,"当月に保全前期",i)
                
                else:
                    inter_switch_time_list = self.inter_switch_time_constraint2_common(self.variables.inter_switch_coeff_dict,
                                                                                    plant,group1_name,group2_name,"その他",i)
                    
                    
            
                #i月とi+1月の月間切替時間の合計＝＝ 近似的に得られる月間切替時間
                self.problem += self.variables.inter_switch_time_head[plant,self.variables.jissui_month_list[i+1]] + \
                    self.variables.inter_switch_time_tail[plant,self.variables.jissui_month_list[i]] == pulp.lpSum(inter_switch_time_list)
                
                
    
    
    
    
    
    
    
    # def fuka_equal_constraint(self):
    #     """
    #     # 制約条件 (各月各工場の負荷時間ぴったり）(絶対制約)
         
    #      このまま描いてtryexceptにするか、⇒やめた
         
    #      monthだけないなんてことはない。
    #      plantと品種の辞書が欲しい。
        
    #     """
        
    #     #ある工場ある月ある品種の生産時間(生産量達成率加味)なんでこれ100かけてるんだっけ？⇒逆数だから
        
        
    #     for plant in self.variables.plant_list:
    #         for month in self.variables.constraint_period_dict["負荷時間一致制約"]:
    #             month_hour_dict = {}
    #             for prod_name in self.variables.plant_prod_dict[plant]:
    #                 prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
    #                 month_hour_dict[prod_name] = prod_time
    #             #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant]) <= (self.variables.fuka_dict[plant][month]-self.variables.ave_switch_dict[plant][month])
    #             self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant]) == (self.variables.fuka_dict[plant][month]-self.variables.ave_switch_dict[plant][month])

    

    
    def fuka_less_constraint_5(self):
        """
        TODO 保全も生産品種もないときに、切り替え時間どうなっちゃう？（月中切替のぱらめーたに、全部0のケースも含めるべきかどうか。）変な値になったとしても行けるのか？
        
        """
        for plant in self.variables.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.variables.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant]) <= (self.variables.fuka_dict[plant][month]-self.variables.ave_switch_dict[plant][month])
                
                
                # fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                #                                                              self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                #                                                              self.variables.prod_capacity_dict[plant][month]["保全"]+
                #                                                              self.variables.prod_capacity_dict[plant][month]["計画停止"])
                
                
                
                fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.variables.maint_hour_dict[plant][month]+
                                                                             self.variables.prod_capacity_dict[plant][month]["計画停止"])
                
                
                
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant]) <= (fuka_time - 
                                                                                                                        self.variables.switch_time[plant,month] -
                                                                                                                        self.variables.inter_switch_time_head[plant,month] -
                                                                                                                        self.variables.inter_switch_time_tail[plant,month])
    
    
    
    
    
    
    def fuka_less_constraint_slack(self):
        for plant in self.variables.constraint_plant_dict["負荷時間以下制約"]:
            for month in self.variables.constraint_period_dict["負荷時間以下制約"]:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                #self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant]) <= (self.variables.fuka_dict[plant][month]-self.variables.ave_switch_dict[plant][month])
                
                
                fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.variables.maint_hour_dict[plant][month]+
                                                                             self.variables.prod_capacity_dict[plant][month]["計画停止"])
                
                #self.problem += self.variables.slack[plant,month] >= 0
                
                
                self.problem += pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])  <= (fuka_time - 
                                                                                                                        self.variables.switch_time[plant,month] -
                                                                                                                        self.variables.inter_switch_time_head[plant,month] -
                                                                                                                        self.variables.inter_switch_time_tail[plant,month]) + self.variables.slack[plant,month]
        
        #解空間を狭めるため
        self.problem += pulp.lpSum(self.variables.slack[plant,month] for plant in 
                                   self.variables.constraint_plant_dict["負荷時間以下制約"] for month in self.variables.constraint_period_dict["負荷時間以下制約"]) <= 10000
    
    
    
    
    def prod_span_constraint_min(self):
        """
        レア品種に関して、一度生産が入ってから次の生産まで必ずkか月以上空けるための制約
        
        さしあたりL3 8UAWのみ。
        
        """
        
        k = 6 - 2               #6か月に一回生産する。つまり生産しない月が5か月続く。
        plant = "L3"
        
        
        for i in range(len(self.variables.jissui_month_list)):
            for j in range(i+1, min(i+k+1, len(self.variables.jissui_month_list))):  # i と j の距離が K 以内なら制約を追加
                month_i = self.variables.jissui_month_list[i]
                month_j = self.variables.jissui_month_list[j]
                self.problem +=  self.variables.delta[plant,month_i,"8UAW"] + self.variables.delta[plant,month_j,"8UAW"] <= 1
        
        
    def prod_span_constraint_max(self):
        """
        
        レア品種に関して、一度生産が入ってから次の生産まで必ずkか月以下空けるための制約
        
        """
        
        k=7
        plant = "L3"
        
        
        # for i in range(len(self.variables.jissui_month_list)):
        #     month_i = self.variables.jissui_month_list[i]
        #     self.problem += pulp.lpSum(self.variables.delta[plant,self.variables.jissui_month_list[j],"8UAW"] for j in 
        #                                range(i+1, min(i+k+2, len(self.variables.jissui_month_list)))) >= self.variables.delta[plant,month_i,"8UAW"]
            

        for i in range(len(self.variables.jissui_month_list)):
            if i + k + 1 < len(self.variables.jissui_month_list):  # n を超えない場合にのみ適用
                month_i = self.variables.jissui_month_list[i]
                self.problem += pulp.lpSum(self.variables.delta[plant,self.variables.jissui_month_list[j],"8UAW"]
                                           for j in range(i+1, i+k+2)) >= self.variables.delta[plant,month_i,"8UAW"]
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def sum_sales_constraint(self):
        """
        # 各品種の販売量の各月合計が合計販売量に一致（絶対制約）
        
        """

        for prod_name in self.variables.all_prod_list:
            for month in self.variables.constraint_period_dict["合計販売量一致制約"]:
                plant_dict = {}
                for plant in self.variables.prod_plant_dict[prod_name]:
                    plant_dict[plant] = self.variables.y[plant,month,prod_name]
                
                
                self.problem += pulp.lpSum(plant_dict[plant] for plant in self.variables.prod_plant_dict[prod_name]) == self.variables.sales_dict[month][prod_name]
                
                #self.problem += pulp.lpSum(plant_dict[plant] for plant in self.variables.prod_plant_dict[prod_name]) >= self.variables.sales_dict[month][prod_name] -100
                #self.problem += pulp.lpSum(plant_dict[plant] for plant in self.variables.prod_plant_dict[prod_name]) <= self.variables.sales_dict[month][prod_name] +100
                
                
                
                
        
        
    def not_minus_stock_constraint(self):
        """
        各月各品種月末在庫が0以上 (絶対制約)
        もしかしたらjissui_month_listでやらないほうがいいかも。
        (確定済み生産計画の方で確定した在庫がマイナスになっている可能性があるため)
        
        """
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["月末在庫0以上制約"]:
            for month in self.variables.constraint_period_dict["月末在庫0以上制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    index = self.variables.jissui_month_list.index(month)      #その月のindex
                    self.problem += self.variables.init_stock_dict[prod_name][plant] + \
                    pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - \
                    pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) >= 0
                
    
    
    def within_basic_stock_constraint_min(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        もしかしたらあとで0.1下駄吐かせた方が良いかもしれない
        
        あとは平均販売量のところだけ！
        
        推定期間で合計販売量がずっと0の品種は除外しないとヤバイ。
        
        特に、基準在庫Min以上を満たすのが難しい。0以上なら多分イイんだけども。。。分けるか。
        
        
        
        """
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["基準在庫月数Min以上制約"]:
            for month in self.variables.constraint_period_dict["基準在庫月数Min以上制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    index = self.variables.jissui_month_list.index(month)
                    
                    #月末在庫
                    stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                    
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
                    self.problem += stock >= ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month])
                    #self.problem += stock >= ave_sales*(self.variables.basic_stock_dict[prod_name][plant]["min"]/30)
                    #self.problem += stock <= ave_sales*(self.variables.basic_stock_dict[prod_name][plant]["max"]/30)
                    
    
    def within_basic_stock_constraint_min2(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        もしかしたらあとで0.1下駄吐かせた方が良いかもしれない
        
        あとは平均販売量のところだけ！
        
        推定期間で合計販売量がずっと0の品種は除外しないとヤバイ。
        
        特に、基準在庫Min以上を満たすのが難しい。0以上なら多分イイんだけども。。。分けるか。
        
        
        
        """
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["基準在庫月数Min以上制約"]:
            for month in self.variables.constraint_period_dict["基準在庫月数Min以上制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    index = self.variables.jissui_month_list.index(month)    
                        
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
                    #在庫量 >= 平均販売量*基準在庫月数Min
                    self.problem += self.variables.z >= ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month])
    
        
    
    
    def within_basic_stock_constraint_max(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        単一工場品種で、年間の販売量(推定期間の販売量) < 期首在庫 な品種は除く
        
        TODO ↑除かない方がいいかも？生産キャパに余裕がある場合に、この品種が生産されまくってしまいそう。
        除くのではなく、在庫月数の計算を先に行って、その結果で基準在庫Maxの値を書き換えるのがいいかも。
        
        """
        exclusion_list = self.variables.too_much_init_stock_prod()   #除去品種リスト
        
        
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["基準在庫月数Max以下制約"]:
            for month in self.variables.constraint_period_dict["基準在庫月数Max以下制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    
                    if prod_name not in exclusion_list:
                    
                        index = self.variables.jissui_month_list.index(month)
                        
                        #月末在庫
                        stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                        
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                        
                        
                        self.problem += stock <= ave_sales*(self.variables.basic_stock_max_dict[prod_name][plant][month])      #例えば期首在庫が異常に多すぎると違反する。
                        
                        #self.problem += stock >= ave_sales*(self.variables.basic_stock_dict[prod_name][plant]["min"]/30)
                        #self.problem += stock <= ave_sales*(self.variables.basic_stock_dict[prod_name][plant]["max"]/30)      #例えば期首在庫が異常に多すぎると違反する。
    
    
    
    
    def within_basic_stock_constraint_max2(self):
        """
        先々○ヶ月で販売量は平均取る。(3かげつとか)
        
        単一工場品種で、年間の販売量(推定期間の販売量) < 期首在庫 な品種は除く
        
        TODO ↑除かない方がいいかも？生産キャパに余裕がある場合に、この品種が生産されまくってしまいそう。
        除くのではなく、在庫月数の計算を先に行って、その結果で基準在庫Maxの値を書き換えるのがいいかも。
        
        """
        exclusion_list = self.variables.too_much_init_stock_prod()   #除去品種リスト
        
        
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["基準在庫月数Max以下制約"]:
            for month in self.variables.constraint_period_dict["基準在庫月数Max以下制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    if prod_name not in exclusion_list:
                        
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                        
                        
                        self.problem += self.variables.z <= ave_sales*(self.variables.basic_stock_max_dict[prod_name][plant][month])      #例えば期首在庫が異常に多すぎると違反する。
    
    
    def min_continuous_constraint(self):
        """
        最低連続生産時間制約
        
        
        """
        # 最低連続生産時間
        #これは確定済み生産計画のところは除いた方がイイので、month_listが0抜いている。
        #確定済み生産計画の扱いをどうするか。     
            
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["最低連続生産時間以上制約"]:
            for month in self.variables.constraint_period_dict["最低連続生産時間以上制約"]:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    self.problem += self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month] \
                        >= self.variables.delta[plant,month,prod_name]*self.variables.min_continuous_dict[prod_name][plant][month]

    
    def num_production_constraint_min(self):
        """
        生産回数制約
        
        """
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["最低生産回数以上制約"]:
            for prod_name in self.variables.plant_prod_dict[plant]:
                #self.problem +=  pulp.lpSum(self.variables.delta[plant,month,prod_name] for month in self.variables.jissui_month_list) <= self.variables.prod_num_times_dict[prod_name][plant]["max"]
                self.problem +=  pulp.lpSum(self.variables.delta[plant,month,prod_name] for month in self.variables.jissui_month_list) >= self.variables.prod_num_times_dict[prod_name][plant]["min"]

    
    def num_production_constraint_max(self):
        """
        生産回数制約
        
        """
        #for plant in self.variables.plant_list:
        for plant in self.variables.constraint_plant_dict["最大生産回数以下制約"]:
            for prod_name in self.variables.plant_prod_dict[plant]:
                self.problem +=  pulp.lpSum(self.variables.delta[plant,month,prod_name] for month in self.variables.jissui_month_list) <= self.variables.prod_num_times_dict[prod_name][plant]["max"]
                #self.problem +=  pulp.lpSum(self.variables.delta[plant,month,prod_name] for month in self.variables.jissui_month_list) >= self.variables.prod_num_times_dict[prod_name][plant]["min"]

    
    def spare_time_constraint(self ,min_value, max_value):
        """
        余力時間一致制約
        
        """
        
        yoryoku_time_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                
                fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.variables.maint_hour_dict[plant][month]+
                                                                             self.variables.prod_capacity_dict[plant][month]["計画停止"])
                
                all_prod_time = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])
                
                yoryoku_time = (fuka_time - self.variables.switch_time[plant,month] - 
                                self.variables.inter_switch_time_head[plant,month] - 
                                self.variables.inter_switch_time_tail[plant,month] - all_prod_time) + self.variables.slack[plant,month]
                
                
                self.problem += yoryoku_time >= 0
                
                yoryoku_time_list.append(yoryoku_time)
        
        self.problem += pulp.lpSum(yoryoku_time_list) <= max_value
        self.problem += pulp.lpSum(yoryoku_time_list) >= min_value
        
    
    def spare_time_constraint2(self ,min_value, max_value):
        """
        余力時間一致制約
        
        """
        
        yoryoku_time_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                
                fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.variables.maint_hour_dict[plant][month]+
                                                                             self.variables.prod_capacity_dict[plant][month]["計画停止"])
                
                all_prod_time = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])
                
                yoryoku_time = (fuka_time - self.variables.switch_time[plant,month] - 
                                self.variables.inter_switch_time_head[plant,month] - 
                                self.variables.inter_switch_time_tail[plant,month] - all_prod_time)
                
                
                
                yoryoku_time_list.append(yoryoku_time)
        
        self.problem += pulp.lpSum(yoryoku_time_list) <= max_value
        self.problem += pulp.lpSum(yoryoku_time_list) >= min_value
    
    
    
    
    
    
    
    
    
    def finalized_sales_constraint(self):
        """
        確定販売量
        
        {'3XR-1': {'L4': {'12月': 90.0}},
        '2UAW': {'L2': {'8月': 80.0}, 'L3': {'4月': 20.0, '7月': 20.0, '1月': 20.0}},
        '4UASW': {'L3': {'9月': 40.0}}}
 
        self.variables.x[plant,month,prod_name]
        
        
        確定生産量のところと同様の懸念のため、イコールではなく
        
        """
        
        if self.variables.finalized_sales_dict is not None:
            for prod_name in self.variables.finalized_sales_dict.keys():
                for plant in self.variables.finalized_sales_dict[prod_name].keys():
                    for month in self.variables.finalized_sales_dict[prod_name][plant].keys():
                        if month in self.variables.jissui_month_list:
                            
                            if self.variables.finalized_sales_dict[prod_name][plant][month] > 0:
                                self.problem += self.variables.y[plant,month,prod_name] >= self.variables.finalized_sales_dict[prod_name][plant][month] -1
                                self.problem += self.variables.y[plant,month,prod_name] <= self.variables.finalized_sales_dict[prod_name][plant][month] +1
                            
                            if self.variables.finalized_sales_dict[prod_name][plant][month] == 0:
                                self.problem += self.variables.y[plant,month,prod_name] == self.variables.finalized_sales_dict[prod_name][plant][month]
        
    
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
        
        if self.variables.finalized_prod_dict is not None:
            for prod_name in self.variables.finalized_prod_dict.keys():
                for plant in self.variables.finalized_prod_dict[prod_name].keys():
                    for month in self.variables.finalized_prod_dict[prod_name][plant].keys():
                        if month in self.variables.jissui_month_list:
                            #self.problem += self.variables.x[plant,month,prod_name] == self.variables.finalized_prod_dict[prod_name][plant][month]
                            
                            if self.variables.finalized_prod_dict[prod_name][plant][month] > 0:
                                self.problem += self.variables.x[plant,month,prod_name] >= self.variables.finalized_prod_dict[prod_name][plant][month] -1
                                self.problem += self.variables.x[plant,month,prod_name] <= self.variables.finalized_prod_dict[prod_name][plant][month] +1
                            
                            if self.variables.finalized_prod_dict[prod_name][plant][month] ==  0:
                                self.problem += self.variables.x[plant,month,prod_name] == self.variables.finalized_prod_dict[prod_name][plant][month]
    
    def w_sw_constraint(self,min_value,max_value):
        """
        該当工場のsva品種の生産量が、最低値以上、最大値以下になるようにする。
        
        """

        all_list = []
        for prod_tuple in self.variables.priority_sva_prod_list:
            sum_prod_amount = pulp.lpSum([self.variables.x[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_amount)
        
        self.problem +=  pulp.lpSum(all_list) <= max_value
        self.problem +=  pulp.lpSum(all_list) >= min_value
    
    
    
    
    def sub_prod_constraint(self,min_value,max_value):
        """
        
        サブ品種の生産量が、最低値以上、最大値以下になるようにする。
        目的関数の値はマイナス付きなので、引数には絶対値をとった値を入れる。
        
        """
    
        all_list = []
        for prod_tuple in self.variables.sub_prod_list:
            sum_prod_amount = pulp.lpSum([self.variables.x[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_amount)
            
        self.problem += pulp.lpSum(all_list) <= max_value
        self.problem += pulp.lpSum(all_list) >= min_value
    
    
    
    def prod_time_constraint(self,min_value,max_value):
        """
        合計生産時間一致制約
        全工場全月の合計生産時間が、最低値以上、最大値以下になるようにする。
        """
        jissui_month_hour_dict = {}
        for plant in self.variables.plant_list:
            total_month_hour_dict = {}
            for month in self.variables.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.variables.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.variables.plant_list) >= min_value
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.variables.plant_list) <= max_value
    
    def over_stock_constraint(self,min_value,max_value):
        """
        
        基準在庫月数Max以下制約違反回数一致制約
        
        
        """
        month_num = (pulp.lpSum(self.variables.delta_z[multi] for multi in self.variables.multi_plant_prod_index))
    
    
        self.problem += month_num <= abs(max_value)
        
        self.problem += month_num >= abs(min_value)
        
        
        
    def over_stock_7_constraint(self,min_value,max_value):
        """
        
        7桁基準在庫月数Max以下制約違反回数一致制約
        
        
        """
        
        month_num = pulp.lpSum(self.variables.delta_7_z[prod_name,month]
                        for month in self.variables.jissui_month_list for prod_name in self.variables.all_prod_list)

    
        self.problem += month_num <= abs(max_value)
        
        self.problem += month_num >= abs(min_value)
    
    
    
        
    
    def shortage_stock_constraint(self,min_value,max_value):
        """
        基準在庫月数Min以上制約違反回数一致制約
        """
    
        month_num = (pulp.lpSum(self.variables.delta_mz[multi] for multi in self.variables.multi_plant_prod_index))
    
    
        self.problem += month_num <= abs(max_value)
        
        self.problem += month_num >= abs(min_value)
        
        
    def shortage_stock_7_constraint(self,min_value,max_value):
        """
        7桁基準在庫月数Min以上制約違反回数一致制約
        """

        
        month_num = pulp.lpSum(self.variables.delta_7_mz[prod_name,month] 
                        for month in self.variables.jissui_month_list for prod_name in self.variables.all_prod_list) 
        
        
        self.problem += month_num <= abs(max_value)
        
        self.problem += month_num >= abs(min_value)
        
        
    def end_shortage_stock_7_constraint(self,min_value,max_value):
        month_num = pulp.lpSum(self.variables.delta_7_mz[prod_name,"3月"] for prod_name in self.variables.all_prod_list) 
        
        
        self.problem += month_num <= abs(max_value)
        
        self.problem += month_num >= abs(min_value)
        
        
        
        
        
        
        
        
        
    
    
    def stock_range_constraint(self,min_value,max_value):
        
        over = (pulp.lpSum(self.variables.delta_z[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]))
        
        shortage = (pulp.lpSum(self.variables.delta_mz[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]))
        
        
        self.problem += over + shortage <= abs(max_value)
        self.problem += over + shortage >= abs(min_value)



    def stock_num_7_constraint(self,min_value,max_value):
        month_num_list = []
        for prod_name in self.variables.all_prod_list:
            total_stock = [self.variables.z[plant,"3月",prod_name] for plant in self.variables.prod_plant_dict[prod_name]]
            total_stock = pulp.lpSum(total_stock)
            
            if self.variables.sales_dict["3月"][prod_name] > 0: 
        
                month_num = total_stock*(1/self.variables.sales_dict["3月"][prod_name])
                month_num_list.append(month_num)
        
        self.problem += pulp.lpSum(month_num_list) >= min_value
        self.problem += pulp.lpSum(month_num_list) <= max_value
        

    
    def over_stock_amount_constraint(self,min_value,max_value):
        """
        超過月末在庫量一致制約。
        マイナスの値も全然とるので注意
        
        """
        over_stock_amount_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                        #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                        ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                        
                        over_stock = self.variables.z[plant,month,prod_name] - ave_sales*(self.variables.basic_stock_max_dict[prod_name][plant][month])
                        
                        # month_num = over_stock/(ave_sales+0.01)
                        # month_num_list.append(month_num)
                        
                        over_stock_amount_list.append(over_stock)
        
       
        self.problem += pulp.lpSum(over_stock_amount_list) >= min_value
        self.problem += pulp.lpSum(over_stock_amount_list) <= max_value
        
        
    
 
    
    def prod_num_constraint(self,min_value,max_value):
        """
        合計生産回数を、レア品種（）生産回数に直す。
        
        """
    
        # self.problem += pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
        #                 for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]) >= abs(self.variables.additional_constraint_dict["レア品種（L1 4USQW、L2 4UYW、L3 8UAW）の合計生産回数一致制約"]) -10
    
        # self.problem += pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
        #                 for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]) <= abs(self.variables.additional_constraint_dict["レア品種（L1 4USQW、L2 4UYW、L3 8UAW）の合計生産回数一致制約"]) +10
        
        # self.problem += (pulp.lpSum([self.variables.delta["L1",month,"4USQW"] for month in self.variables.jissui_month_list]) + \
        #                pulp.lpSum([self.variables.delta["L2",month,"4UYW"] for month in self.variables.jissui_month_list]) + \
        #                pulp.lpSum([self.variables.delta["L3",month,"8UAW"] for month in self.variables.jissui_month_list])) == abs(self.variables.additional_constraint_dict["レア品種の合計生産回数一致制約"])
        
        
        all_list = []
        for prod_tuple in self.variables.rare_prod_list:
            sum_prod_num = pulp.lpSum([self.variables.delta[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_num)
        
        self.problem += pulp.lpSum(all_list)  <= abs(max_value)
        self.problem += pulp.lpSum(all_list)  >= abs(min_value)
        
    
    
    def over_fuka_constraint(self,min_value,max_value):
        """
        負荷時間以下制約違反量一致制約
        
        """
        jissui_month_hour_dict = {}
        for plant in self.variables.plant_list:
            total_month_hour_dict = {}
            for month in self.variables.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
            
            jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.variables.jissui_month_list)     #ある工場の各月負荷時間合計(月で和をとる)
        
        exclusion_plant_list = list(set(self.variables.plant_list) - set(self.variables.constraint_plant_dict["負荷時間以下制約"]))

        #生産可能時間
        #total = pulp.lpSum(self.variables.fuka_dict[plant][month] for plant in exclusion_plant_list for month in self.variables.jissui_month_list) - pulp.lpSum(self.variables.ave_switch_dict[plant][month] for plant in exclusion_plant_list for month in self.variables.jissui_month_list)
        #st.write(sum([self.variables.fuka_dict[plant][month] for plant in self.variables.plant_list for month in self.variables.jissui_month_list])-sum([self.variables.ave_switch_dict[plant][month] for plant in self.variables.plant_list for month in self.variables.jissui_month_list]))
        
        self.problem += (pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list)) >= abs(min_value)
        self.problem += (pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list)) <= abs(max_value)
    
    
    def almost_touch_min_stock_constraint(self,min_value,max_value):
        #TODO 確定生産量とか確定販売量との兼ね合いでこの基準在庫Minの制約守られない危険性あり。（解無し）このように新たに制約を増やすのはよくないかも。目的関数経由がいいか。
        exclusion_plant_list = list(set(self.variables.plant_list) - set(self.variables.constraint_plant_dict["負荷時間以下制約"]))

        diff_list = []
        for plant in exclusion_plant_list:
            for month in self.variables.jissui_month_list:
                for prod_name in self.variables.plant_prod_dict[plant]:
                    index = self.variables.jissui_month_list.index(month)
                    
                    #月末在庫
                    stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                    
                    #翌月以降〇ヶ月の平均販売量（ひと月当たり）
                    ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
                    diff = stock - ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month])    #Min在庫からどれだけ離れているか。
                    diff_list.append(diff)
                    
        
        
        self.problem += (pulp.lpSum(diff_list)) >= abs(min_value)
        self.problem += (pulp.lpSum(diff_list)) <= abs(max_value)
    
    
    def maintenance_dope_num_constraint(self,min_value,max_value):
        """
        #TODO 2ドープ以上に対応する
        
        """
        dope_num_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.maint_month_list[plant]:
                dope_num_list.append(pulp.lpSum([self.variables.group1_flag[plant,month],self.variables.group2_flag[plant,month]]))
        
        self.problem += pulp.lpSum(dope_num_list) >= abs(min_value)
        self.problem += pulp.lpSum(dope_num_list) <= abs(max_value)
    
    
    
    def main_dope_num_constraint(self,min_value,max_value):
        num_list = []
        for plant in self.variables.plant_list:
            for key in self.variables.dopenum_dope_dict[plant].keys():
                if self.variables.dopenum_dope_dict[plant][key] == self.variables.main_dope_prod_dict[plant]["メインドープ"]:
                    if key == "dope1":
                        dope_flag = self.variables.dope1_flag
                    if key == "dope2":
                        dope_flag = self.variables.dope2_flag
                    if key == "dope3":
                        dope_flag = self.variables.dope3_flag
            
            

            num_list.append(pulp.lpSum(dope_flag[plant,month] for month in self.variables.maint_month_list[plant]))
        
        self.problem += pulp.lpSum(num_list) >= abs(min_value) 
        self.problem += pulp.lpSum(num_list) <= abs(max_value) 
    
    
    
    def main_prod_amount_constraint(self,min_value,max_value):
        amount_list = []
        for plant in self.variables.plant_list:
            main_prod = self.variables.main_dope_prod_dict[plant]["メイン品種"]
            amount = pulp.lpSum(self.variables.x[plant,month,main_prod] for month in self.variables.jissui_month_list)
            amount_list.append(amount)
        total_amount = pulp.lpSum(amount_list)
        
        self.problem += total_amount >= abs(min_value)
        self.problem += total_amount <= abs(max_value)
    
    
    
    
    # def long_dope_switch_constraint(self,min_value,max_value):
    #     """
    #     長時間ドープ切り替え回数最小化
        
    #     """
    #     self.problem += (pulp.lpSum(self.variables.dope_switch_flag[month] for month in self.variables.jissui_month_list)) >= min_value
    #     self.problem += (pulp.lpSum(self.variables.dope_switch_flag[month] for month in self.variables.jissui_month_list)) <= max_value

    
    
    # def sazma_continuous_constraint(self,min_value,max_value):
    #     """
    #     sazma系はなるべく連続生産する
        
    #     """
    #     #self.problem += (pulp.lpSum(self.variables.sazma_continuous_flag[month] for month in self.variables.jissui_month_list)) == abs(self.variables.additional_constraint_dict["SAZMA系品種連続生産月数一致制約"])
        
    #     self.problem += (pulp.lpSum(self.variables.sazma_to_sva_flag[month] for month in self.variables.jissui_month_list)+\
    #                     pulp.lpSum(self.variables.sva_to_sazma_flag[month] for month in self.variables.jissui_month_list)) >= min_value
        
        
    #     self.problem += (pulp.lpSum(self.variables.sazma_to_sva_flag[month] for month in self.variables.jissui_month_list)+\
    #                     pulp.lpSum(self.variables.sva_to_sazma_flag[month] for month in self.variables.jissui_month_list)) <= max_value
    
    
    def total_switch_time_constraint(self,min_value,max_value):
        """
        合計切替時間最小化
        
        """
        temp_list = []
        for plant in self.variables.plant_list:
            total_inner_switch = pulp.lpSum(self.variables.switch_time[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_head = pulp.lpSum(self.variables.inter_switch_time_head[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_tail = pulp.lpSum(self.variables.inter_switch_time_tail[plant,month] for month in self.variables.jissui_month_list)
            
            total_switch = total_inner_switch + total_inter_switch_time_head + total_inter_switch_time_tail
            temp_list.append(total_switch)
        
        self.problem += pulp.lpSum(temp_list) <= max_value
        self.problem += pulp.lpSum(temp_list) >= min_value
    
    
    def long_dope_total_switch_time_constraint(self,min_value,max_value):
        """
        合計切替時間最小化
        
        """
        temp_list = []
        long_dope_plant_list = ["L3","L6","L7"]
        for plant in long_dope_plant_list:
            total_inner_switch = pulp.lpSum(self.variables.switch_time[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_head = pulp.lpSum(self.variables.inter_switch_time_head[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_tail = pulp.lpSum(self.variables.inter_switch_time_tail[plant,month] for month in self.variables.jissui_month_list)
            
            total_switch = total_inner_switch + total_inter_switch_time_head + total_inter_switch_time_tail
            temp_list.append(total_switch)
        
        self.problem += pulp.lpSum(temp_list) <= max_value
        self.problem += pulp.lpSum(temp_list) >= min_value
        self.problem += pulp.lpSum(temp_list) >=0                #いるか？これ
    
    
    
    
    
    # def long_dope_switch_variable_constraint(self):
    #     """
    #     長時間のドープ切り替えを検知するための変数をただしく動かすための制約
    #     とりあえずL6のみ
        
    #     """
        
    #     #TAC群にひとつでも1があったら1、すべてが0のときに0を返すバイナリ変数
    #     for month in self.variables.jissui_month_list:
    #         for prod_name in self.variables.plant_prod_dict["L6"]:
    #             if "SAZMA" not in prod_name:
    #                 self.problem += self.variables.tac_prod_flag[month] >= self.variables.delta["L6",month,prod_name]
            
    #         self.problem += self.variables.tac_prod_flag[month] <= pulp.lpSum(self.variables.delta["L6",month,prod_name] for prod_name in self.variables.plant_prod_dict["L6"] 
    #                                                 if "SAZMA" not in prod_name)
        
        
        
    #     #sazma群にひとつでも1があったら1、すべてが0のときに0を返すバイナリ変数
    #     for month in self.variables.jissui_month_list:
    #         for prod_name in self.variables.plant_prod_dict["L6"]:
    #             if "SAZMA" in prod_name:
    #                 self.problem += self.variables.sazma_prod_flag[month] >= self.variables.delta["L6",month,prod_name]
            
    #         self.problem += self.variables.sazma_prod_flag[month] <= pulp.lpSum(self.variables.delta["L6",month,prod_name] for prod_name in self.variables.plant_prod_dict["L6"]
    #                                                 if "SAZMA" in prod_name)
        
        
    #     for month in self.variables.jissui_month_list:
    #         self.problem += self.variables.dope_switch_flag[month] <= self.variables.tac_prod_flag[month]
    #         self.problem += self.variables.dope_switch_flag[month] <= self.variables.sazma_prod_flag[month]
    #         self.problem += self.variables.dope_switch_flag[month] >= self.variables.tac_prod_flag[month] + self.variables.sazma_prod_flag[month] - 1
    
    # def sazma_continuous_variable_constraint(self):
    #     """
    #     sazma系品種の連続生産フラグを設定するための制約
        
    #     """
    #     for i in range(len(self.variables.jissui_month_list)-1):
    #         self.problem += self.variables.sazma_continuous_flag[self.variables.jissui_month_list[i]] <= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]]
    #         self.problem += self.variables.sazma_continuous_flag[self.variables.jissui_month_list[i]] <= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]]
    #         self.problem += self.variables.sazma_continuous_flag[self.variables.jissui_month_list[i]] >= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]] + self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]] -1
        
        
    # def sazma_to_sva_constraint(self):
    #     """
    #     sazma_prod_flag が 1⇒0 のとき1、それ以外のとき0 
        
    #     """
    #     for i in range(len(self.variables.jissui_month_list)-1):
    #         self.problem += self.variables.sazma_to_sva_flag[self.variables.jissui_month_list[i]] <= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]]
    #         self.problem += self.variables.sazma_to_sva_flag[self.variables.jissui_month_list[i]] <= 1 - self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]]
    #         self.problem += self.variables.sazma_to_sva_flag[self.variables.jissui_month_list[i]] >= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]] - self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]]
        
    #     self.problem += self.variables.sazma_to_sva_flag[self.variables.jissui_month_list[-1]] ==0
        
        
        
    # def sva_to_sazma_constraint(self):
    #     """
    #     sazma_prod_flag が 0⇒1 のとき1、それ以外のとき0 
        
    #     """
    #     for i in range(len(self.variables.jissui_month_list)-1):
    #         self.problem += self.variables.sva_to_sazma_flag[self.variables.jissui_month_list[i]] <= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]]
    #         self.problem += self.variables.sva_to_sazma_flag[self.variables.jissui_month_list[i]] <= 1 - self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]]
    #         self.problem += self.variables.sva_to_sazma_flag[self.variables.jissui_month_list[i]] >= self.variables.sazma_prod_flag[self.variables.jissui_month_list[i+1]] - self.variables.sazma_prod_flag[self.variables.jissui_month_list[i]]
        
    #     self.problem += self.variables.sva_to_sazma_flag[self.variables.jissui_month_list[-1]] ==0
    
    
    

    def max_switch_constraint(self):
        """
        切替時間の最大値最小化
        
        """
        pass
    
    
    def total_prod_num_constraint(self,min_value,max_value):
        """
        合計生産回数最小化
        """
        
        #self.problem += -pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
        #                        for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant])
    
    
        self.problem += pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]) <= max_value
        
        self.problem += pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]) >= min_value
    
    
     
    def prod_month_constraint(self,min_value,max_value):
        
        total = pulp.lpSum(self.variables.all_prod_flag[plant,month]for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list)
        
        self.problem += total >= min_value
        self.problem += total <= max_value
        
             
     
     
     
    def bundled_maint_options_constraint(self):
        """
        切替時間と保全を抱き合わせるための制約
        

        
        工場、保全名、時間、タイミング
        
        {
            "L6":{
            "保全①":{
            "8月":272
            "9月":208
            }
            "保全②":{
            "10月":384
            }
            }
}
        
        
        """
        for plant in self.variables.bundle_maint_dict.keys():
            for maint_name in self.variables.bundle_maint_dict[plant].keys():
                if len(self.variables.bundle_maint_dict[plant][maint_name]) == 2:
                    #月間切替に制約
                    
                    temp_month_list = list(self.variables.bundle_maint_dict[plant][maint_name].keys())
                    
                    month_1 = temp_month_list[0]
                    month_2 = temp_month_list[1]
                    
                    total_maint_hour =  sum([self.variables.bundle_maint_dict[plant][maint_name][month_1],
                                                self.variables.bundle_maint_dict[plant][maint_name][month_2]])*0.8 #近似値なので一応0.9掛けしとく
                    
                    total_inter_switch_time = self.variables.inter_switch_time_head[plant,month_2] + self.variables.inter_switch_time_tail[plant,month_1]
                    
                    
                    self.problem += total_inter_switch_time >= total_maint_hour     #ほんとにこれだけでいいんか？良い気がする。
                    
                    #分解をイイ感じにするため(まあ必ず比を同じにする必要はないけどね。。。)
                    #self.problem += self.variables.inter_switch_time_tail[plant,month_1] >= total_inter_switch_time*(self.variables.bundle_maint_dict[plant][maint_name][month_1]/total_maint_hour)
                    #self.problem += self.variables.inter_switch_time_head[plant,month_2] >= total_inter_switch_time*(self.variables.bundle_maint_dict[plant][maint_name][month_2]/total_maint_hour)
                    
                    self.problem += self.variables.inter_switch_time_tail[plant,month_1] >= self.variables.bundle_maint_dict[plant][maint_name][month_1]*0.8
                    self.problem += self.variables.inter_switch_time_head[plant,month_2] >= self.variables.bundle_maint_dict[plant][maint_name][month_2]*0.8
                    
                    
                    
                
                if len(self.variables.bundle_maint_dict[plant][maint_name]) == 1:
                    
                    #月中切替に制約
                    month = list(self.variables.bundle_maint_dict[plant][maint_name].keys())[0]
                    
                    #月中切替時間が保全時間の0.9倍以上であること
                    self.problem += self.variables.switch_time[plant,month] >= (self.variables.bundle_maint_dict[plant][maint_name][month])*0.7 #近似値なので一応0.9掛けしとく
                    #self.problem += pulp.lpSum([self.variables.dope1_flag[plant,month],self.variables.dope2_flag[plant,month]]) >= 2
                    
                    #ドープグループは複数（2種）
                    self.problem += pulp.lpSum([self.variables.group1_flag[plant,month],self.variables.group2_flag[plant,month]]) == 2
                    
                    
                    
     
     
    def not_bundled_maint_constraint(self):
        """
        長時間の切替の工場について、
        保全前後でdopeを同じにするための制約。
        短い保全を皮切りにdope変更させないようにするため
        
        dopeフラグで行く。とおもったが、group_flagで行く方がよさそう
        
        
        
        
        
        
        L3L6L7
        
        """
        
        plant_list = list(self.variables.not_bundle_maint_dict.keys())      #抱き合わせしない保全を持つ工場リスト
        
        for plant in plant_list:
            for maint in self.variables.not_bundle_maint_dict[plant].keys():
                
                #ひと月にしかない保全の場合は、懸念していることは起きない仕様なので、スルー
                #TODO 24/12/18 時点の基本予算ではL3L6L7においてふたつきにまたがるような保全はないので
                #問題にはならない。
                
                
                if len(self.variables.not_bundle_maint_dict[plant][maint]) > 1:
                    
                    month_list = list(self.variables.not_bundle_maint_dict[plant][maint].keys())
                    
                    #トータル保全時間
                    total_maint_hour = sum([self.variables.not_bundle_maint_dict[plant][maint][month] for month in month_list])
                    
                    #トータルの保全時間がドープ切替時間未満の場合、ドープを同じにする（正確に言うと立下立上も含んで、未満の場合）
                    
                    
                    
                    
                    
                    month_list = list(self.variables.not_bundle_maint_dict[plant][maint].keys())
                    
                    month_1 = month_list[0]       #保全前期の月
                    month_2 = month_list[1]       #保全後期の月
                    
                    
                    #TODO メインドープ ∈ group1 でないとだめ。
                    #保全前期後期どちらかが非生産イベント（テストとか）で埋め尽くされる場合だめ。
                    #TODO 24/12/18 時点の基本予算ではL3L6L7においてふたつきにまたがるような保全はないので問題にはならない。
                    #TODO 保全からの立上立下が実際のところ何月なのかは他の目的関数においても必要な情報なのでいずれ何とかしたい。
                    
                    
                    self.problem += self.variables.group1_flag[plant,month_1] == self.variables.group1_flag[plant,month_2]
                    
                    
         
     
    def slack_sum_constraint(self,min_value,max_value):
        """
        スラック変数の合計一致制約 
        
        """
         
        slack_sum = pulp.lpSum(self.variables.slack[plant,month] for plant in self.variables.plant_list
                            for month in self.variables.jissui_month_list)
         
         
        self.problem += slack_sum >= min_value
        self.problem += slack_sum <= max_value
    
    
    def slack_zero_constraint(self):
        
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                self.problem += self.variables.slack[plant,month] == 0
    
     
     
    
     
     
    def define_constraints(self,constraint_list,additional_constraint_dict):
        """
        制約の定義
        
        """
        #制約条件
        self.z_variable_constraint()                   #zを月末在庫にするための制約
        self.delta_subdelta_constraint()               #生産フラグ用
        self.delta_subdelta_constraint_z()             #基準在庫Max超過検出用
        self.delta_subdelta_constraint_mz()            #基準在庫Min不足検出用
        
        self.delta_subdelta_constraint_7_z()
        self.delta_subdelta_constraint_7_mz()        
        
        
        
        
        #抱き合わせたい保全のタイミングで長めの切替を入れるための制約
        self.bundled_maint_options_constraint()
        
        #レア品種の生産に関して何か月か空けるようにする
        self.prod_span_constraint_min()    #最低k以上あけろ
        self.prod_span_constraint_max()    #最大k以下あけろ
        
        

        #TODO 短め保全時に立下と立上のドープを同じにする制約（長時間の工場のみ）
        #優先度は下げる
        #self.not_bundled_maint_constraint()
        
        # if hasattr(self.variables,"slack"):
        #    self.shortage_of_capacity_all_constraint()    #全ての目的関数を制約条件化
        
        
        
        #月中切替時間のための制約条件
        self.switch_time_constraint()      #変数switch_timeが線形回帰式で表現されるようにするための制約
        self.dope_flag_constraint()        #dopeフラグがただしく機能するための制約
        self.all_prod_flag_constraint()    #all_prod_flagがただしく機能するための制約
        
        
        #月間切替のための制約条件
        self.dope_group_flag_constraint()       #group_flagがただしく機能するための制約
        self.inter_switch_flag_constraint3()    #月間でグループの変換があるか。
        self.inter_switch_time_constraint2()    #変数inter_switch_timeが線形回帰式で表現されるようにするための制約
        
        
        for constraint_name in constraint_list:
            self.all_constraint_functions[constraint_name]()
            print(constraint_name)
        
        #追加の制約条件(昔目的関数だったもの)    
        for additional_constraint_name, value_dict in additional_constraint_dict.items():
            print(additional_constraint_dict)
            self.all_obj_constraint_functions[additional_constraint_name](value_dict["min"],value_dict["max"])
        
        
        return self.problem