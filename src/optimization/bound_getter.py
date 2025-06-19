
import pickle

class BoundGetter:
    """
    決定変数のlower_bound, upper_boundを取得するクラス
    理論的にキワキワを設定することで計算高速化を計る
    
    
    
    """
    def __init__(self, all_params_dict):
        self.sales_dict = all_params_dict["sales_dict"]
        self.safety_up_margin = 1.1                        #理論上の上限に掛ける係数
        

    def get_sales_bound(self):
        sales_bound_dict = {}
        return sales_bound_dict



    def main(self):
        self.get_sales_bound()


if __name__ == "__main__":
    
    with open("./test/all_params_dict.pickle", mode='rb') as f:
        all_params_dict = pickle.load(f)
    
    
    bg = BoundGetter(all_params_dict)
    bg.main()
        
        