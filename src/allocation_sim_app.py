
import sys
from pathlib import Path
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu



from setup_paths import add_project_paths
add_project_paths()

from allocation_web import AllocationWeb
from version_history import VersionHistory
from inner_switch_formatter import InnerSwitchFormatter
from inter_switch_formatter import InterSwitchFormatter
from capacity_survey_web import CapacitySurveyWeb
from fine_tuning_web import FineTuningWeb
from approx_formula_web import ApproxFormulaWeb
from bundling_maint_survey_web import BundlingMaintSurveyWeb

##############################################################################
### 生産計画シミュレータwebアプリの全体構造をつかさどるスクリプトです。 #########
##############################################################################

#


# プロジェクトのルートディレクトリを基準にする
project_root = Path(__file__).resolve().parent.parent  # スクリプトのディレクトリを取得
image_path = project_root / "src/画像1.png"





img = Image.open(image_path)
version = "ver8.6.0"

st.set_page_config(page_title=f"工場・月度割り当て最適化シミュレータ {version}",
                   page_icon=img,
                   layout="wide",
                   initial_sidebar_state="auto")

#他にもシミュパターン増えたら個々に追加してゆく
PAGES = {
         #"切替時間の近似式取得":ApproxFormulaWeb(),
         "抱き合わせ保全の組合せ調査":BundlingMaintSurveyWeb(),
         "負荷時間不足工場の調査":CapacitySurveyWeb(),
         "確定量の微調整":FineTuningWeb(),
         "製膜工場シミュレーション実施":AllocationWeb(),
         "オフライン工場シミュレーション実施":AllocationWeb("オフライン工場"),
         "バージョン履歴":VersionHistory(),
         "月中切替時間のフォーマット取得":InnerSwitchFormatter(),
         "月間切替時間のフォーマット取得":InterSwitchFormatter()
         }        
st.write()


st.sidebar.image(img, use_column_width=True)

with st.sidebar:
    st.title(version)
    st.markdown(f'<h1 style="color:#595959;font-size:12px;">{"メインメニュー"}</h1>', unsafe_allow_html=True)
    selection = option_menu(None,["抱き合わせ保全の組合せ調査",
                                  "負荷時間不足工場の調査","確定量の微調整","製膜工場シミュレーション実施",
                                  "オフライン工場シミュレーション実施","バージョン履歴",
                                  "月中切替時間のフォーマット取得","月間切替時間のフォーマット取得"], 
        icons=["","bi-search","bi-wrench-adjustable","robot","robot","clock-history"], menu_icon="cast", default_index=3,
        styles={
        "nav-link-selected": {"background-color": "#009F3A"},
    })
page = PAGES[selection]
page.main()


    
