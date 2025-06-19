# tabs/
このディレクトリには、Streamlit アプリの **タブ（サイドバー）で切り替えるコンテンツ** を管理するスクリプトを格納します。

## 📌 ディレクトリの役割
- **タブでページを切り替える構成**
- `allocation_sim_app.py` から `tabs/` の各 `.py` をインポートして使用


## 📁 タブの構成
| ファイル名 | 役割 |
|------------|-----------------------------|
| `bundling_maint_survey_web.py` | 抱き合わせ保全の組合せ調査画面（※休止中）|
| `capacity_survey_web.py` | 負荷時間不足工場の調査画面（※休止中） |
| `fine_tuning_web.py` | 確定量の微調整（※休止中） |
| `allocation_web.py` | シミュレーション実施画面 |
| `version_history.py` | バージョン履歴画面 |
| `inner_switch_formatter.py` | 月中切替時間のフォーマット取得画面（※休止中） |
| `inter_switch_formatter.py` | 月間切替時間のフォーマット取得画面 （※休止中）|




## 🛠️ 実装ルール
- `tabs/` 内の各 `.py` は `allocation_sim_app.py` から `import` される
- **各タブファイル (`tabs/*.py`) は `main()` 関数を定義し、それをエンドポイントとする**

## 🚀 使い方
```bash
streamlit run allocation_sim_app.py  # アプリを実行