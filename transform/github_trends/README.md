# GitHub Trend Curator

登録したキーワード（言語・技術）に基づいてGitHubのトレンドリポジトリを自動収集・可視化するパーソナルキュレーションツールです。

## 使用技術

- **Python** - メイン言語
- **httpx** - GitHub APIからデータ取得
- **DuckDB** - ローカルデータベース
- **dbt** - データ変換・集計
- **Streamlit** - ダッシュボードUI
- **Plotly** - インタラクティブグラフ

## アーキテクチャ
[GitHub API]
↓ Extract（httpx）
[DuckDB] ← Raw層
↓ Transform（dbt）
[集計テーブル] ← staging / marts
↓
[Streamlit ダッシュボード]

## 機能

- 登録キーワードに基づくリポジトリの自動収集
- 言語別トレンドの可視化
- 日別Top10の表示
- キーワードの登録・削除
- 1日1回のデータ自動更新制御

## セットアップ

### 1. リポジトリをクローン

\```bash
git clone https://github.com/あなたのユーザー名/github-trend-curator.git
cd github-trend-curator
\```

### 2. 仮想環境を作成

\```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Mac/Linux
\```

### 3. ライブラリをインストール

\```bash
pip install httpx duckdb python-dotenv streamlit plotly pandas numpy dbt-duckdb
\```

### 4. GitHubトークンを設定

\```bash
# .envファイルを作成
GITHUB_TOKEN=あなたのトークン
\```

### 5. dbtの設定

\```bash
# ~/.dbt/profiles.ymlを作成
github_trends:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: /あなたのパス/github_trends.duckdb
      schema: main
      threads: 1
\```

### 6. データを取得

\```bash
python ingest/fetch.py
cd transform/github_trends
dbt run
cd ../..
\```

### 7. アプリを起動

\```bash
streamlit run dashboard/app.py
\```

## 今後の改善予定

- [ ] dbtのテスト追加
- [ ] GitHub Actionsで定期実行の自動化
- [ ] Streamlit Cloudでデプロイ