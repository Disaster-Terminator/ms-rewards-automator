"""
MS Rewards Automator - Dashboard
Focus: Today's task completion status
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="MS Rewards Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=60)
def load_daily_reports():
    report_file = Path("logs/daily_report.json")
    if not report_file.exists():
        return []
    try:
        with open(report_file, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Load failed: {e}")
        return []


def get_today_status(reports):
    today = datetime.now().strftime("%Y-%m-%d")
    target_desktop, target_mobile = 30, 20
    today_desktop, today_mobile, today_points = 0, 0, 0
    initial_points, current_points = 0, 0

    for report in reports:
        if report.get("date") == today:
            session = report.get("session", {})
            state = report.get("state", {})
            today_desktop += session.get("desktop_searches", 0)
            today_mobile += session.get("mobile_searches", 0)
            if initial_points == 0:
                initial_points = state.get("initial_points", 0)
            current_points = state.get("current_points", 0)

    if current_points > 0 and initial_points > 0:
        today_points = current_points - initial_points

    return {
        "desktop": today_desktop,
        "mobile": today_mobile,
        "total": today_desktop + today_mobile,
        "points": today_points,
        "target_desktop": target_desktop,
        "target_mobile": target_mobile,
        "target_total": target_desktop + target_mobile,
        "desktop_complete": today_desktop >= target_desktop,
        "mobile_complete": today_mobile >= target_mobile,
        "all_complete": today_desktop >= target_desktop and today_mobile >= target_mobile,
        "current_points": current_points,
    }


def parse_reports_to_dataframe(reports):
    daily_data = {}
    for report in reports:
        date = report.get("date", "")
        state = report.get("state", {})
        session = report.get("session", {})

        if date not in daily_data:
            daily_data[date] = {
                "Date": date,
                "Initial": state.get("initial_points", 0),
                "Current": state.get("current_points", 0),
                "Gained": 0,
                "Desktop": 0,
                "Mobile": 0,
                "Alerts": 0,
            }

        daily_data[date]["Desktop"] += session.get("desktop_searches", 0)
        daily_data[date]["Mobile"] += session.get("mobile_searches", 0)
        daily_data[date]["Alerts"] += len(session.get("alerts", []))

        current = state.get("current_points", 0)
        if current > 0:
            daily_data[date]["Current"] = current
            daily_data[date]["Gained"] = current - daily_data[date]["Initial"]

    data = []
    for date_key in sorted(daily_data.keys()):
        day = daily_data[date_key]
        day["Total"] = day["Desktop"] + day["Mobile"]
        day["Complete"] = day["Desktop"] >= 30 and day["Mobile"] >= 20
        data.append(day)

    return pd.DataFrame(data)


def main():
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.title("🎯 MS Rewards Dashboard")
    with col_refresh:
        st.write("")
        if st.button("🔄 刷新", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    reports = load_daily_reports()
    if not reports:
        st.warning("📭 暂无数据，请先运行主程序")
        st.code("python main.py", language="bash")
        return

    today = get_today_status(reports)

    # 今日任务状态
    if today["all_complete"]:
        st.success("### ✅ 今日任务已完成")
    else:
        st.warning("### ⚠️ 今日任务未完成")

    st.markdown("#### 📋 今日进度")

    col1, col2, col3 = st.columns(3)

    with col1:
        status = "✅" if today["desktop_complete"] else "⚠️"
        color = "normal" if today["desktop_complete"] else "inverse"
        delta = (
            "已完成"
            if today["desktop_complete"]
            else f"还差 {today['target_desktop'] - today['desktop']} 次"
        )
        st.metric(
            label=f"{status} 桌面搜索",
            value=f"{today['desktop']}/{today['target_desktop']}",
            delta=delta,
            delta_color=color,
        )

    with col2:
        status = "✅" if today["mobile_complete"] else "⚠️"
        color = "normal" if today["mobile_complete"] else "inverse"
        delta = (
            "已完成"
            if today["mobile_complete"]
            else f"还差 {today['target_mobile'] - today['mobile']} 次"
        )
        st.metric(
            label=f"{status} 移动搜索",
            value=f"{today['mobile']}/{today['target_mobile']}",
            delta=delta,
            delta_color=color,
        )

    with col3:
        st.metric(
            label="💰 今日积分",
            value=f"+{today['points']}",
            delta=f"总积分: {today['current_points']:,}" if today["current_points"] > 0 else None,
        )

    # 操作建议
    if not today["all_complete"]:
        st.markdown("---")
        st.info("💡 **建议操作**：运行以下命令补充搜索")

        if not today["desktop_complete"] and not today["mobile_complete"]:
            st.code("python main.py", language="bash")
        elif not today["desktop_complete"]:
            st.code("python main.py --mobile-only", language="bash")
        else:
            st.code("python main.py --desktop-only", language="bash")

    st.markdown("---")

    # 历史数据
    df = parse_reports_to_dataframe(reports)
    st.markdown("### 📊 历史数据")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📅 运行天数", f"{len(df)}")

    with col2:
        completed = df["Complete"].sum()
        rate = completed / len(df) * 100 if len(df) > 0 else 0
        st.metric("✅ 完成天数", f"{completed}/{len(df)}", delta=f"{rate:.0f}%")

    with col3:
        st.metric("🔍 总搜索次数", f"{df['Total'].sum()}")

    with col4:
        st.metric("💎 累计积分", f"+{df['Gained'].sum()}")

    # 详细数据
    with st.expander("📋 查看详细数据", expanded=False):
        display = df.copy()
        display["状态"] = display["Complete"].apply(lambda x: "✅ 已完成" if x else "⚠️ 未完成")
        display = display[["Date", "状态", "Desktop", "Mobile", "Total", "Gained", "Alerts"]]
        display.columns = ["日期", "状态", "桌面搜索", "移动搜索", "总搜索", "获得积分", "告警数"]
        st.dataframe(display.sort_values("日期", ascending=False), width="stretch", hide_index=True)

    # 图表
    with st.expander("📈 查看趋势图表", expanded=False):
        tab1, tab2 = st.tabs(["搜索趋势", "积分趋势"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(x=df["Date"], y=df["Desktop"], name="桌面搜索", marker_color="#ff7f0e")
            )
            fig.add_trace(
                go.Bar(x=df["Date"], y=df["Mobile"], name="移动搜索", marker_color="#9467bd")
            )
            fig.add_hline(y=50, line_dash="dash", line_color="green", annotation_text="目标: 50次")
            fig.update_layout(barmode="stack", yaxis_title="搜索次数", height=400)
            st.plotly_chart(fig, width="stretch")

        with tab2:
            fig = go.Figure()
            fig.add_trace(
                go.Bar(x=df["Date"], y=df["Gained"], name="每日获得", marker_color="#2ca02c")
            )
            fig.update_layout(yaxis_title="积分", height=400)
            st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
