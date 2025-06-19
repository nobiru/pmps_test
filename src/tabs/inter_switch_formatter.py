import streamlit as st
import pandas as pd
import itertools


class InterSwitchFormatter():
    def __init__(self):
        pass
    
    
        

    def parse_factory_data(self,row):
        """Parse group1 and group2 columns to extract unique products as single strings."""
        group1_products = [row['group1']] if pd.notna(row['group1']) else []
        group2_products = [row['group2']] if pd.notna(row['group2']) else []
        return group1_products + group2_products

    def generate_combinations(self,products):
        """Generate all 0/1 combinations for 前月_ and 当月_ columns for a given list of products."""
        product_columns = [f"前月_{p}" for p in products] + [f"当月_{p}" for p in products]
        #combinations = list(itertools.product([0, 1], repeat=len(products) * 2))
        
        combinations = list(itertools.product([0, 1], repeat=len(products) * 2))
        table = pd.DataFrame(combinations, columns=product_columns)
        table.insert(0, 'ケースid', range(1, len(table) + 1))  # Add Case ID column
        
        
        
        return table

    def create_monthly_switching_tables(self,factory_data):
        """Create switching tables for all factories."""
        factory_tables = {}
        for _, row in factory_data.iterrows():
            factory_name = row['工場']
            products = self.parse_factory_data(row)
            if products:  # Only generate table if there are products
                factory_tables[factory_name] = self.generate_combinations(products)
        return factory_tables
    
    def add_column_with_value(self,factory_tables, column_name, value=1):
        """Add a new column to a copy of the DataFrame in factory_tables with all rows filled with the specified value."""
        """Add a new column to the DataFrame with all rows filled with the specified value."""
        new_factory_tables = {}
        for factory, df in factory_tables.items():
            new_df = df.copy()
            new_df[column_name] = value
            new_factory_tables[factory] = new_df
        return new_factory_tables
    
    

    def save_tables_to_excel(self,factory_tables, output_file):
        """Save all factory switching tables to an Excel file."""
        with pd.ExcelWriter(output_file) as writer:
            for factory, table in factory_tables.items():
                table.to_excel(writer, sheet_name=factory, index=False)
                
    
    def output_excel(self,df, sheet_name,initial_flag=False):
        """
        エクセルファイルとしての書き出し
        一番初めに書き出す場合にinitial_flagをTrueにする
        
        """        
        if initial_flag == True:
            df.to_excel("月間切替時間_1216_未記入.xlsx",sheet_name=sheet_name,index=None)
        
        else:
            with pd.ExcelWriter("月間切替時間_1216_未記入.xlsx",engine='openpyxl', mode='a') as writer:
                df.to_excel(writer,sheet_name=sheet_name,index=None)
        
        return
    
    
    
    

    
    def main(self):
        
        file = st.file_uploader("ドープグループをアップロードしてください",
                                accept_multiple_files=False)  #複数ファイルはだめ
        
 
        
        if file is not None:
            sheet1_data = pd.read_excel(file, sheet_name='ドープグループ')


            # Create switching tables
            factory_switching_tables = self.create_monthly_switching_tables(sheet1_data)
            
            
            factory_switching_tables_kouki = self.add_column_with_value(factory_switching_tables, "前月_保全後期", value=1)
            factory_switching_tables_zenki = self.add_column_with_value(factory_switching_tables, "当月_保全前期", value=1)
            
            

            for plant in ["L1","L2","L3","L4","L5","L6","L7"]:
                if plant == "L1":
                    initial_flag = True
                else:
                    initial_flag = False
                self.output_excel(factory_switching_tables[plant], f"{plant}月間切替（生産品種のみ）",initial_flag)
                
            
            for plant in ["L1","L2","L3","L4","L5","L6","L7"]:
                self.output_excel(factory_switching_tables_kouki[plant], f"{plant}月間切替（保全後期）",initial_flag)
                self.output_excel(factory_switching_tables_zenki[plant], f"{plant}月間切替（保全前期）",initial_flag)
            