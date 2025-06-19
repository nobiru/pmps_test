import streamlit as st
import pandas as pd

import pandas as pd
import itertools
#import xlsxwriter


class InnerSwitchFormatter():
    """
    月中
    
    """
    def __init__(self):
        pass
    


    def load_data(self,file_path, sheet_name):
        """Load data from the specified Excel sheet."""
        return pd.read_excel(file_path, sheet_name=sheet_name)

    def generate_combinations(self,factory_data, factory_columns):
        """Generate all 0/1 combinations for each factory."""
        sheets_with_combinations = {}
        for factory in factory_columns:
            products_for_factory = factory_data[factory_data[factory] == 1]
            product_names = products_for_factory['品種名'].tolist()
            combinations = list(itertools.product([0, 1], repeat=len(product_names)))
            
            sheet_data = []
            for combination in combinations:
                for pre in [0, 1]:
                    for post in [0, 1]:
                        row = {'保全前期': pre, '保全後期': post}
                        row.update(dict(zip(product_names, combination)))
                        sheet_data.append(row)
            
            sheets_with_combinations[factory] = pd.DataFrame(sheet_data)
        return sheets_with_combinations

    def sort_and_add_case_id(self,sheets):
        """Sort sheets based on 保全前期 and 保全後期 and add ケースID."""
        sorted_sheets = {}
        for factory, df in sheets.items():
            df['ケースID'] = range(1, len(df) + 1)
            df_sorted = df.sort_values(
                by=['保全前期', '保全後期'],
                key=lambda col: col.map({0: 0, 1: 2}) if col.name == '保全前期' else col.map({0: 0, 1: 1})
            ).reset_index(drop=True)
            df_sorted['ケースID'] = range(1, len(df_sorted) + 1)
            sorted_sheets[factory] = df_sorted
        return sorted_sheets

    def save_to_excel_with_formatting(self,output_path, sheets):
        """Save sorted dataframes to Excel with conditional formatting."""
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            for factory, df in sheets.items():
                df.to_excel(writer, sheet_name=f'{factory}', index=False)
                workbook = writer.book
                worksheet = writer.sheets[f'{factory}']
                red_format = workbook.add_format({'bg_color': '#FFCCCC'})
                worksheet.conditional_format(
                    1, 2, len(df), len(df.columns) - 1,
                    {'type': 'cell', 'criteria': '==', 'value': 1, 'format': red_format}
                )
    
    def output_excel(self,df, sheet_name,initial_flag=False):
        """
        エクセルファイルとしての書き出し
        一番初めに書き出す場合にinitial_flagをTrueにする
        
        """        
        if initial_flag == True:
            df.to_excel("月中切替時間_1216.xlsx",sheet_name=sheet_name,index=None)
        
        else:
            with pd.ExcelWriter("月中切替時間_1216.xlsx",engine='openpyxl', mode='a') as writer:
                df.to_excel(writer,sheet_name=sheet_name,index=None)
        
        return 
    
    
    
    
    
    
    

    def main(self):
        """
        #TODO 1の並び順、カラム順
        
        """
        """Main function to process the data and save the Excel file."""
        
        file = st.file_uploader("工場品種対応表をアップロードしてください",
                                accept_multiple_files=False)  #複数ファイルはだめ
        
        if file is not None:
        
            # Step 1: Load data
            factory_data = self.load_data(file, sheet_name='工場品種対応表')
            
            st.write(factory_data)
            factory_columns = [col for col in factory_data.columns if 'L' in col]
            
            st.write(factory_columns)
            # Step 2: Generate combinations
            sheets_with_combinations = self.generate_combinations(factory_data, factory_columns)
            
            # Step 3: Sort and add ケースID
            sorted_sheets = self.sort_and_add_case_id(sheets_with_combinations)
            
            
            for plant in factory_columns:
                if plant == "L1" or plant == "LX1":
                    initial_flag = True
                else:
                    initial_flag = False
                self.output_excel(sorted_sheets[plant], f"{plant}月中切替",initial_flag)
            
            
            
        
        
        
        #output_path = '工場1月中切替_整列済み_セル色付き修正.xlsx'
        # Step 4: Save to Excel with formatting
        #self.save_to_excel_with_formatting(output_path, sorted_sheets)
        #print(f"Program completed. File saved to: {output_path}")

 
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # def main():
        
    #     st.title("月中切替時間のフォーマット取得")
    #     st.write("------------------------------------")
        
    #     file = st.file_uploader("工場品種対応表をアップロードしてください",accept_multiple_files=False)  #複数ファイルはだめ
        
    #     pd.read_excel(file,index_col="品種名")
        
    #     sheets_sorted = {}

    #     for factory, df in sheets_with_case_id.items():
    #         # Sort based on the specified order for 保全前期 and 保全後期
    #         df_sorted = df.sort_values(
    #             by=['保全前期', '保全後期'],
    #             key=lambda col: col.map({0: 0, 1: 2}) if col.name == '保全前期' else col.map({0: 0, 1: 1})
    #         ).reset_index(drop=True)
            
    #         # Update the ケースID after sorting
    #         df_sorted['ケースID'] = range(1, len(df_sorted) + 1)
            
    #         # Store the sorted dataframe
    #         sheets_sorted[factory] = df_sorted

    #     # Save the sorted dataframes to an Excel file
    #     output_file_path_sorted = '/mnt/data/工場1月中切替_整列済み.xlsx'
    #     with pd.ExcelWriter(output_file_path_sorted, engine='xlsxwriter') as writer:
    #         for factory, df in sheets_sorted.items():
    #             df.to_excel(writer, sheet_name=f'{factory}', index=False)