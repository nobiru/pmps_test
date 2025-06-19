import sys
from pathlib import Path

def add_project_paths():
    """
    プロジェクトのディレクトリをPythonの検索パスに追加する。
    エントリーポイントで呼び出すことによって、プロジェクト内のモジュールをimportできるようになる。
    
    ディレクトリ構成が変わる場合はコチラをメンテする。
    """
    root_path = Path(__file__).resolve().parent
    sys.path.append(str(root_path))                     # ルートディレクトリ(src)
    sys.path.append(str(root_path / 'tabs'))            # tabディレクトリ
    sys.path.append(str(root_path / 'optimization'))    # optimizationディレクトリ
    sys.path.append(str(root_path / 'export' / "scripts" ))  # scriptsディレクトリ

    