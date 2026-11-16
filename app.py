from __future__ import annotations

import os
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
UNKNOWN_ANSWER = "I cannot verify that from the current Degree OS data."
STATUS_ORDER = ["Not Started", "In Progress", "Completed"]
PLAN_STATUS_ORDER = ["Not Started", "In Progress", "Done"]

DATA_FILES = {
    "Semesters": "semesters.csv",
    "Courses": "courses.csv",
    "Academic Calendar": "academic_calendar.csv",
    "Assessments": "assessments.csv",
    "Scores": "scores.csv",
    "Plan & Checklist": "plan_checklist.csv",
    "Programme Info": "program_info.csv",
}

st.set_page_config(
    page_title="My Engineering Degree OS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root {
        --ink: #f3f5f4;
        --muted: #a4afaa;
        --green: #59c49c;
        --green-light: #12362a;
        --amber: #f5b547;
        --amber-light: #3a2a12;
        --red: #ff7777;
        --red-light: #3a1717;
        --blue: #82aaff;
        --blue-light: #17263f;
        --line: #292d2b;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #000000; color: var(--ink); }
    h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: -0.03em; }
    h1 { font-size: 1.95rem !important; margin-bottom: 0.2rem !important; }
    [data-testid="stSidebar"] { background: #050505; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { font-size: 1.15rem !important; }
    [data-testid="stMetric"] { background: #0c0c0c; border: 1px solid var(--line); padding: 14px 18px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
    [data-testid="stMetricLabel"] { color: var(--muted); font-size: 0.85rem !important; font-weight: 500; }
    [data-testid="stMetricValue"] { font-family: 'Manrope', sans-serif; font-size: 1.45rem !important; font-weight: 700; }
    .eyebrow { color: var(--green); font-size: .75rem; text-transform: uppercase; letter-spacing: .12em; font-weight: 700; margin-bottom: 4px; }
    .subtle { color: var(--muted); font-size: 0.95rem; margin-top: -4px; margin-bottom: 18px; }
    .semester-card {
        min-height: 145px;
        background: #0c0c0c;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.25);
        color: var(--ink);
    }
    .semester-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .semester-card strong { font-family: 'Manrope', sans-serif; font-size: 1.05rem; }
    .semester-card p { margin: 6px 0 2px; color: var(--muted); font-size: .86rem; }
    .status-pill { display: inline-block; border-radius: 20px; padding: 3px 10px; font-size: .72rem; background: var(--green-light); color: var(--green); font-weight: 600; }
    .status-pill-amber { display: inline-block; border-radius: 20px; padding: 3px 10px; font-size: .72rem; background: var(--amber-light); color: var(--amber); font-weight: 600; }
    .status-pill-blue { display: inline-block; border-radius: 20px; padding: 3px 10px; font-size: .72rem; background: var(--blue-light); color: var(--blue); font-weight: 600; }
    .status-pill-neutral { display: inline-block; border-radius: 20px; padding: 3px 10px; font-size: .72rem; background: #202321; color: var(--muted); font-weight: 600; }
    .info-card { background: #0c0c0c; border: 1px solid var(--line); border-radius: 12px; padding: 18px; margin-bottom: 16px; }
    .prompt-chip { display: inline-block; background: #10251c; border: 1px solid #294c3c; border-radius: 16px; padding: 5px 12px; font-size: 0.8rem; margin: 3px; color: #a6e8cb; cursor: pointer; }
    [data-testid="stDataFrame"], [data-testid="stTable"] { background: #0c0c0c; }
    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
        background: #111111;
        color: var(--ink);
        border-color: var(--line);
    }
    input, textarea { color: var(--ink) !important; }
    [data-testid="stChatMessage"] { background: #0c0c0c; }
    [data-testid="stAlert"] { background: #101210; }
    div.stButton > button[kind="primary"] { background: var(--green); border-color: var(--green); }
    div.stButton > button[kind="primary"] { color: #06140e; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def save_csv(filename: str, data: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    data.to_csv(DATA_DIR / filename, index=False)
    load_csv.clear()


def parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def show_data_warning(name: str, data: pd.DataFrame) -> bool:
    if data.empty:
        st.warning(f"⚠️ {name} data is missing or empty. Add rows in Data Admin or create data/{DATA_FILES.get(name, filename)}.")
        return True
    return False


def heading(title: str, description: str) -> None:
    st.markdown("<div class='eyebrow'>Degree Command Center</div>", unsafe_allow_html=True)
    st.title(title)
    st.markdown(f"<p class='subtle'>{description}</p>", unsafe_allow_html=True)


def current_semester(semesters_df: pd.DataFrame) -> int | None:
    if semesters_df.empty or "status" not in semesters_df:
        return None
    active = semesters_df[semesters_df["status"].astype(str).str.strip().str.lower() == "in progress"]
    if active.empty:
        return None
    return int(active.iloc[0]["semester"])


def upcoming_rows(data: pd.DataFrame, date_column: str, today: date | None = None) -> pd.DataFrame:
    if data.empty or date_column not in data:
        return pd.DataFrame()
    today = today or date.today()
    dated = data.copy()
    dated["_date"] = parse_dates(dated[date_column])
    return dated[dated["_date"].notna() & (dated["_date"] >= today)].sort_values("_date")


def format_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    return parsed.strftime("%b %d, %Y") if not pd.isna(parsed) else "Date not set"


# Load all CSV tables
semesters = load_csv("semesters.csv")
courses = load_csv("courses.csv")
calendar = load_csv("academic_calendar.csv")
assessments = load_csv("assessments.csv")
scores = load_csv("scores.csv")
plan = load_csv("plan_checklist.csv")
program_info = load_csv("program_info.csv")

curr_sem = current_semester(semesters)

with st.sidebar:
    st.markdown("## 🎓 Degree OS")
    st.caption("Personal Engineering Command Center")
    if curr_sem is not None:
        st.markdown(f"<span class='status-pill'>Semester {curr_sem} In Progress</span>", unsafe_allow_html=True)
    st.divider()
    page = st.radio(
        "Workspace Navigation",
        [
            "Dashboard",
            "Semesters 1-8",
            "Courses & Syllabus",
            "University Syllabus",
            "Academic Calendar",
            "Internal Assessments",
            "Status Tracker",
            "Scorecard",
            "Plan & Checklist",
            "Ask Degree AI",
            "Data Admin",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("📌 Built with Streamlit & Pandas. Maintained via local CSV files.")


# -----------------------------------------------------------------------------
# 1. Dashboard
# -----------------------------------------------------------------------------
if page == "Dashboard":
    heading("Your Degree, at a Glance", "High-level summary of 8-semester progress, upcoming dates, and immediate priorities.")

    total_credits = pd.to_numeric(semesters.get("total_credits", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    completed_credits = pd.to_numeric(semesters.get("completed_credits", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    completion = (completed_credits / total_credits * 100) if total_credits else 0

    progress_cols = st.columns(4)
    progress_cols[0].metric("Current Semester", f"Semester {curr_sem}" if curr_sem else "Not Set")
    progress_cols[1].metric("Degree Progress", f"{completion:.1f}%")
    progress_cols[2].metric("Credits Completed", f"{completed_credits:g} / {total_credits:g}")

    if not scores.empty and {"score", "max_marks"}.issubset(scores.columns):
        score_total = pd.to_numeric(scores["score"], errors="coerce").sum()
        max_total = pd.to_numeric(scores["max_marks"], errors="coerce").sum()
        score_percentage = (score_total / max_total * 100) if max_total else 0
        progress_cols[3].metric("Prototype Score %", f"{score_percentage:.1f}%", help="Simple weighted score average. Not an official university CGPA.")
    else:
        progress_cols[3].metric("Prototype Score %", "—")

    st.markdown("")
    left, right = st.columns([1.3, 1])

    with left:
        st.subheader("Semester Progress Breakdown")
        if not show_data_warning("Semesters", semesters):
            chart_data = semesters.copy()
            total = pd.to_numeric(chart_data["total_credits"], errors="coerce")
            completed = pd.to_numeric(chart_data["completed_credits"], errors="coerce").fillna(0)
            chart_data["progress"] = (completed.div(total.where(total.ne(0))) * 100).fillna(0)
            chart_data["label"] = chart_data["semester"].map(lambda value: f"Sem {value}")
            st.bar_chart(chart_data.set_index("label")["progress"], height=270)
            st.caption("Completion percentage per semester calculated from completed credits.")

    with right:
        st.subheader("Upcoming Academic Schedule")
        next_assessment = upcoming_rows(assessments, "date")
        next_event = upcoming_rows(calendar, "date")

        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        if not next_assessment.empty:
            item = next_assessment.iloc[0]
            st.markdown(f"**Next Assessment · {format_date(item['_date'])}**")
            st.write(f"📝 {item.get('assessment_type', 'Assessment')} — {item.get('course_code', '')}")
            st.caption(f"Status: {item.get('status', 'Planned')} · Max Marks: {item.get('max_marks', '—')}")
        else:
            st.info("No upcoming assessments found in the schedule.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        holidays = next_event[
            next_event.get("event_type", pd.Series(index=next_event.index, dtype=str))
            .astype(str).str.contains("holiday|leave", case=False, na=False)
        ]
        if not holidays.empty:
            item = holidays.iloc[0]
            st.markdown(f"**Next Holiday / Leave · {format_date(item['_date'])}**")
            st.write(f"🏖️ {item.get('title', 'Calendar event')} ({item.get('event_type', 'Holiday')})")
        else:
            st.info("No upcoming holidays or leaves in the schedule.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    st.subheader("Quick Attention")
    incomplete_courses = 0
    if not courses.empty and "status" in courses:
        incomplete_courses = int((~courses["status"].astype(str).str.lower().eq("completed")).sum())
    
    pending_tasks = int((plan.get("status", pd.Series(dtype=str)).astype(str).str.lower() != "done").sum()) if not plan.empty else 0
    
    c1, c2 = st.columns(2)
    c1.info(f"📚 **{incomplete_courses} courses** across the degree are currently pending or in progress.")
    c2.info(f"⚡ **{pending_tasks} checklist items** require attention in your degree action plan.")


# -----------------------------------------------------------------------------
# 2. Semesters 1-8
# -----------------------------------------------------------------------------
elif page == "Semesters 1-8":
    heading("Semesters 1 to 8 Journey", "Visual cards for all 8 semesters with course count, credits, completion status, and course details.")
    
    if not show_data_warning("Semesters", semesters):
        cards = semesters.sort_values("semester").reset_index(drop=True)
        
        # Display 8 semester cards in 2 rows of 4 columns
        for start in range(0, len(cards), 4):
            cols = st.columns(4)
            for col, (_, row) in zip(cols, cards.iloc[start:start + 4].iterrows()):
                sem_num = int(row["semester"])
                total = float(row.get("total_credits", 0) or 0)
                completed = float(row.get("completed_credits", 0) or 0)
                ratio = completed / total if total else 0
                status = str(row.get("status", "Not Started")).strip()
                
                # Count courses for this semester
                sem_courses = courses[courses["semester"].astype(int) == sem_num] if not courses.empty and "semester" in courses else pd.DataFrame()
                course_count = len(sem_courses)
                
                pill_class = "status-pill" if status.lower() == "completed" else "status-pill-amber" if status.lower() == "in progress" else "status-pill-neutral"
                
                with col:
                    st.markdown(
                        f"""
                        <div class="semester-card">
                            <div class="semester-card-header">
                                <strong>Semester {sem_num}</strong>
                                <span class="{pill_class}">{status}</span>
                            </div>
                            <p>📖 <b>{course_count}</b> courses</p>
                            <p>🎯 <b>{completed:g}</b> of <b>{total:g}</b> credits</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.progress(min(max(ratio, 0.0), 1.0))
                    st.caption(f"{ratio*100:.0f}% credits completed")

        st.divider()
        st.subheader("Filter Semester Course Details")
        sem_list = sorted(semesters["semester"].astype(int).unique())
        chosen_sem = st.selectbox("Select Semester to View Courses", sem_list, index=sem_list.index(curr_sem) if curr_sem in sem_list else 0, key="semester_cards_filter")
        
        selected_courses = courses[courses["semester"].astype(int) == int(chosen_sem)] if not courses.empty else pd.DataFrame()
        st.markdown(f"#### Semester {chosen_sem} Registered Courses ({len(selected_courses)} courses)")
        if selected_courses.empty:
            st.info(f"No courses registered for Semester {chosen_sem} yet.")
        else:
            display_cols = [c for c in ["course_code", "course_name", "credits", "faculty", "syllabus", "status"] if c in selected_courses.columns]
            st.dataframe(selected_courses[display_cols], use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 3. Courses & Syllabus
# -----------------------------------------------------------------------------
elif page == "Courses & Syllabus":
    heading("Courses & Syllabus Catalog", "Explore course codes, credits, faculty in-charge, status, and detailed syllabus topics.")
    
    if not show_data_warning("Courses", courses):
        col_filter1, col_filter2 = st.columns([1, 2])
        course_semesters = sorted(courses["semester"].astype(int).unique())
        
        with col_filter1:
            chosen = st.selectbox("Filter by Semester", course_semesters, index=course_semesters.index(curr_sem) if curr_sem in course_semesters else 0)
        with col_filter2:
            search_query = st.text_input("Search Course Code, Name, or Topic", placeholder="e.g. Data Structures, CS301, calculus...")
            
        selected = courses[courses["semester"].astype(int) == int(chosen)].copy()
        
        if search_query.strip():
            sq = search_query.strip().lower()
            selected = selected[
                selected["course_name"].astype(str).str.lower().str.contains(sq)
                | selected["course_code"].astype(str).str.lower().str.contains(sq)
                | selected["syllabus"].astype(str).str.lower().str.contains(sq)
            ]
            
        if "syllabus" in selected:
            selected["topics"] = selected["syllabus"].astype(str).str.split(";").apply(
                lambda topics: ", ".join(t.strip() for t in topics if t.strip())
            )
            
        display_columns = [c for c in ["course_code", "course_name", "credits", "faculty", "topics", "status"] if c in selected]
        st.dataframe(selected[display_columns], use_container_width=True, hide_index=True)
        
        st.markdown(f"Showing **{len(selected)}** course(s) for Semester **{chosen}**.")


# -----------------------------------------------------------------------------
# 4. University Syllabus
# -----------------------------------------------------------------------------
elif page == "University Syllabus":
    heading("University Programme Syllabus", "Official programme summary, graduation credit structure, and verified curriculum reference.")
    
    if not show_data_warning("Programme Info", program_info):
        for _, row in program_info.iterrows():
            st.subheader(str(row.get("programme_name", "Degree Programme Overview")))
            st.write(row.get("overview", ""))
            
            m1, m2 = st.columns(2)
            m1.metric("Total Semesters", row.get("total_semesters", "8"))
            m2.metric("Total Degree Credits Required", row.get("expected_credits", "128"))
            
            st.markdown("<div class='info-card'>", unsafe_allow_html=True)
            source = str(row.get("source_reference", "")).strip()
            st.markdown(f"**Official Syllabus Source / Reference:**\n\n`{source if source else 'Not provided'}`")
            st.caption("🔒 Grounding Guardrail: No university regulations, attendance cutoffs, or GPA formulas are assumed beyond the explicit source loaded.")
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.info("💡 Academic coordinators can update programme details in the **Data Admin** tab.")


# -----------------------------------------------------------------------------
# 5. Academic / Leave Calendar
# -----------------------------------------------------------------------------
elif page == "Academic Calendar":
    heading("Academic & Leave Calendar", "Filter schedule milestones, holidays, teaching days, and examinations by year and semester.")
    
    if not show_data_warning("Academic Calendar", calendar):
        c1, c2, c3 = st.columns(3)
        with c1:
            years = ["All Academic Years"] + sorted(calendar["academic_year"].dropna().astype(str).unique().tolist())
            years_selected = st.selectbox("Academic Year", years)
        with c2:
            sem_values = ["All Semesters"] + sorted(calendar["semester"].dropna().astype(int).unique().tolist())
            sem_selected = st.selectbox("Semester", sem_values)
        with c3:
            event_types = ["All Event Types"] + sorted(calendar["event_type"].dropna().astype(str).unique().tolist())
            type_selected = st.selectbox("Event Type", event_types)
            
        filtered = calendar.copy()
        if years_selected != "All Academic Years":
            filtered = filtered[filtered["academic_year"].astype(str) == years_selected]
        if sem_selected != "All Semesters":
            filtered = filtered[filtered["semester"].astype(int) == int(sem_selected)]
        if type_selected != "All Event Types":
            filtered = filtered[filtered["event_type"].astype(str) == type_selected]
            
        filtered["_date"] = pd.to_datetime(filtered["date"], errors="coerce")
        filtered = filtered.sort_values("_date")
        
        # Add visual badges for event types
        def format_event_type(t: str) -> str:
            t_str = str(t).lower()
            if "holiday" in t_str:
                return "🏖️ Holiday"
            elif "leave" in t_str:
                return "🌴 Leave"
            elif "exam" in t_str:
                return "📝 Examination"
            return "📖 Academic"
            
        view_table = filtered.copy()
        view_table["Event Category"] = view_table["event_type"].apply(format_event_type)
        
        display_cols = [c for c in ["academic_year", "semester", "date", "Event Category", "title"] if c in view_table.columns]
        st.dataframe(view_table[display_cols], use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(view_table)} calendar events matching your filter.")


# -----------------------------------------------------------------------------
# 6. Internal Assessments
# -----------------------------------------------------------------------------
elif page == "Internal Assessments":
    heading("Internal Assessments & Evaluations", "Keep track of IA1, IA2, assignments, lab evaluations, project reviews, and end-semester exams.")
    
    if not show_data_warning("Assessments", assessments):
        c1, c2 = st.columns(2)
        with c1:
            sems = ["All Semesters"] + sorted(assessments["semester"].dropna().astype(int).unique().tolist())
            chosen_sem = st.selectbox("Filter Semester", sems, index=sems.index(curr_sem) if curr_sem in sems else 0)
        with c2:
            types = ["All Types"] + sorted(assessments["assessment_type"].dropna().astype(str).unique().tolist())
            chosen_type = st.selectbox("Filter Assessment Type", types)
            
        filtered = assessments.copy()
        if chosen_sem != "All Semesters":
            filtered = filtered[filtered["semester"].astype(int) == int(chosen_sem)]
        if chosen_type != "All Types":
            filtered = filtered[filtered["assessment_type"].astype(str) == chosen_type]
            
        filtered["_sort_date"] = pd.to_datetime(filtered["date"], errors="coerce")
        filtered = filtered.sort_values("_sort_date").drop(columns="_sort_date")
        
        # Merge course name if available
        if not courses.empty and "course_code" in courses:
            course_map = dict(zip(courses["course_code"], courses["course_name"]))
            filtered["course_name"] = filtered["course_code"].map(course_map).fillna("")
            cols = ["semester", "course_code", "course_name", "assessment_type", "date", "max_marks", "status"]
            cols = [c for c in cols if c in filtered.columns]
            st.dataframe(filtered[cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(filtered, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 7. Status Tracker
# -----------------------------------------------------------------------------
elif page == "Status Tracker":
    heading("Academic Status Tracker", "Course-by-course completion tracker with status breakdown and progress bars.")
    
    if not show_data_warning("Courses", courses):
        col1, col2 = st.columns([1, 2])
        with col1:
            chosen = st.selectbox("Select Semester", sorted(courses["semester"].astype(int).unique()), key="status_semester", index=sorted(courses["semester"].astype(int).unique()).index(curr_sem) if curr_sem in courses["semester"].astype(int).unique() else 0)
            
        selected = courses[courses["semester"].astype(int) == int(chosen)]
        counts = selected["status"].value_counts()
        
        metrics = st.columns(3)
        for col, status in zip(metrics, STATUS_ORDER):
            col.metric(status, int(counts.get(status, 0)))
            
        completed_count = int(counts.get("Completed", 0))
        prog_ratio = completed_count / len(selected) if len(selected) else 0
        st.progress(prog_ratio)
        st.caption(f"**{completed_count} of {len(selected)} courses** ({prog_ratio*100:.0f}%) completed in Semester {chosen}.")
        
        st.subheader(f"Courses in Semester {chosen}")
        display_cols = [c for c in ["course_code", "course_name", "credits", "faculty", "status"] if c in selected.columns]
        st.dataframe(selected[display_cols], use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Degree-Wide Course Completion Overview")
        overall_counts = courses["status"].value_counts()
        oc1, oc2, oc3 = st.columns(3)
        oc1.metric("Total Completed Courses", int(overall_counts.get("Completed", 0)))
        oc2.metric("In Progress Courses", int(overall_counts.get("In Progress", 0)))
        oc3.metric("Not Started Courses", int(overall_counts.get("Not Started", 0)))


# -----------------------------------------------------------------------------
# 8. Scorecard
# -----------------------------------------------------------------------------
elif page == "Scorecard":
    heading("Student Scorecard & Performance", "Marks, grades, evaluated credits, semester averages, and cumulative progress.")
    
    if not show_data_warning("Scores", scores):
        scores_view = scores.copy()
        scores_view["score"] = pd.to_numeric(scores_view["score"], errors="coerce")
        scores_view["max_marks"] = pd.to_numeric(scores_view["max_marks"], errors="coerce")
        
        total_score = scores_view["score"].sum()
        total_max = scores_view["max_marks"].sum()
        percentage = (total_score / total_max * 100) if total_max else 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Prototype Score Percentage", f"{percentage:.1f}%")
        m2.metric("Total Marks Scored", f"{total_score:g} / {total_max:g}")
        m3.metric("Assessments Scored", len(scores_view.dropna(subset=["score"])))
        
        st.caption("ℹ️ Note: This is an aggregate prototype score percentage based on loaded assessment records. It is not an official university CGPA.")
        
        # Merge course credits if available
        if not courses.empty and {"course_code", "credits"}.issubset(courses.columns):
            credit_map = dict(zip(courses["course_code"], courses["credits"]))
            scores_view["credits"] = scores_view["course_code"].map(credit_map).fillna(4)
        
        st.divider()
        st.subheader("Semester-Wise Performance & Cumulative Progress")
        
        summary = (
            scores_view.groupby("semester", as_index=False)
            .agg(score=("score", "sum"), max_marks=("max_marks", "sum"))
            .sort_values("semester")
        )
        summary["semester_percentage"] = (summary["score"] / summary["max_marks"] * 100).round(1)
        summary["cumulative_score"] = summary["score"].cumsum()
        summary["cumulative_max"] = summary["max_marks"].cumsum()
        summary["cumulative_progress_pct"] = (summary["cumulative_score"] / summary["cumulative_max"] * 100).round(1)
        
        summary_display = summary.rename(columns={
            "semester": "Semester",
            "score": "Sem Scored",
            "max_marks": "Sem Max",
            "semester_percentage": "Sem Average %",
            "cumulative_score": "Cumul Scored",
            "cumulative_max": "Cumul Max",
            "cumulative_progress_pct": "Cumulative Progress %",
        })
        st.dataframe(summary_display, use_container_width=True, hide_index=True)
        
        st.subheader("Detailed Assessment Score Records")
        display_score_cols = [c for c in ["semester", "course_code", "assessment_type", "score", "max_marks", "grade", "credits"] if c in scores_view.columns]
        st.dataframe(scores_view[display_score_cols], use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# 9. Plan & Checklist
# -----------------------------------------------------------------------------
elif page == "Plan & Checklist":
    heading("Plan & Degree Execution Control Panel", "Execution control panel organizing weekly targets, semester milestones, and long-range degree checkpoints.")
    
    if not show_data_warning("Plan & Checklist", plan):
        today = date.today()
        
        # Calculate Health metrics dynamically
        working_plan = plan.copy()
        working_plan["_date"] = pd.to_datetime(working_plan["target_date"], errors="coerce").dt.date
        
        done_count = int(working_plan["status"].astype(str).str.lower().eq("done").sum())
        due_soon_count = int(
            ((working_plan["_date"] >= today) & (working_plan["_date"] <= today + timedelta(days=7))
             & ~working_plan["status"].astype(str).str.lower().eq("done")).sum()
        )
        overdue_count = int(
            ((working_plan["_date"] < today) & working_plan["_date"].notna()
             & ~working_plan["status"].astype(str).str.lower().eq("done")).sum()
        )
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Checklist Items", len(working_plan))
        m2.metric("Done", done_count)
        m3.metric("Due in 7 Days", due_soon_count)
        m4.metric("Overdue", overdue_count)
        
        # Compute health indicator
        working_plan["health"] = working_plan.apply(
            lambda row: "Done" if str(row["status"]).strip().lower() == "done"
            else "Overdue" if pd.notna(row["_date"]) and row["_date"] < today
            else "Due Soon" if pd.notna(row["_date"]) and row["_date"] <= today + timedelta(days=7)
            else "On Track",
            axis=1,
        )
        
        # Section 1: This Week
        st.markdown("### 📅 This Week (Next 7 Days)")
        this_week = working_plan[
            (working_plan["_date"] >= today)
            & (working_plan["_date"] <= today + timedelta(days=7))
            & ~working_plan["status"].astype(str).str.lower().eq("done")
        ]
        if this_week.empty:
            st.info("🎉 No pending tasks due in the next 7 days.")
        else:
            st.dataframe(this_week[["category", "item", "target_date", "status", "health", "notes"]], use_container_width=True, hide_index=True)
            
        # Section 2 & 3: Semester & Degree Milestones
        tab_sem, tab_deg = st.tabs(["🎯 Semester Milestones", "🚀 Degree Milestones"])
        
        with tab_sem:
            st.caption("Major academic outcomes for the active semester (exams, lab submissions, mini-projects).")
            sem_items = working_plan[
                working_plan["category"].isin(["Semester Preparation", "Assessments", "Labs", "Projects"])
            ]
            st.dataframe(sem_items[["category", "item", "target_date", "status", "health", "notes"]], use_container_width=True, hide_index=True)
            
        with tab_deg:
            st.caption("Long-range checkpoints (internship applications, placement readiness, capstone, documents).")
            deg_items = working_plan[
                working_plan["category"].isin(["Internship/Placement", "Skills", "Documents"])
            ]
            st.dataframe(deg_items[["category", "item", "target_date", "status", "health", "notes"]], use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("✏️ Editable Execution Checklist")
        st.caption("Edit item status, dates, or notes below and click 'Save Checklist' to persist updates.")
        
        editable_view = plan.copy()
        editable_view["target_date"] = pd.to_datetime(editable_view["target_date"], errors="coerce").dt.date
        
        edited = st.data_editor(
            editable_view,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=["Semester Preparation", "Assessments", "Labs", "Projects", "Documents", "Skills", "Internship/Placement"],
                    required=True,
                ),
                "status": st.column_config.SelectboxColumn("Status", options=PLAN_STATUS_ORDER, required=True),
                "target_date": st.column_config.DateColumn("Target Date", format="YYYY-MM-DD"),
                "item": st.column_config.TextColumn("Action Item", required=True),
                "notes": st.column_config.TextColumn("Notes"),
            },
            key="plan_editor",
        )
        
        if st.button("Save Checklist Updates", type="primary"):
            save_csv("plan_checklist.csv", edited)
            st.success("✅ Saved updates to data/plan_checklist.csv.")
            st.rerun()


# -----------------------------------------------------------------------------
# 10. Ask Degree AI
# -----------------------------------------------------------------------------
elif page == "Ask Degree AI":
    heading("Ask Degree AI Assistant", "Grounded degree intelligence answering queries strictly using your Degree OS data.")
    st.caption("Try the suggested questions below or enter your own query.")
    
    # Clickable prompt chips
    sample_queries = [
        "What courses are still incomplete in Semester 3?",
        "When is my next internal assessment?",
        "Show my next holiday",
        "What topics are in Data Structures?",
        "What is my official university CGPA formula?",
        "What subjects are left in Sem 5?",
    ]
    
    cols = st.columns(len(sample_queries))
    selected_chip = None
    for idx, (col, q_text) in enumerate(zip(cols, sample_queries)):
        if col.button(q_text, key=f"chip_{idx}"):
            selected_chip = q_text

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("area"):
                st.caption(f"📁 Data area used: **{message['area']}**")

    def local_answer(question: str) -> tuple[str, str]:
        query = question.lower()
        
        # 1. Unverified policy or formula question -> Strict Safe Refusal
        if any(term in query for term in ["cgpa", "gpa formula", "cgpa formula", "official formula", "exam regulation", "eligibility rule", "attendance rule"]):
            if not program_info.empty and "official_formula" in program_info:
                formula = program_info["official_formula"].dropna().astype(str)
                formula = formula[formula.str.strip().ne("")]
                if not formula.empty:
                    return formula.iloc[0], "Scores"
            return UNKNOWN_ANSWER, "Scores"

        # 2. Incomplete courses / subjects left
        semester_match = re.search(r"semester\s*(\d+)|sem\s*(\d+)", query)
        requested_semester = int(next(v for v in semester_match.groups() if v)) if semester_match else curr_sem
        
        is_course_query = any(term in query for term in [
            "incomplete", "still left", "courses left", "subjects left", "subjects are left", 
            "not completed", "pending courses", "remaining courses", "courses pending"
        ]) or (("subject" in query or "course" in query) and ("left" in query or "pending" in query or "remaining" in query))
        
        if is_course_query:
            if courses.empty or requested_semester is None:
                return UNKNOWN_ANSWER, "Courses"
            rows = courses[
                (courses["semester"].astype(int) == requested_semester)
                & ~courses["status"].astype(str).str.lower().eq("completed")
            ]
            names = [f"{row['course_name']} ({row['course_code']})" for _, row in rows.iterrows()]
            if names:
                return f"Incomplete courses in Semester {requested_semester}: {', '.join(names)}.", "Courses"
            return f"All recorded courses for Semester {requested_semester} are marked Completed.", "Courses"

        # 3. Next assessment / internal assessment (IA)
        if any(term in query for term in ["next ia", "next assessment", "upcoming assessment", "internal assessment", "when is my next"]):
            upcoming = upcoming_rows(assessments, "date")
            if upcoming.empty:
                return "There are no upcoming assessments recorded in the schedule.", "Assessments"
            
            # If asking specifically for IA
            if "ia" in query and not "assignment" in query:
                ia_rows = upcoming[upcoming["assessment_type"].astype(str).str.contains("ia", case=False, na=False)]
                if not ia_rows.empty:
                    row = ia_rows.iloc[0]
                    return f"Your next internal assessment test is {row.get('assessment_type', 'IA')} for {row.get('course_code', '')} scheduled on {format_date(row['_date'])}.", "Assessments"
                    
            row = upcoming.iloc[0]
            next_ia = upcoming[upcoming["assessment_type"].astype(str).str.contains("ia", case=False, na=False)]
            ia_note = f" (Next IA test is {next_ia.iloc[0].get('assessment_type')} on {format_date(next_ia.iloc[0]['_date'])})" if not next_ia.empty and next_ia.iloc[0]["_date"] != row["_date"] else ""
            return f"Your next scheduled assessment is {row.get('assessment_type', 'Assessment')} for {row.get('course_code', '')} on {format_date(row['_date'])}{ia_note}.", "Assessments"

        # 4. Next holiday / leave
        if any(term in query for term in ["holiday", "leave", "vacation", "off"]):
            upcoming = upcoming_rows(calendar, "date")
            if not upcoming.empty:
                upcoming = upcoming[upcoming["event_type"].astype(str).str.contains("holiday|leave", case=False, na=False)]
            if upcoming.empty:
                return "There are no upcoming holidays or leaves recorded in the calendar.", "Calendar"
            row = upcoming.iloc[0]
            return f"Your next holiday / leave is {row.get('title', 'Holiday')} on {format_date(row['_date'])} ({row.get('event_type')}).", "Calendar"

        # 5. Course syllabus / topics
        if any(term in query for term in ["topic", "syllabus", "content", "curriculum", "unit"]):
            if courses.empty:
                return UNKNOWN_ANSWER, "Courses"
            # Extract possible keywords
            words = [w for w in re.findall(r"[a-zA-Z0-9]+", query) if w not in {"what", "topics", "topic", "in", "the", "are", "for", "course", "syllabus", "show", "me", "tell", "about", "content", "of"}]
            # Look for match in course_name or course_code
            matched = courses[
                courses["course_name"].astype(str).str.lower().apply(lambda name: any(w in name for w in words))
                | courses["course_code"].astype(str).str.lower().apply(lambda code: any(w in code for w in words))
            ]
            if not matched.empty:
                row = matched.iloc[0]
                topics_str = row.get("syllabus", "No topics listed")
                return f"{row['course_name']} ({row['course_code']}) syllabus topics: {topics_str}.", "Courses"

        # 6. Semester status check
        if "status" in query and ("semester" in query or "sem" in query):
            if semesters.empty or requested_semester is None:
                return UNKNOWN_ANSWER, "Courses"
            rows = semesters[semesters["semester"].astype(int) == requested_semester]
            if not rows.empty:
                row = rows.iloc[0]
                return f"Semester {requested_semester} is currently marked '{row['status']}' with {row.get('completed_credits', 0)} of {row.get('total_credits', 0)} credits completed.", "Courses"
            return UNKNOWN_ANSWER, "Courses"

        # 7. Checklist / plan items
        if any(term in query for term in ["checklist", "plan", "task", "milestone", "this week"]):
            if plan.empty:
                return UNKNOWN_ANSWER, "Plan"
            pending = plan[~plan["status"].astype(str).str.lower().eq("done")]
            if pending.empty:
                return "All recorded degree checklist items are marked Done! 🎯", "Plan"
            top_tasks = [f"{r['item']} ({r['status']}, target {r['target_date']})" for _, r in pending.head(3).iterrows()]
            return f"Upcoming open checklist items: {'; '.join(top_tasks)}.", "Plan"

        # Safe grounding fallback
        return UNKNOWN_ANSWER, "Courses"

    def gemini_api_key() -> str | None:
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            return key
        try:
            sec_key = st.secrets.get("GEMINI_API_KEY")
            if sec_key:
                return sec_key
        except Exception:
            pass
        # Check .env file in project directory
        env_file = APP_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
        return None

    def ask_gemini(question: str, fallback: tuple[str, str]) -> tuple[str, str] | None:
        api_key = gemini_api_key()
        if not api_key:
            return None
        try:
            from google import genai
            from google.genai.errors import APIError
            from google.genai import types
        except ImportError:
            return None

        data_context = "\n".join(
            f"{name} CSV data:\n{frame.head(50).to_csv(index=False)}"
            for name, frame in [
                ("Semesters", semesters), ("Courses", courses), ("Calendar", calendar),
                ("Assessments", assessments), ("Scores", scores), ("Plan", plan),
            ]
            if not frame.empty
        )
        prompt = (
            f"DEGREE DATA CONTEXT:\n{data_context}\n\n"
            f"STUDENT QUESTION: {question}\n\n"
            "Instructions: Provide a concise, friendly answer based ONLY on the degree data. "
            "End your answer with the data area used, exactly in the format: 'Data area: <Courses|Calendar|Assessments|Scores|Plan>'."
        )
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are Degree AI. Answer only from the supplied degree data. "
                        "Do not invent university rules, dates, marks, formulas or syllabus content. "
                        f"If the requested information is missing, say: {UNKNOWN_ANSWER}"
                    )
                ),
            )
            if response.text:
                text = response.text.strip()
                area_match = re.search(r"Data area:\s*(Courses|Calendar|Assessments|Scores|Plan)", text, re.IGNORECASE)
                area = area_match.group(1).capitalize() if area_match else fallback[1]
                clean_text = re.sub(r"Data area:\s*(Courses|Calendar|Assessments|Scores|Plan)", "", text, flags=re.IGNORECASE).strip()
                return clean_text, area
        except Exception:
            return fallback
        return fallback

    user_query = selected_chip or st.chat_input("Ask about your courses, dates, assessments, or progress…")

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Policy & formula questions must strictly trigger safe fallback (never hallucinate)
        is_policy = any(
            term in user_query.lower()
            for term in ["cgpa", "gpa formula", "official formula", "exam regulation", "eligibility rule", "attendance rule"]
        )
        
        local_res = local_answer(user_query)
        final_res = local_res if is_policy else (ask_gemini(user_query, local_res) or local_res)
        
        st.session_state.messages.append({"role": "assistant", "content": final_res[0], "area": final_res[1]})
        st.rerun()


# -----------------------------------------------------------------------------
# 11. Data Admin
# -----------------------------------------------------------------------------
elif page == "Data Admin":
    heading("Data Administration & Maintenance", "Directly view and edit CSV datasets powering the Degree OS without touching Python code.")
    st.info("💡 Changes made in the tables below are saved to the `/data` directory and take effect immediately.")
    
    for label, filename in DATA_FILES.items():
        with st.expander(f"📁 {label} ({filename})", expanded=(label == "Courses")):
            frame = load_csv(filename)
            if frame.empty:
                st.warning(f"No existing data at data/{filename}. Enter rows below and click save.")
                frame = pd.DataFrame()
                
            editor = st.data_editor(
                frame,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key=f"admin_editor_{filename}",
            )
            
            if st.button(f"Save {label} Data", key=f"save_btn_{filename}", type="primary"):
                save_csv(filename, editor)
                st.success(f"✅ Successfully saved data/{filename}!")
                st.rerun()
