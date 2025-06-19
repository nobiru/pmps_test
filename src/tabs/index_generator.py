
from collections import defaultdict
from itertools import chain, combinations


class CommonProcess():
    """
    最適化計算のための入力パラメタ、最適化計算後の結果取り出し
    の双方で必要なデータについて適切な形式に変換するクラス。
    
    #TODO 名前変える。
    
    
    """
    def __init__(self,jissui_month_list,cs_dict):
        self.cs_dict = cs_dict                             #cs
        self.jissui_month_list = jissui_month_list         #推定月

        
    
    def get_all_index(self):
        """
        決定変数の添え字を取得。（工場,月,品種名）というタプルのリスト。
        総当たりではなく、その工場でその品種作れるもののみ。（変数削減のため）
        
        
        
        csは、
        {"6UAW":{
            "L3":{
                "4月":62,
                "5月":62,
                "6月":62,
        
        """
        all_prod_list = list(self.cs_dict.keys())     #全品種名リスト(生産品種のみ。CS入力の無い品種は無視する（たとえ販売があっても。生産しないのなら本質的に最適化に関係ないと判断。）)
        
        all_index = []
        for prod_name in all_prod_list:
            plant_list = list(self.cs_dict[prod_name].keys())
            for plant in plant_list:
                temp = [(plant,month,prod_name) for month in self.jissui_month_list]
                all_index = all_index+temp
        
        
        return all_index
    
    
    def get_multi_plant_prod_index(self,all_index):
        """
        複数工場で生産可能な品種の添え字を取得。
        工場が複数ある品種の添え字のリストを取得する。
        
        """
        product_factory_map = defaultdict(set)
        for plant, month, product in all_index:
            product_factory_map[product].add(plant)

        # 複数工場にある品種を抽出
        multiple_factory_products = {product for product, factories in product_factory_map.items() if len(factories) > 1}

        # その品種に該当するタプルを取得
        multi_plant_prod_index = [entry for entry in all_index if entry[2] in multiple_factory_products]

        # 結果表示
        print(multi_plant_prod_index)
        
        return multi_plant_prod_index

    


    def get_plant_prod_dict(self,all_index):
        """
        キー：工場 value:品種リスト
        
        
        """
        plant_list = list(set([index[0] for index in all_index]))
        
        plant_prod_dict = {}
        for plant in plant_list:
            prod_list = list(set([index[2] for index in all_index if plant == index[0]]))
            plant_prod_dict[plant] = prod_list
        
        return plant_prod_dict
        
    def get_prod_plant_dict(self,all_index):
        """
        キー：品種 value:工場リスト
        
        
        """
        all_prod_list = list(self.cs_dict.keys())     #全品種名リスト
        
        prod_plant_dict = {}
        for prod_name in all_prod_list:
            plant_list = list(set([index[0] for index in all_index if prod_name == index[2]]))
            prod_plant_dict[prod_name] = plant_list
        
        return prod_plant_dict
    
    
    def get_single_factory_prod(self,prod_plant_dict):
        
        """
        単一工場品種のリストを作成
        
    
        """
        
        all_prod_list = list(self.cs_dict.keys())     #全品種名リスト
        
        single_factory_prod_list = []
        
        for prod in all_prod_list:
            plant_list = prod_plant_dict[prod]
            if len(plant_list) == 1:
                single_factory_prod_list.append(prod)
        return single_factory_prod_list
    
    

    
    
    def get_plant_month_index(self,all_index):
        
        plant_list = list(set([index[0] for index in all_index]))
        
        # リスト内包表記で総当たりのタプルのリストを作成
        plant_month_index = [(x, y) for x in plant_list for y in self.jissui_month_list]
        
        return plant_month_index
    
    
    def get_prod_month_index(self):
        #全品種名リスト(生産品種のみ。CS入力の無い品種は無視する（たとえ販売があっても。生産しないのなら本質的に最適化に関係ないと判断。）)
        all_prod_list = list(self.cs_dict.keys())     
        
        prod_month_index = [(x, y) for x in all_prod_list for y in self.jissui_month_list]
        
        return prod_month_index
    
    
    
    
    
    
    def main(self):
        all_index = self.get_all_index()
        plant_prod_dict = self.get_plant_prod_dict(all_index)
        prod_plant_dict = self.get_prod_plant_dict(all_index)
        single_factory_prod_list = self.get_single_factory_prod(prod_plant_dict)
        
        plant_month_index = self.get_plant_month_index(all_index)
        
        prod_month_index = self.get_prod_month_index()
        
        
        multi_plant_prod_index = self.get_multi_plant_prod_index(all_index)
        
        return all_index, plant_prod_dict, prod_plant_dict, single_factory_prod_list,\
                plant_month_index, prod_month_index, multi_plant_prod_index





    