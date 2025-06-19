from anytree import Node, RenderTree
from anytree import find, findall
import pandas as pd

"""
名称対応表から、木構造を作るクラス。(TreeMaker)




"""


class TreeMaker():
    # def __init__(self,file_path, plant):
    #     self.plant = plant
    #     self.name_table = pd.read_excel(file_path,sheet_name=self.plant)
    #     self.root = Node(self.plant)

    def __init__(self,name_table, plant):
         self.plant = plant
         self.name_table = name_table
         self.root = Node(self.plant)

    ##根～第1階層
    def get_first_layer(self):
        two_column = self.name_table.iloc[:,0:2]
        unique_parent = list(set(two_column.iloc[:,0]))
        #self.root = Node(unique_parent[0])
        unique_child = list(set(two_column.iloc[:,1][two_column.iloc[:,0] == unique_parent[0]]))

        first_layer_dict = {}
        for i in range(len(unique_child)):
            first = Node(unique_child[i],parent=self.root)
            first_layer_dict[unique_child[i]] = first
    
        
        return first_layer_dict
    


    #第１階層以降
    def get_next_layer(self, col_num, layer_dict):
        two_column = self.name_table.iloc[:,col_num:col_num+2]
        unique_parent = list(set(two_column.iloc[:,0]))

        next_layer_dict = {}
        unique_child_list = []
        for j in range(len(unique_parent)):
            unique_child = list(set(two_column.iloc[:,1][two_column.iloc[:,0] == unique_parent[j]]))
            unique_child_list.append(unique_child)

        for k in range(len(unique_child_list)):
            for l in range(len(unique_child_list[k])):
                next_layer = Node(unique_child_list[k][l],parent = layer_dict[unique_parent[k]])
                next_layer_dict[unique_child_list[k][l]] = next_layer
                
        return next_layer_dict
    
    
    
    def get_tree(self):
        next_layer_dict = self.get_first_layer()
        for i in range(1,len(self.name_table.columns) -1):
            next_layer_dict = self.get_next_layer(i,next_layer_dict)
            #print(next_layer_dict)
        return self.root

if __name__ == "__main__":
    
    #名称対応表の階層が違うところに同じ名称が入っていてもwラーにはならない.
    #これ、結果ファイル群の中にpickleファイルで持っておいた方がいい
    
    
    plant = "L2"
    name_table = pd.read_excel("./test/パラメーター/名称対応表.xlsx",plant)
    
    
    tree = TreeMaker(name_table, plant)
    root = tree.get_tree()
    for pre, fill, node in RenderTree(root):
        print("%s%s" % (pre, node.name))