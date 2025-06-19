import pandas as pd
import streamlit as st
from pathlib import Path

class VersionHistory():
    """
    Excelファイルからバージョン履歴を読み込み、Streamlitライブラリを使用してウェブアプリケーションに表示するためのクラス。

    Attributes
    ----------
    file_path : str
        バージョン履歴が保存されているExcelファイルのパス。

    Methods
    -------
    __init__(self)
        クラスの初期化メソッド。Excelファイルのパスをクラス変数に設定します。

    main(self)
        Excelファイルからバージョン履歴を読み込み、更新日を整形してStreamlitアプリケーションに表示します。
        また、バージョン番号の変更ポリシーについての情報も表示します。

    Notes
    -----
    - Excelファイルは"バージョン履歴.xlsx"という名前で、このスクリプトと同じディレクトリに配置する必要があります。
    - このクラスの利用にはpandasライブラリとStreamlitライブラリが必要です。
    - 更新日は日付に最も近い値に丸められ、文字列形式で表示されます。
    - バージョン番号の変更ポリシーは、アプリケーション内の展開可能セクションで説明されます。
    """
    
    
    
    def __init__(self):
        
        # `data/` ディレクトリのパスを取得
        DATA_DIR = Path(__file__).resolve().parent
        self.EXCEL_PATH = DATA_DIR / "バージョン履歴.xlsx"
        
        
        
        
    
    def main(self):
        st.title("バージョン履歴")
        st.write("")
        st.write("------------------------")
        df = pd.read_excel(self.EXCEL_PATH)
        df["更新日"] = df["更新日"].dt.round("D")
        
        
        df["更新日"] = df["更新日"].astype(str)
        
        #style = df.style.hide_index()          #pandasのバージョン違いでエラーになる
        style = df.style.hide(axis="index")
        
        
        
        #表示
        st.write(style.to_html(), unsafe_allow_html=True,)
        
        
        #プログラムの修正で見た目変わらん⇐一番下のバージョン変える
        # 画面が変わる⇒二桁目を変える 
        st.write("")
        st.write("")
        with st.expander(label="バージョン番号変更ポリシー"):
            st.write("バグの修正等の軽微な変更はバージョン番号の一番右の数字を上げる。（パッチバージョン）")
            st.write("新機能の追加はバージョン番号の真ん中の数字を上げる。（マイナーバージョン）")
            st.write("上記以上の超大規模変更の場合はバージョン番号の一番左の数字を上げる。（メジャーバージョン）")