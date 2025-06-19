import pulp
from model_variables import ModelVariables


class ObjectiveFunctionCatalog:
    """
    目的関数のカタログクラス。
    解きたい問題に応じて目的関数を選択する。
    
    
    """
    def __init__(self,variables: ModelVariables,problem):
        self.variables: ModelVariables = variables       #変数を格納したインスタンス
        self.problem = problem                           #最適化問題を格納したインスタンス
    
    
        self.all_objective_function_dict = {"優先SVA品種の合計生産量を最大化":self.w_sw_prod_obj_function,
                                            "サブ品種の合計生産量最小化":self.sub_prod_obj_function,
                                            "合計生産時間最大化":self.prod_time_obj_function,
                                            "基準在庫月数Max以下制約違反回数最小化":self.over_stock_obj_function,
                                            "超過月末在庫量最小化":self.over_stock_amount_obj_function,
                                            "レア品種の合計生産回数最小化":self.prod_num_obj_function,
                                            "基準在庫月数Min以上制約違反回数最小化":self.shortage_stock_obj_function,   
                                            "負荷時間以下制約違反量最小化":self.over_fuka_obj_function,
                                            "基準在庫月数Min超在庫量最小化（原因調査用）":self.almost_touch_min_stock_obj_function,
                                            "長時間ドープ切り替え回数最小化":self.long_dope_switch_obj_function,
                                            "SAZMA系品種連続生産月数最大化":self.sazma_continuous_obj_function,
                                            "保全月合計ドープ数最小化":self.maintenance_dope_num_obj_function,
                                            "メインドープによる立上・立下回数最大化":self.main_dope_num_obj_function,
                                            "メイン品種生産量最大化":self.main_prod_amount_obj_function,
                                            "合計切替時間最小化":self.total_switch_time_obj_function,
                                            "長時間ドープ切替工場合計切替時間最小化":self.long_dope_total_switch_time_obj_function,
                                            "合計生産回数最小化":self.total_prod_num_obj_function,
                                            "負荷時間スラック変数合計最小化":self.slack_sum_objective_function,
                                            "生産イベント月数最大化":self.prod_month_obj_function,
                                            "余力時間最小化":self.spare_time_objective_function,
                                            "負荷時間スラック変数合計最小化2":self.slack_sum_objective_function,
                                            "余力時間最小化2":self.spare_time_objective_function2,
                                            "基準在庫月数違反回数最小化":self.stock_range_obj_function,
                                            "7桁在庫月数合計最小化":self.stock_num_7_obj_function,
                                            "7桁基準在庫月数Max以下制約違反回数最小化":self.over_stock_7_obj_function,
                                            "7桁基準在庫月数Min以上制約違反回数最小化":self.shortage_stock_7_obj_function,
                                            "年度末7桁基準在庫月数Min以上制約違反回数最小化":self.end_shortage_stock_7_obj_function,
                                            
                                            #"負荷時間スラック余力時間最小化"
                                            }
                                            
                                            

                                            
    
    
    # def get_fuka_obj(self):
    #     """
    #     推定期間の全工場全月合計負荷時間を最小化
        
    #     発想の転換で、元々の負荷時間との差を最大化！
        
    #     """
        
    #     #実際の生産時間から求めた負荷時間
    #     jissui_month_hour_dict = {}
    #     for plant in self.variables.plant_list:
    #         total_month_hour_dict = {}
    #         for month in self.variables.jissui_month_list:
    #             month_hour_dict = {}
    #             for prod_name in self.variables.plant_prod_dict[plant]:
    #                 prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[month][plant]*100  
    #                 month_hour_dict[prod_name] = prod_time
                
                
    #             total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])    #ある工場ある月の負荷時間
            
    #         jissui_month_hour_dict[plant] = pulp.lpSum(total_month_hour_dict[month] for month in self.variables.jissui_month_list)     #ある工場の各月負荷時間合計
        
        
        
    #     # #パラメータファイルで設定した負荷時間
    #     # params_plant_hour = {}
    #     # for plant in self.variables.plant_list:
    #     #     month_hour = {}
    #     #     for month in self.variables.jissui_month_list:
    #     #         month_hour[month] = self.variables.fuka_dict[plant][month]
    #     #     params_plant_hour[plant] = pulp.lpSum(list(month_hour.values()))
         
        
    #     #定数から引く意味ないかも
    #     #obj2 = pulp.lpSum(params_plant_hour[plant] for plant in self.variables.plant_list) - pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.variables.plant_list)
    #     obj2 =  - pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.variables.plant_list)
        
    #     return obj2
    
    

        
        
    def w_sw_prod_obj_function(self):
        """
        L4 3XRW と L6 3XRSW の合計生産量を最大化
        優先SVA品種の合計生産量最大化s
        
        """
        # self.problem += pulp.lpSum([self.variables.x["L4",month,"3XR-1"] for month in self.variables.jissui_month_list]) + \
        #                 pulp.lpSum([self.variables.x["L6",month,"3XR-1SW"] for month in self.variables.jissui_month_list])
                        
        all_list = []
        for prod_tuple in self.variables.priority_sva_prod_list:
            sum_prod_amount = pulp.lpSum([self.variables.x[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_amount)
            
        self.problem += pulp.lpSum(all_list)
        
        
        
        #self.problem += pulp.lpSum(all_list) <= 10000
        #self.problem += pulp.lpSum(all_list) >= -10000
        
        
        
    def sub_prod_obj_function(self):
        """
        サブ品種（L2 4UAW、L3 2UAW、L6 3XR-UWD、L3 3XR-1）の推定期間での合計生産量を最小化
        
        基本は最大化問題として解きたい（これは好み）ので、符号を逆転させる
        
        """
        
        # self.problem += -(pulp.lpSum([self.variables.x["L2",month,"4UAW"] for month in self.variables.jissui_month_list]) + \
        #                pulp.lpSum([self.variables.x["L3",month,"2UAW"] for month in self.variables.jissui_month_list]) + \
        #                pulp.lpSum([self.variables.x["L6",month,"3XR-1UWD"] for month in self.variables.jissui_month_list])+\
        #                    pulp.lpSum([self.variables.x["L3",month,"3XR-1"] for month in self.variables.jissui_month_list]))
        
        
        all_list = []
        for prod_tuple in self.variables.sub_prod_list:
            sum_prod_amount = pulp.lpSum([self.variables.x[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_amount)
            
            self.problem += sum_prod_amount >= 0
        
        self.problem += pulp.lpSum(all_list)
        
        
        
                       
        
    
    def prod_time_obj_function(self):
        """
        推定期間の全工場合計生産時間を最大化
        
        単純にxを全部足せばよくねと思ったが、xは生産量であって、時間の変換時に品種情報が必要なので
        わざわざ品種ごとの生産時間もとめてから全部足す必要あり。
        

        
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
        
        self.problem += pulp.lpSum(jissui_month_hour_dict[plant] for plant in self.variables.plant_list)
        
    
    def over_stock_obj_function(self):
        """
        在庫上限を超える月数最小化
        
        """

        
        self.problem += (pulp.lpSum(self.variables.delta_z[multi] for multi in self.variables.multi_plant_prod_index))
        
        
    def over_stock_7_obj_function(self):
        """
        ７桁在庫上限を超える月数最小化
        
        """
        
        
        self.problem += (pulp.lpSum(self.variables.delta_7_z[prod_name,month]
                                for month in self.variables.jissui_month_list for prod_name in self.variables.all_prod_list))
        
    
    def shortage_stock_obj_function(self):
        """
        在庫下限を割る月数最小化
        
        """
        
        
        self.problem += (pulp.lpSum(self.variables.delta_mz[multi] for multi in self.variables.multi_plant_prod_index))
    
    
    def shortage_stock_7_obj_function(self):
        """
        在庫下限を割る月数最小化
        
        """
        
        
        self.problem += (pulp.lpSum(self.variables.delta_7_mz[prod_name,month]
                                for month in self.variables.jissui_month_list for prod_name in self.variables.all_prod_list))
    
    
    
    def end_shortage_stock_7_obj_function(self):
        self.problem += (pulp.lpSum(self.variables.delta_7_mz[prod_name,"3月"] for prod_name in self.variables.all_prod_list))
    
    
    
    def stock_range_obj_function(self):
        """
        在庫上限を超える月数と在庫下限を割る月数の合計最小化
        
        """
        over = (pulp.lpSum(self.variables.delta_z[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]))
        
        shortage = (pulp.lpSum(self.variables.delta_mz[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]))
        
        self.problem += over + shortage
    
    
    def stock_num_7_obj_function(self):
        """
        7桁在庫月数の合計最小化
        
        """
        
        month_num_list = []
        for prod_name in self.variables.all_prod_list:
            total_stock = [self.variables.z[plant,"3月",prod_name] for plant in self.variables.prod_plant_dict[prod_name]]
            total_stock = pulp.lpSum(total_stock)
            
            
            if self.variables.sales_dict["3月"][prod_name] > 0: 
            
                month_num = total_stock*(1/self.variables.sales_dict["3月"][prod_name])
                month_num_list.append(month_num)
        
        self.problem += pulp.lpSum(month_num_list)
        
        
    
    
    
    
    
    
    def over_stock_amount_obj_function(self):
        """
        "超過月末在庫月数最小化"
        
        無限大の発散を防ぐため、平均販売量に0.01を足して0にならんようにする。⇒変数同士の割り算なので非線形でそもそもNG。変数変換で行けるのかもしれんが。
        仕方ないので単純に超過量を合計することに。本当は月数でやりたいけどなー。7桁でやる手もあるが。
        
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
        
        
        self.problem += pulp.lpSum(over_stock_amount_list)
        
        
                    
    def prod_num_obj_function(self):
        """
        レア品種のみにした方がいいかも
        
        
        24/12/20 単なる合計ではなく、なるべくばらけてほしい
        
        
        """

        
        all_list = []
        for prod_tuple in self.variables.rare_prod_list:
            sum_prod_num = pulp.lpSum([self.variables.delta[prod_tuple[0],month,prod_tuple[1]] for month in self.variables.jissui_month_list])
            all_list.append(sum_prod_num)
            
            self.problem += sum_prod_num >= 0
        
        self.problem +=  pulp.lpSum(all_list)
        
        
        
                        
    def over_fuka_obj_function(self):
        """
        負荷時間以下制約違反量最小化
        (実際には使用生産時間最小化をしている。)
        
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

        #使用生産時間
        self.problem += (pulp.lpSum(jissui_month_hour_dict[plant] for plant in exclusion_plant_list))
        
        
        #基準在庫Minの制約を付ける(該当工場のみ？なくてもよい。（0以上制約で満足なら。）)
        # for plant in exclusion_plant_list:
        #     for month in self.variables.jissui_month_list:
        #         for prod_name in self.variables.plant_prod_dict[plant]:
        #             index = self.variables.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
        #             self.problem += stock >= ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month])
        
        #①在庫 - 基準在庫Min > 0 になる月数最小化（定式化上いけるのか？？マイナスつけるだけ？　複数品種複数工場で負荷時間足りていない時これでなにかおつりないか？）
        #翌月の月数との差最小化（3月末在庫月数でそろうことを期待。これは微妙かも）
        #
        
        
        
        
        #余力時間は0以下にしたいよってやつ(制約条件)
        #よく考えたら、必ずしも0以下にならんかも。販売量によっては。むしろ、
        #在庫月数がMinでずっと行く方が大事か。
        # for plant in exclusion_plant_list:
        #     total_month_hour_dict = {}
        #     for month in self.variables.jissui_month_list:
        #         month_hour_dict = {}
        #         for prod_name in self.variables.plant_prod_dict[plant]:
        #             prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[month][plant]*100  
        #             month_hour_dict[prod_name] = prod_time
                
        #         total_month_hour_dict[month] = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])    #ある工場ある月の負荷時間（品種で和をとる。）
                
        #         self.problem += (self.variables.fuka_dict[plant][month]-self.variables.ave_switch_dict[plant][month]) - total_month_hour_dict[month] <= 0
            
        
        
        
        
        
        
        
        # #TODO:各月各品種の基準在庫Minとの差を最小化。（複数工場またがり品種・工場でもいけるか？？）
        # for plant in exclusion_plant_list:
        #     for month in self.variables.jissui_month_list:
        #         for prod_name in self.variables.plant_prod_dict[plant]:
        #             index = self.variables.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
        #             self.problem += -(stock - ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month]))
        
        
    
    
    def maintenance_dope_num_obj_function(self):
        """
        TODO 3ドープ以上ある工場や、
        
        2024/12/22  ドープグループに書き換え。
        
        """
        dope_num_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.maint_month_list[plant]:
                dope_num_list.append(pulp.lpSum([self.variables.group1_flag[plant,month],self.variables.group2_flag[plant,month]]))
        
                self.problem += pulp.lpSum(pulp.lpSum([self.variables.group1_flag[plant,month],self.variables.group2_flag[plant,month]])) >= 0
        self.problem += pulp.lpSum(dope_num_list)
        
    
    
        
        
    def almost_touch_min_stock_obj_function(self):
        """
        なるべく基準在庫Minすれすれにするため。
        負荷時間以下制約を外して実行するときにつかう。
        
        
        
        """
        
        
        #TODO 確定生産量とか確定販売量との兼ね合いでこの基準在庫Minの制約守られない危険性あり。（解無し）このように新たに制約を増やすのはよくないかも。目的関数経由がいいか。
        exclusion_plant_list = list(set(self.variables.plant_list) -
                                    set(self.variables.constraint_plant_dict["負荷時間以下制約"]))
        # #基準在庫Minの制約を付ける(該当工場のみ？なくてもよい。（0以上制約で満足なら。）)
        # for plant in exclusion_plant_list:
        #     for month in self.variables.jissui_month_list:
        #         for prod_name in self.variables.plant_prod_dict[plant]:
        #             index = self.variables.jissui_month_list.index(month)
                    
        #             #月末在庫
        #             stock = self.variables.init_stock_dict[prod_name][plant] + pulp.lpSum(self.variables.x[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1]) - pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.jissui_month_list[:index+1])
                    
        #             #翌月以降〇ヶ月の平均販売量（ひと月当たり）
        #             ave_sales = pulp.lpSum(self.variables.y[plant,month2,prod_name] for month2 in self.variables.ave_month_dict[month])/len(self.variables.ave_month_dict[month])
                    
        #             self.problem += stock >= ave_sales*(self.variables.basic_stock_min_dict[prod_name][plant][month])
        
        
        #TODO:各月各品種の基準在庫Minとの差を最小化。（複数工場またがり品種・工場でもいけるか？？）
        
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
                    
        
        
        self.problem += (pulp.lpSum(diff_list))
    
    
    def long_dope_switch_obj_function(self):
        """
        長時間ドープ切り替え回数最小化
        
        """
        self.problem += -(pulp.lpSum(self.variables.dope_switch_flag[month] for month in self.variables.jissui_month_list))
    
    
    def sazma_continuous_obj_function(self):
        #self.problem += pulp.lpSum(self.variables.sazma_continuous_flag[month] for month in self.variables.jissui_month_list)
        
        self.problem += (pulp.lpSum(self.variables.sazma_to_sva_flag[month] for month in self.variables.jissui_month_list)+\
                          pulp.lpSum(self.variables.sva_to_sazma_flag[month] for month in self.variables.jissui_month_list))
        
    
    
    def main_dope_num_obj_function(self):
        """
        メインドープによる立上、立下回数を最大化する。
        
        
        本当は保全のある月と同義ではないが、一旦これでいく
        保全入っている前後の月に立上立下の可能性もあるので。。。。
        
        """
        
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
            
            self.problem += pulp.lpSum(dope_flag[plant,month] for month in self.variables.maint_month_list[plant]) >=0
            self.problem += pulp.lpSum(dope_flag[plant,month] for month in self.variables.maint_month_list[plant]) <=50
        
        self.problem += pulp.lpSum(num_list)
        
    
    
    def main_prod_amount_obj_function(self):
        """
        メイン品種生産量最大化
        
        """
        amount_list = []
        for plant in self.variables.plant_list:
            main_prod = self.variables.main_dope_prod_dict[plant]["メイン品種"]
            amount = pulp.lpSum(self.variables.x[plant,month,main_prod] for month in self.variables.jissui_month_list)
            amount_list.append(amount)
        total_amount = pulp.lpSum(amount_list)
        
        self.problem += total_amount
    
            
    
    
    def total_switch_time_obj_function(self):
        """
        全工場合計切替時間最小化
        
        とりあえず工場毎に切り替え時間を足してその合計とする。
        その方が確実に長時間の切替なくなりそう
        
        あれ、でも↑ふつうに合計するのと同じことしてる？？
        
        """
        temp_list = []
        for plant in self.variables.plant_list:
            total_inner_switch = pulp.lpSum(self.variables.switch_time[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_head = pulp.lpSum(self.variables.inter_switch_time_head[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_tail = pulp.lpSum(self.variables.inter_switch_time_tail[plant,month] for month in self.variables.jissui_month_list)
            
            total_switch = total_inner_switch + total_inter_switch_time_head + total_inter_switch_time_tail
            temp_list.append(total_switch)
        
        self.problem += pulp.lpSum(temp_list)
    
    
    def long_dope_total_switch_time_obj_function(self):
        """
        長時間のdope切替が入る全工場合計切替時間最小化
        
        とりあえず工場毎に切り替え時間を足してその合計とする。
        その方が確実に長時間の切替なくなりそう
        
        あれ、でも↑ふつうに合計するのと同じことしてる？？
        
        """
        temp_list = []
        
        long_dope_plant_list = ["L3","L6","L7"]
        
        #long_dope_plant_list = ["L6"]
        
        for plant in long_dope_plant_list:
            total_inner_switch = pulp.lpSum(self.variables.switch_time[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_head = pulp.lpSum(self.variables.inter_switch_time_head[plant,month] for month in self.variables.jissui_month_list)
            total_inter_switch_time_tail = pulp.lpSum(self.variables.inter_switch_time_tail[plant,month] for month in self.variables.jissui_month_list)
            
            total_switch = total_inner_switch + total_inter_switch_time_head + total_inter_switch_time_tail
            temp_list.append(total_switch)
            
            self.problem += total_switch >= -100
        
        self.problem += pulp.lpSum(temp_list)
        
        self.problem += pulp.lpSum(temp_list) >=0
        
    
    
    
    def total_prod_num_obj_function(self):
        """
        合計生産回数最小化
        """
        
        #self.problem += -pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
        #                        for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant])
    
    
        self.problem += pulp.lpSum(self.variables.delta[plant,month,prod_name] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant])
    
    
    
    
    def prod_month_obj_function(self):
        """
        なにかしら生産イベントが入るようにするための目的関数
        まるまる余力時間残してしまう生産計画が出力されるのを防ぐために作成
        
        """
        self.problem += pulp.lpSum(self.variables.all_prod_flag[plant,month]for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list)
        
        
        
        
        
    
    
    
    
    
    
    def slack_sum_objective_function(self):
        """
        スラック変数合計最小化
        
        """
        
        self.problem += pulp.lpSum(self.variables.slack[plant,month] for plant in self.variables.plant_list
                                for month in self.variables.jissui_month_list)
    
    
    def spare_time_objective_function(self):
        """
        余力時間最小化
        
        """
        
        yoryoku_time_list = []
        for plant in self.variables.plant_list:
            for month in self.variables.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.variables.plant_prod_dict[plant]:
                    prod_time = self.variables.x[plant,month,prod_name]*1000/self.variables.width_dict[prod_name]/self.variables.cs_dict[prod_name][plant][month]/60/self.variables.achieve_rate_dict[prod_name][plant][month]  
                    month_hour_dict[prod_name] = prod_time
                
                #負荷時間
                fuka_time = self.variables.prod_capacity_dict[plant][month]["暦日時間"] - (self.variables.prod_capacity_dict[plant][month]["開発テスト"]+
                                                                             self.variables.prod_capacity_dict[plant][month]["生技テスト"]+
                                                                             self.variables.maint_hour_dict[plant][month]+
                                                                             self.variables.prod_capacity_dict[plant][month]["計画停止"])
                #生産時間の合計
                all_prod_time = pulp.lpSum(month_hour_dict[prod_name] for prod_name in self.variables.plant_prod_dict[plant])
                
                yoryoku_time = (fuka_time - self.variables.switch_time[plant,month] - 
                                self.variables.inter_switch_time_head[plant,month] - 
                                self.variables.inter_switch_time_tail[plant,month] - all_prod_time) + self.variables.slack[plant,month]
                
                
                self.problem += yoryoku_time >= 0              #なんかy余力時間がマイナスな答えも許容してしまうことがあるっぽいので。制約条件つけとく
                
                #self.problem += yoryoku_time <= 1000
                
                #self.problem += all_prod_time >= 0
                
                yoryoku_time_list.append(yoryoku_time)
        
        self.problem += pulp.lpSum(yoryoku_time_list)
                
                
        
    def spare_time_objective_function2(self):
        """
        余力時間最小化スラック変数ないバージョン
        
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
        
        self.problem += pulp.lpSum(yoryoku_time_list)
        
        
        
    def define_objective_function(self,obj_name):
        """
        目的関数部分
        
        """
        if obj_name is None:
            self.problem += 5
            #self.problem += pulp.lpSum([self.variables.x[plant,month,prod_name] for plant in self.variables.plant_list for month in self.variables.jissui_month_list for prod_name in self.variables.plant_prod_dict[plant]])
            #self.problem += pulp.lpSum([self.variables.x["L6","9月","3XR-1SW"]])
        
        
        # if obj_name == "負荷時間スラック変数合計最小化":
        #     self.slack_objective_function()
        
        
        if obj_name is not None:
           self.all_objective_function_dict[obj_name]()