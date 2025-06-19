from anytree import find, findall


"""

ある粒度レベルの名称をシミュレータで計算する際の適切な粒度（巻長・巻き方レベルとか）になおす




"""




class NameAdjuster():
    def __init__(self,root,name_list,layer_num):
        self.root = root                    #木構造
        self.name_list = name_list          #名称リスト
        self.layer_num = layer_num          #ほしい階層の番号
        
        
    def get_subroot(self,name):
        #subroot = find(self.root, lambda node: node.name == name)      #階層が違うのに名称が同じ場合にエラーになる
        
        subroot = findall(self.root, lambda node: node.name == name)    #↑回避
        subroot = subroot[0]
        
        depth = subroot.depth                                           #今の階層の深さ。
        
        diff = int(self.layer_num - depth)                              #欲しい階層の方が深い場合は正。
        return subroot, depth, diff
        
            
    
        
    def get_ancestor(self,subroot,diff):
        parent = subroot
        for j in range(abs(diff)):
            parent = parent.parent
            
        return parent.name
        
    
    def get_descendant(self,subroot):
        children = findall(self.root, lambda node: subroot in node.path and node.depth == self.layer_num)
        children_list = []
        for i in range(len(children)):
            children_list.append(children[i].name)
        
        return children_list
    
    def get_adjusted_name(self,name):
        subroot, depth, diff = self.get_subroot(name)
        if diff >= 0:
            children_list = self.get_descendant(subroot)
            return children_list
        
        if diff < 0:
            ancester = self.get_ancestor(subroot, diff)
            return ancester
    
    
    def get_all_adjusted_name(self):
        adjusted_name_dict = {}
        for i in range(len(self.name_list)):
            adjusted_name = self.get_adjusted_name(self.name_list[i])
            adjusted_name_dict[self.name_list[i]] = adjusted_name
        
        
        return adjusted_name_dict
    
if __name__ == "__main__":
    
    from tree_maker import TreeMaker
    import pandas as pd
    
    plant = "L5"
    name_table = pd.read_excel("./test/パラメーター/名称対応表.xlsx",plant)
    
    tree = TreeMaker(name_table, plant)
    root = tree.get_tree()
    
    
    a = NameAdjuster(root,["KC5VQ-1 1840"],1)
    b = a.get_all_adjusted_name()
    print(b)