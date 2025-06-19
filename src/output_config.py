from pathlib import Path

# プロジェクトのルートディレクトリ
ROOT_DIR = Path(__file__).resolve().parent

# 結果出力先ディレクトリ
RESULT_DIR = ROOT_DIR / 'export/results'
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# 解出力先ディレクトリ
SOLUTION_DIR = ROOT_DIR / 'export/solutions'
SOLUTION_DIR.mkdir(parents=True, exist_ok=True)

# ソルバーが出力するファイル入れ先（計算終了後ファイルは削除される）
SOLVER_TEMP_DIR = ROOT_DIR / "export" / "solver_temp"
SOLVER_TEMP_DIR.mkdir(parents=True, exist_ok=True)

