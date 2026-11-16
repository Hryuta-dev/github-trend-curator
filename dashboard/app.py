import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd
import json
import os
import sys

DB_PATH = "github_trends.duckdb"

# グラフの棒の色（.streamlit/config.toml の primaryColor と同じ色）
ACCENT = "#2a78d6"

def get_con():
    return duckdb.connect(DB_PATH)

def style_bar(fig, horizontal=False):
    """棒グラフの見た目を整える（データには触らない）"""
    fig.update_traces(marker_color=ACCENT)
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=20, t=10, b=0),
        bargap=0.35,
    )
    if horizontal:
        # 1位が一番上に来るように並べる
        fig.update_yaxes(autorange="reversed", title=None)
    else:
        fig.update_xaxes(title=None)
    return fig

def show_empty():
    st.info("表示できるデータがまだありません。「設定」ページからデータを取得してください。")

st.set_page_config(
    page_title="GitHub Trend Curator",
    page_icon="📈",
    layout="wide",
)

st.title("GitHub Trend Curator")
st.caption("あなたのキーワードに基づいたGitHubトレンド分析")

# サイドバー
st.sidebar.title("メニュー")
page = st.sidebar.radio("ページ選択", ["トップ", "今日上昇", "言語トレンド", "リポジトリ一覧","設定"])

if page == "トップ":
    st.header("今日のTop10")
    st.caption("スター数が多い順")

    con = get_con()
    df = con.execute("""
        SELECT name, language, stargazers_count, description, html_url
        FROM daily_top10
        WHERE fetched_date = (SELECT MAX(fetched_date) FROM daily_top10)
        ORDER BY rank
    """).fetchdf()
    con.close()

    if df.empty:
        show_empty()

    for position, (_, row) in enumerate(df.iterrows(), start=1):
        language = row['language'] if pd.notna(row['language']) else "言語不明"
        description = row['description'] if pd.notna(row['description']) else "（説明なし）"

        with st.container(border=True):
            col_rank, col_main, col_stars = st.columns([1, 9, 2])
            with col_rank:
                st.subheader(f"{position}")
            with col_main:
                st.markdown(f"**[{row['name']}]({row['html_url']})**")
                st.caption(language)
                st.write(description)
            with col_stars:
                st.metric("スター数", f"{row['stargazers_count']:,}")

elif page == "今日上昇":
    st.header("今日上昇")
    st.caption("前日と比べてスター数が伸びたリポジトリ")

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

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("増加数ランキング")

        if df_growth.empty:
            show_empty()
        else:
            fig_growth = px.bar(
                df_growth,
                x="zouka",
                y="name",
                orientation="h",
                labels={"zouka": "増加数", "name": "リポジトリ", "today_stars": "スター数"},
                hover_data=["today_stars"],
                height=420
            )
            fig_growth.update_traces(texttemplate="%{x:,}", textposition="outside", cliponaxis=False)
            st.plotly_chart(style_bar(fig_growth, horizontal=True), width="stretch")

            st.dataframe(
                df_growth.style.format({"today_stars": "{:,}", "zouka": "{:,}"}, na_rep="-"),
                column_config={
                    "name": "リポジトリ",
                    "today_stars": "スター数",
                    "zouka": "増加数",
                },
                hide_index=True,
                width="stretch",
            )

    with col2:
        st.subheader("増加率ランキング")

        if df_growth_rate.empty:
            show_empty()
        else:
            fig_growth_rate = px.bar(
                df_growth_rate,
                x="zouka_rate",
                y="name",
                orientation="h",
                labels={"zouka_rate": "増加率", "name": "リポジトリ", "today_stars": "スター数"},
                hover_data=["today_stars"],
                height=420
            )
            fig_growth_rate.update_traces(texttemplate="%{x:.2%}", textposition="outside", cliponaxis=False)
            fig_growth_rate.update_xaxes(tickformat=".1%")
            st.plotly_chart(style_bar(fig_growth_rate, horizontal=True), width="stretch")

            st.dataframe(
                df_growth_rate.style.format({"today_stars": "{:,}", "zouka_rate": "{:.2%}"}, na_rep="-"),
                column_config={
                    "name": "リポジトリ",
                    "today_stars": "スター数",
                    "zouka_rate": "増加率",
                },
                hide_index=True,
                width="stretch",
            )

elif page == "言語トレンド":
    st.header("言語別トレンド")
    st.caption("言語ごとのスター数合計")

    con = get_con()
    df = con.execute("""
        SELECT language, repo_count, total_stars, avg_stars
        FROM language_trends
        ORDER BY total_stars DESC
    """).fetchdf()
    con.close()

    if df.empty:
        show_empty()
    else:
        fig = px.bar(
            df,
            x="language",
            y="total_stars",
            labels={
                "total_stars": "スター数合計",
                "language": "言語",
                "repo_count": "リポジトリ数",
            },
            hover_data=["repo_count"],
            height=420
        )
        fig.update_yaxes(tickformat=",")
        st.plotly_chart(style_bar(fig), width="stretch")

        st.subheader("詳細データ")
        st.dataframe(
            df.style.format(
                {"repo_count": "{:,}", "total_stars": "{:,}", "avg_stars": "{:,.0f}"},
                na_rep="-",
            ),
            column_config={
                "language": "言語",
                "repo_count": "リポジトリ数",
                "total_stars": "スター数合計",
                "avg_stars": "平均スター数",
            },
            hide_index=True,
            width="stretch",
        )

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
    st.caption(f"{len(filtered_df):,} 件を表示中（全 {len(df):,} 件）")
    st.dataframe(
        filtered_df.style.format({"stargazers_count": "{:,}"}, na_rep="-"),
        column_config={
            "name": "リポジトリ",
            "language": "言語",
            "stargazers_count": "スター数",
            "description": st.column_config.TextColumn("説明", width="large"),
            "html_url": st.column_config.LinkColumn("GitHub", display_text="開く"),
        },
        hide_index=True,
        width="stretch",
        height=600,
    )

elif page == "設定":
    st.header("キーワード管理")
    st.caption("ここで登録した言語と技術キーワードをもとにリポジトリを取得します")

    with open("keywords.json", "r") as f:
        keywords = json.load(f)

    st.subheader("登録済みキーワード")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        with st.container(border=True):
            st.write("**言語**")
            for lang in keywords["languages"]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(lang)
                with col_b:
                    if st.button("削除", key=f"del_lang_{lang}", width="stretch"):
                        keywords["languages"].remove(lang)
                        with open("keywords.json", "w") as f:
                            json.dump(keywords, f)
                        st.rerun()

    with col2:
        with st.container(border=True):
            st.write("**技術キーワード**")
            for tech in keywords["techs"]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(tech)
                with col_b:
                    if st.button("削除", key=f"del_tech_{tech}", width="stretch"):
                        keywords["techs"].remove(tech)
                        with open("keywords.json", "w") as f:
                            json.dump(keywords, f)
                        st.rerun()

    st.divider()
    st.subheader("キーワードを追加")

    col3, col4 = st.columns(2, gap="large")

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
            subprocess.run([sys.executable, "ingest/fetch.py"], env=env)
        with st.spinner("Transform中..."):
            subprocess.run(["dbt", "run"], cwd="transform/github_trends", env=env)
        st.success("更新完了！")
        st.rerun()
