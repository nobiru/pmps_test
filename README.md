# AllocationOptSim

## 2.アプリ起動方法
srcディレクトリに移動し、

```
streamlit run allocation_sim_app.py
```


## 4.ディレクトリ構成

```
.
├── README.md                                   #本ファイル
├── requirements.txt                            #必要ライブラリ
└── src
    ├── allocation_sim_app.py                   #streamlitアプリのエントリーポイント
    ├── constants.py                            #定数をまとめたファイル
    ├── output_config.py                        #ファイルの出力先pathをまとめたファイル
    ├── setup_paths.py                          #ディレクトリの構成をpythonの検索pathに追加する関数
    ├── 画像1.png                               #ロゴマーク
    ├── tabs                                    #各タブに対応したUIを担当するスクリプト
    ├── optimization                            #最適化に関わるスクリプト
    ├── export                                  #出力に関わる処理及びスクリプト
    ├── libs                                    #ほぼ使っていない
    ├── logs                                    #ほぼ使っていない
    └── test                                    #ほぼ使っていない



```


## 5.簡易シーケンス図（クラスの呼び出し）

```mermaid
sequenceDiagram
    participant A as (A) AllocationWeb
    participant B as (B) HierachicalOptimizer
    participant C as (C) direct_optimizer
    participant D as (D) PuLPライブラリ（数理最適化ソルバー）


    A ->> B: A.main() が B.main() を呼び出し
    B ->> C: B.main() が C.main() を呼び出し
    
    loop 全ての目的関数が計算されるまで
        C ->> D: C.main() が Dを呼び出し、ソルバーが計算実行
        D -->> C: ソルバーが計算結果を返す
    end


    C -->> B: C.main() の処理結果を返す
    B -->> A: B.main() の処理結果を返す

```

このあと、処理結果をエクセルに出力する処理が入ります。
