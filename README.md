# GitHub Trend Curator

登録したキーワード（言語・技術）をもとにGitHubのリポジトリを毎日取得・蓄積し、言語別トレンドや日別Top10を可視化するデータダッシュボードです。

## 概要

データエンジニアリングの基礎を実践的に学ぶために開発しました。GitHub APIからデータを取得してDuckDBに保存し、dbtで整形・集計してStreamlitで可視化するELTパイプラインを構築しています。

## アーキテクチャ
```
GitHub API
↓ Extract（httpx）
DuckDB（Raw層）
↓ Transform（dbt）
DuckDB（staging / marts層）
↓
Streamlit ダッシュボード
```
## 機能

- キーワード（言語・技術）の登録・削除
- 登録キーワードに一致するリポジトリの取得・蓄積
- 言語別スター数のトレンド可視化
- 日別Top10リポジトリの表示
- 1日1回のデータ取得制御（API制限対策）

## 使用技術

| 技術 | 用途 |
|---|---|
| Python | メイン言語 |
| httpx | GitHub APIからデータ取得 |
| DuckDB | ローカル分析用データベース |
| dbt | データ整形・集計（ELTのT） |
| Streamlit | ダッシュボードUI |
| Plotly | インタラクティブグラフ |

## セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/Hryuta-dev/github-trend-curator.git
cd github-trend-curator
```

### 2. 仮想環境を作成・有効化

```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# Mac/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. ライブラリをインストール

```bash
pip install httpx duckdb python-dotenv streamlit plotly pandas numpy dbt-duckdb
```

### 4. GitHubトークンを設定

`.env`ファイルをプロジェクトルートに作成して以下を記入してください。

GITHUB_TOKEN=あなたのトークン

GitHubトークンは[こちら](https://github.com/settings/tokens)から発行できます。スコープは不要です。

### 5. dbtの設定

`~/.dbt/profiles.yml`を作成して以下を記入してください。

```yaml
github_trends:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: /あなたのパス/github_trends.duckdb
      schema: main
      threads: 1
```

### 6. データを取得してアプリを起動

```bash
# データ取得
python ingest/fetch.py

# dbtでデータ整形
cd transform/github_trends
dbt run
cd ../..

# アプリ起動
streamlit run dashboard/app.py
```

ブラウザで`http://localhost:8501`を開いてください。

## ディレクトリ構成
```
github-trend-curator/
├── ingest/
│   └── fetch.py              # GitHub APIからデータ取得・保存
├── transform/
│   └── github_trends/
│       └── models/
│           ├── staging/
│           │   └── stg_repositories.sql  # データ整形
│           └── marts/
│               ├── language_trends.sql   # 言語別集計
│               └── daily_top10.sql       # 日別Top10
├── dashboard/
│   └── app.py                # Streamlitダッシュボード
├── keywords.json             # 追跡キーワード設定
├── .env                      # GitHubトークン（要作成）
└── README.md,
```
## 今後の改善予定

- [ ] dbtのテスト追加
- [ ] GitHub Actionsで定期実行の自動化
- [ ] Streamlit Cloudでデプロイ
