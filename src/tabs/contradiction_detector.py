
import streamlit as st

class ContradictionDetector():
    """"
    
    入力パラメータが明らかにオカシイ場合に、それを補足する関数を
    まとめたクラス。
    
    
    """
    def __init__(self,all_params_dict):
        
        
        self.all_index = all_params_dict["all_index"]
        self.plant_prod_dict = all_params_dict["plant_prod_dict"]
        self.prod_plant_dict = all_params_dict["prod_plant_dict"]
        
        self.jissui_month_list = all_params_dict["jissui_month_list"]
        #self.fuka_dict = all_params_dict["fuka_dict"]
        #self.ave_switch_dict = all_params_dict["ave_switch_dict"]
        self.sales_dict = all_params_dict["sales_dict"]
        self.cs_dict = all_params_dict["cs_dict"]
        self.finalized_sales_dict =all_params_dict["finalized_sales_dict"]
        self.finalized_prod_dict = all_params_dict["finalized_prod_dict"]
        self.init_stock_dict = all_params_dict["init_stock_dict"]
        self.prod_num_times_dict = all_params_dict["prod_num_times_dict"]
        self.min_continuous_dict = all_params_dict["min_continuous_dict"]
        self.basic_stock_max_dict = all_params_dict["basic_stock_max_dict"]
        self.basic_stock_min_dict = all_params_dict["basic_stock_min_dict"]
        self.width_dict = all_params_dict["width_dict"]
        self.achieve_rate_dict = all_params_dict["achieve_rate_dict"]
        
        
        self.prod_capacity_dict = all_params_dict["prod_capacity_dict"]
        
        #self.plant_list = list(self.fuka_dict.keys())
        
        self.plant_list = list(self.prod_capacity_dict.keys())
        self.prod_list = list(self.basic_stock_max_dict.keys())

        
        #st.write(self.plant_prod_dict)
        #st.write(self.finalized_prod_dict)
        
        
    def fuka_switch_contradiction(self):
        # 負荷時間 < 平均切り替え時間 の捕捉
        error_list = []
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                diff = self.fuka_dict[plant][month] - self.ave_switch_dict[plant][month]
                if diff < 0:
                    element = {"エラー箇所":(plant,month),
                            "エラー内容":"負荷時間よりも平均切り替え時間が大きい"}
                    error_list.append(element)

        return error_list
    
    def basic_stock_contradiction(self):
        # 基準在庫月数Max < 基準在庫月数Min の捕捉
        error_list = []
        for prod in self.prod_list:
            for plant in self.prod_plant_dict[prod]:
                for month in self.jissui_month_list:
                    diff = self.basic_stock_max_dict[prod][plant][month] - self.basic_stock_min_dict[prod][plant][month]
                    if diff < 0:
                        element = {"エラー箇所":(plant,prod,month),
                            "エラー内容":"基準在庫月数Maxよりも基準在庫月数Minが大きい"}
                        error_list.append(element)
        
        return error_list
    
    
    
    def prod_num_contradiction(self):
        # 最大生産回数 < 最低生産回数 の捕捉

        error_list = []
        for prod in self.prod_list:
            for plant in self.prod_plant_dict[prod]:
                    diff = self.prod_num_times_dict[prod][plant]["max"] - self.prod_num_times_dict[prod][plant]["min"]
                    if diff < 0:
                        element = {"エラー箇所":(plant,prod),
                            "エラー内容":"最大生産回数よりも最低生産回数が大きい"}
                        error_list.append(element)
        
        return error_list
    
    def fuka_finalized_production_contradiction(self):
        """
        確定生産量を時間に直した際に
        各工場各月合計が（負荷時間-切り替え時間）を超えている場合
        
        #TODO 計算あっているか確認
        
        """
        error_list = []
        for plant in self.plant_list:
            for month in self.jissui_month_list:
                month_hour_dict = {}
                for prod_name in self.plant_prod_dict[plant]:
                    #確定生産量の設定があればその値。なければ0
                    try:
                        prod_time = self.finalized_prod_dict[prod_name][plant][month]*1000/self.width_dict[prod_name]/self.cs_dict[prod_name][plant][month]/60/self.achieve_rate_dict[month][plant]*100  
                    except:
                        prod_time = 0
                    
                    month_hour_dict[prod_name] = prod_time     #キー品種名、バリュー生産時間
                
              
                
                total = sum(month_hour_dict[prod_name] for prod_name in self.plant_prod_dict[plant])    #月ごとの合計生産時間
                
                
                diff = self.fuka_dict[plant][month]-self.ave_switch_dict[plant][month] - total     #totalの方が大きい時はngとする
                
                
                #小数点以下数桁のせいで×になるのは避けたいので、0未満ではなく、-0.1未満とする(確定生産と確定販売の制約は+-1バッファ持たせてるので大丈夫)
                if diff < -0.1:
                    element = {"エラー箇所":(plant,month),
                               f"エラー内容":f"確定生産量の合計を時間に変換すると生産可能時間よりも{round(abs(diff),2)}時間多い"}
                    error_list.append(element)
        
        return error_list
    
    def finalized_sales_contradiction(self):
        """
        確定販売量の合計が合計販売量を超えている場合
        
        #TODO 計算あっているか確認
        """
        
        error_list = []
        for prod_name in self.prod_list:
            for month in self.jissui_month_list:
                plant_dict = {}
                for plant in self.prod_plant_dict[prod_name]:
                    try:

                        plant_dict[plant] = self.finalized_sales_dict[prod_name][plant][month]
                    except:
                        plant_dict[plant] = 0
                
                total = sum(plant_dict[plant] for plant in self.prod_plant_dict[prod_name])
                
                diff = self.sales_dict[month][prod_name] - total
                
                if diff < 0:
                    element = {"エラー箇所":(month,prod_name),
                               f"エラー内容":f"確定販売量の合計が7桁販売量よりも{round(abs(diff),2)}千平米多い"}
                    error_list.append(element)
        return error_list
        
    
    
    
    def jissui_select_missing(self):
        """
        推定月にゼロうめあったらエラー出す
        
        """
        
        error_list = []
        for month in self.jissui_month_list:
            total = sum(self.sales_dict[month].values())
            if total == 0:
                element = {f"エラー内容":f"実推選択が間違っています。"}
                error_list.append(element)
        
        return error_list
            
            
    
    

    
    
    def main(self):
        
        
        
        #fuka_error_list = self.fuka_switch_contradiction()
        basic_stock_error_list = self.basic_stock_contradiction()
        prod_num_error_list = self.prod_num_contradiction()
        #fuka_finalized_production_error_list = self.fuka_finalized_production_contradiction()
        finalized_sales_error_list = self.finalized_sales_contradiction()
        
        jissui_select_error_list = self.jissui_select_missing()
        
        
        all_error_list = jissui_select_error_list + basic_stock_error_list + \
                         prod_num_error_list +\
                        finalized_sales_error_list
        
        
        
        if len(all_error_list) != 0:
            for error in all_error_list:
                st.error(error)
        
        
        return len(all_error_list)
                
        
        
        
        