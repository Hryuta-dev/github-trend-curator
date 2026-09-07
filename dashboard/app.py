import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd
import json
import os

DB_PATH = "github_trends.duckdb"

def get_con():
    return duckdb.connect(DB_PATH)

st.title("GitHub Trend Curator")
st.caption("あなたのキーワードに基づいたGitHubトレンド分析")

# サイドバー
st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ選択", ["トップ", "今日上昇", "言語トレンド", "リポジトリ一覧","設定"])

if page == "トップ":
    st.header("今日のTop10")

    con = get_con()
    df = con.execute("""
        SELECT name, language, stargazers_count, description, html_url
        FROM daily_top10
        WHERE fetched_date = (SELECT MAX(fetched_date) FROM daily_top10)
        ORDER BY rank
    """).fetchdf()
    con.close()

    for _, row in df.iterrows():
        with st.expander(f"⭐ {row['stargazers_count']:,}  {row['name']} ({row['language']})"):
            st.write(row['description'])
            st.markdown(f"[GitHubで見る]({row['html_url']})")

elif page == "今日上昇":
    st.header("今日上昇")

    con = get_con()
    df_growth = con.execute("""
        SELECT name, today_stars, zouka
        FROM daily_top10_by_growth
        WHERE today_date = (SELECT MAX(today_date) FROM daily_top10_by_growth)
        ORDER BY trend_rank
    """).fetchdf()
    df_growth_rate = con.execute("""
        SELECT name, today_stars, zouka_rate
        FROM daily_top10_by_growth_rate
        WHERE today_date = (SELECT MAX(today_date) FROM daily_top10_by_growth_rate)
        ORDER BY trend_rank
    """).fetchdf()
    con.close()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("増加数ランキング")
        st.dataframe(df_growth)

        fig_growth = px.bar(
            df_growth,
            x="name",
            y="zouka",
            title="増加数ランキング(グラフ)",
            height=500
        )
        fig_growth.update_xaxes(tickangle=45)
        st.plotly_chart(fig_growth)

    with col2:
        st.subheader("増加率ランキング")
        st.dataframe(df_growth_rate)

        fig_growth_rate = px.bar(
            df_growth_rate,
            x="name",
            y="zouka_rate",
            title="増加率ランキング(グラフ)",
            height=500
        )
        fig_growth_rate.update_xaxes(tickangle=45)
        st.plotly_chart(fig_growth_rate)

elif page == "言語トレンド":
    st.header("言語別トレンド")

    con = get_con()
    df = con.execute("""
        SELECT language, repo_count, total_stars, avg_stars
        FROM language_trends
        ORDER BY total_stars DESC
    """).fetchdf()
    con.close()

    fig = px.bar(
        df,
        x="language",
        y="total_stars",
        color="language",
        title="言語別スター数合計",
        labels={"total_stars": "スター数合計", "language": "言語"}
    )
    st.plotly_chart(fig)

    st.subheader("詳細データ")
    st.dataframe(df)

elif page == "リポジトリ一覧":
    st.header("リポジトリ一覧")

    con = get_con()
    df = con.execute("""
        SELECT name, language, stargazers_count, description, html_url
        FROM stg_repositories
        WHERE fetched_date = (SELECT MAX(fetched_date) FROM stg_repositories)
        ORDER BY stargazers_count DESC
    """).fetchdf()
    con.close()

    language_filter = st.multiselect(
        "言語でフィルタ",
        options=df['language'].unique(),
        default=df['language'].unique()
    )

    filtered_df = df[df['language'].isin(language_filter)]
    st.dataframe(filtered_df)

elif page == "設定":
    st.header("キーワード管理")

    with open("keywords.json", "r") as f:
        keywords = json.load(f)

    st.subheader("登録済みキーワード")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**言語**")
        for lang in keywords["languages"]:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(lang)
            with col_b:
                if st.button("削除", key=f"del_lang_{lang}"):
                    keywords["languages"].remove(lang)
                    with open("keywords.json", "w") as f:
                        json.dump(keywords, f)
                    st.rerun()

    with col2:
        st.write("**技術キーワード**")
        for tech in keywords["techs"]:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(tech)
            with col_b:
                if st.button("削除", key=f"del_tech_{tech}"):
                    keywords["techs"].remove(tech)
                    with open("keywords.json", "w") as f:
                        json.dump(keywords, f)
                    st.rerun()

    st.divider()
    st.subheader("キーワードを追加")

    col3, col4 = st.columns(2)

    with col3:
        new_lang = st.text_input("言語を追加（例：Go、Ruby）")
        if st.button("言語を追加"):
            if new_lang and new_lang not in keywords["languages"]:
                keywords["languages"].append(new_lang)
                with open("keywords.json", "w") as f:
                    json.dump(keywords, f)
                st.success(f"{new_lang}を追加しました")
                st.rerun()

    with col4:
        new_tech = st.text_input("技術キーワードを追加（例：Docker、Kubernetes）")
        if st.button("技術キーワードを追加"):
            if new_tech and new_tech not in keywords["techs"]:
                keywords["techs"].append(new_tech)
                with open("keywords.json", "w") as f:
                    json.dump(keywords, f)
                st.success(f"{new_tech}を追加しました")
                st.rerun()

    st.divider()
    st.subheader("データを更新する")
    st.caption("キーワードを変更したらデータを再取得してください")
if st.button("今すぐデータ取得", type="primary"):
    import subprocess
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    with st.spinner("データ取得中..."):
        subprocess.run(["python", "ingest/fetch.py"], env=env)
    with st.spinner("Transform中..."):
        subprocess.run(["dbt", "run"], cwd="transform/github_trends", env=env)
    st.success("更新完了！")
    st.rerun()