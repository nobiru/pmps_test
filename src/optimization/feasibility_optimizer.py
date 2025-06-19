
import pulp
from direct_opimizer import DirectOptimizer




class FeasibilityOptimizer:
    """
    実行可能性判定問題として解くクラス
    
    
    この中で目的関数⇒制約への書き替えやるべきなのか、この外でやるべきなのか。
    ここでやらんとこのクラスの意味ない。
    
    てか、このクラスで目的関数⇒制約の書き換えしたらDirectOptimizer呼び出せばええやんっていう。
    
    """
    def __init__(self, all_params_dict,additional_constraint_dict,obj_name,obj_constraint_name,init_num,timelimit,
                 pre_solution
                 ):
        
        
        self.constraint_list = all_params_dict["constraint_list"]                              #今回のシミュで共通して使う制約条件の名前リスト
        self.additional_constraint_dict = additional_constraint_dict                           #追加制約条件名の辞書(key:制約名、value:目的関数値（これと等しいとして制約条件とする）)
        self.obj_name = obj_name                                                               #目的関数名                                                             #最適化時間制限
        
        self.all_params_dict = all_params_dict
        
        self.obj_constraint_name = obj_constraint_name                                        #目的関数値を制約条件として扱う制約条件名
        self.init_num = init_num    #初期値
        
        length = 200

        # init_numの正負を判定してリストを作成します（#TODO これもしかしたら分岐いらんかも。最小化か最大化かさえわかれば）
        if init_num > 0:
            self.int_list = [init_num - i for i in range(length)]  # 降順で30個の整数リスト
        elif init_num <= 0:
            self.int_list = [init_num + i for i in range(length)]  # 昇順で30個の整数リスト
        
        
        #self.timelimit = timelimit
        self.timelimit = 30
        
        
        self.pre_solution = pre_solution                                             #前階層の解を初期解として使う
        
        self.pre_solutiuon = None
        
        #しかし、制約に書き換えているので、初期解が実行可能解である保証はない。
        #よって、初期解が実行可能解であるかどうかを判定するようなアルゴリズムを書く必要がある。
        
        
        
        

    def main(self):
        
        ##
        timelimit_tmp=3000                        #タイムアウトする計算時間は
        for obj_num in self.int_list:
            
            print(f"{obj_num}でいきまーす")
            print(self.additional_constraint_dict)
            self.additional_constraint_dict[self.obj_constraint_name] = {}
            self.additional_constraint_dict[self.obj_constraint_name]["min"] = obj_num
            self.additional_constraint_dict[self.obj_constraint_name]["max"] = obj_num
            
            
            
            
            
            DO = DirectOptimizer(self.all_params_dict,
                            None,
                            self.additional_constraint_dict,
                            timelimit_tmp,
                            self.pre_solutiuon)
            self.variables, self.problem,self.solver = DO.main()
            
            status = pulp.LpStatus[self.problem.status]  # LpStatusで状態を文字列に変換
            
            if status == "Optimal":
                break
            
            if status == "Not Solved":
                timelimit_tmp = timelimit_tmp*2                  #タイムアウトする計算時間を増やす
                
                #TODO初期解を更新
                
                
                
                
                
                
                
                
        
        if status != "Optimal":
            print("実行可能性判定問題で最適解が見つかりませんでした")
        
        return self.variables, self.problem, obj_num, self.solver