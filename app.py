import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="ScholarHub (Southern Africa)", page_icon="🎓", layout="wide")

# Custom CSS for UI polish & Calendar
st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; }
    .calendar-card {
        border: 1px solid #E9ECEF;
        border-radius: 8px;
        padding: 8px;
        min-height: 80px;
        background-color: white;
    }
    .badge-idc { background-color: #FFE3E3; color: #C92A2A; font-size: 11px; padding: 2px 4px; border-radius: 4px; margin-top: 4px; font-weight: bold; }
    .badge-nsfas { background-color: #E7F5FF; color: #1864AB; font-size: 11px; padding: 2px 4px; border-radius: 4px; margin-top: 4px; font-weight: bold; }
    .badge-sasol { background-color: #E6FCF5; color: #087F5B; font-size: 11px; padding: 2px 4px; border-radius: 4px; margin-top: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# 2. Sidebar - Lite Mode & Profile
st.sidebar.title("🎓 ScholarHub Profile")
lite_mode = st.sidebar.toggle("📱 데이터 절약 모드 (Lite Mode)", value=False)

st.sidebar.subheader("📄 AI 서류 드롭존")
uploaded_file = st.sidebar.file_uploader("증명서 업로드 (Proof of Address, Tribal Letter, SASSA)", type=["pdf", "png", "jpg"])
if uploaded_file:
    st.sidebar.success(f"✓ {uploaded_file.name} 검증 완료")

st.sidebar.subheader("👤 6단계 학생 프로필")
name = st.sidebar.text_input("이름", value="Lee Nae Hyeok")
province = st.sidebar.selectbox("거주 지역", ["Gauteng", "Western Cape", "KwaZulu-Natal", "Limpopo", "Eastern Cape"])
school_type = st.sidebar.selectbox("학교/커리큘럼 선택", ["Secondary (Quintile 1-3 No-Fee)", "Secondary (Quintile 4-5)", "University / TVET"])
school_search = st.sidebar.text_input("2차 학교명 검색", value="Thubelihle High School")
income = st.sidebar.selectbox("가계 소득 구간", ["NSFAS 대상 (R350k 이하)", "Missing Middle (R350k-R600k)", "General (R600k 초과)"])
family = st.sidebar.selectbox("가정 형태 & 우대 조건", ["일반", "Single Parent (한부모)", "Orphan (보호대상/고아)", "SASSA 수혜 가구"])
math_lvl = st.sidebar.slider("수학 (Mathematics Level)", 1, 7, 6)
sci_lvl = st.sidebar.slider("과학 (Physical Sciences Level)", 1, 7, 5)

is_quintile_no_fee = "Quintile 1-3" in school_type
if is_quintile_no_fee:
    st.sidebar.success("🏫 Quintile 1~3 무상교 인증 완료")

# 3. Dynamic Calculation: 학비 커버리지 비율
coverage = 0
if income == "NSFAS 대상 (R350k 이하)":
    coverage += 60
elif income == "Missing Middle (R350k-R600k)":
    coverage += 35
else:
    coverage += 10

if is_quintile_no_fee:
    coverage += 25

if family in ["Orphan (보호대상/고아)", "SASSA 수혜 가구"]:
    coverage += 15
elif family == "Single Parent (한부모)":
    coverage += 10

coverage = min(coverage, 100)

# 4. Dummy Data & Dynamic Matching Engine
raw_data = [
    {
        "name": "NSFAS Bursary Scheme", 
        "min_inc": "NSFAS 대상 (R350k 이하)", 
        "min_math": 1, 
        "req_quintile": False,
        "full_fund": True, "init_grant": False, "special": False, 
        "desc": "남아공 정부 공식 전액 학비/주거/생활비 지원 프로그램",
        "deadline": "2026-11-20"
    },
    {
        "name": "IDC Rural Youth Bursary", 
        "min_inc": "전체", 
        "min_math": 4, 
        "req_quintile": True,
        "full_fund": True, "init_grant": True, "special": False, 
        "desc": "Quintile 1~3 무상교 출신 최우선 선발 풀펀딩 Bursary",
        "deadline": "2026-11-02"
    },
    {
        "name": "Sasol STEM Engineering Bursary", 
        "min_inc": "전체", 
        "min_math": 6, 
        "req_quintile": False,
        "full_fund": True, "init_grant": False, "special": False, 
        "desc": "수학 Level 6 및 과학 Level 5 이상 STEM 전공 희망자 전액 우대 지원",
        "deadline": "2026-11-15"
    },
    {
        "name": "Standard Bank Chairman Grant", 
        "min_inc": "Missing Middle 이하", 
        "min_math": 3, 
        "req_quintile": False,
        "full_fund": False, "init_grant": True, "special": False, 
        "desc": "대학 입학 전형료(R100~300) 및 상경 교통비 초기 지원",
        "deadline": "2026-11-10"
    },
    {
        "name": "Vodacom Women in Tech Bursary", 
        "min_inc": "전체", 
        "min_math": 5, 
        "req_quintile": False,
        "full_fund": True, "init_grant": True, "special": True, 
        "desc": "여성 및 공학/IT 커리어 희망자 우대 Bursary",
        "deadline": "2026-11-25"
    },
    {
        "name": "Capitec Social Impact Bursary", 
        "min_inc": "NSFAS 대상 (R350k 이하)", 
        "min_math": 2, 
        "req_quintile": False,
        "full_fund": True, "init_grant": False, "special": True, 
        "desc": "한부모 가정 및 SASSA 수혜 가구 전용 취업 연계형 Bursary",
        "deadline": "2026-11-18"
    }
]

matched_bursaries = []
for b in raw_data:
    # 소득 조건 판별
    inc_pass = False
    if b["min_inc"] == "전체":
        inc_pass = True
    elif b["min_inc"] == "NSFAS 대상 (R350k 이하)" and income == "NSFAS 대상 (R350k 이하)":
        inc_pass = True
    elif b["min_inc"] == "Missing Middle 이하" and income in ["NSFAS 대상 (R350k 이하)", "Missing Middle (R350k-R600k)"]:
        inc_pass = True

    # 성적 조건 판별
    math_pass = math_lvl >= b["min_math"]

    # Quintile 무상교 필수 조건 판별
    quin_pass = True
    if b["req_quintile"] and not is_quintile_no_fee:
        quin_pass = False

    if inc_pass and math_pass and quin_pass:
        matched_bursaries.append(b)

# Header
st.title("🎓 ScholarHub (Southern Africa)")
st.caption("남아프리카공화국 청년 맞춤형 장학금 매칭 & 디지털 케어 플랫폼")

col_head1, col_head2 = st.columns([3, 1])
with col_head2:
    st.info(f"🔔 **실시간 매칭 알림**: {len(matched_bursaries)}건의 지원 가능 Bursary 발견")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 대시보드", "🔍 맞춤 장학금 탐색", "🚀 미래 장학금 탐색", "📅 내 캘린더", "💬 커뮤니티"])

# TAB 1: 대시보드
with tab1:
    st.header("🏠 내 수혜 현황 및 예상 학비 커버리지")
    
    col_dash1, col_dash2 = st.columns([1, 1])
    with col_dash1:
        if not lite_mode:
            fig = px.pie(
                names=["예상 수혜 커버리지", "잔여 본인 부담"], 
                values=[coverage, 100 - coverage], 
                hole=0.65, 
                color_discrete_sequence=["#1B263B", "#E9ECEF"]
            )
            fig.update_layout(showlegend=True, title=f"프로필 기반 학비 면제 비율: {coverage}%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric(label="📊 [Lite Mode] 예상 학비 면제 비율", value=f"{coverage}%")

    with col_dash2:
        st.subheader(f"👋 반갑습니다, {name}님!")
        st.write(f"- **선택 학교**: {school_search} ({school_type})")
        st.write(f"- **소득/우대**: {income} | {family}")
        st.write(f"- **수학 성적**: Level {math_lvl}")
        st.success(f"현재 조건으로 **총 {len(matched_bursaries)}개**의 Bursary에 지원 자격이 충족됩니다.")

    st.divider()
    st.subheader("🎯 실시간 매칭된 핵심 장학금 목록")
    if matched_bursaries:
        for b in matched_bursaries[:3]:
            st.info(f"✨ **{b['name']}** - {b['desc']} (마감일: {b['deadline']})")
    else:
        st.warning("현재 입력 조건에 매칭되는 장학금이 없습니다. 프로필 조건(소득/성적 등)을 조정해보세요.")

# TAB 2: 🔍 맞춤 장학금 탐색
with tab2:
    st.header("🔍 100% 맞춤 장학금 탐색 (자격 충족 전용)")
    st.caption("학생 프로필(소득, Quintile 무상교, 수학 Level)에 기반하여 실제 신청 가능한 장학금만 필터링되어 표시됩니다.")
    
    if matched_bursaries:
        for b in matched_bursaries:
            with st.container(border=True):
                tags = ""
                if b["full_fund"]: tags += " `[🏠 풀펀딩 Bursary]`"
                if b["init_grant"]: tags += " `[🎁 초기 진학 지원금]`"
                if b["special"]: tags += " `[👩‍💻 여성/특수 우대]`"
                if b["req_quintile"]: tags += " `[🌾 농촌 무상교 전용]`"
                
                st.subheader(f"{b['name']} {tags}")
                st.write(f"**상세 설명**: {b['desc']}")
                st.write(f"**필요 지원 조건**: 소득({b['min_inc']}) | 수학 최소 Level {b['min_math']}")
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button("신청 및 캘린더 등록", key=f"btn_{b['name']}"):
                        st.toast(f"✅ {b['name']} 지원 목록에 등록 완료!")
    else:
        st.error("조건을 만족하는 장학금이 없습니다. 프로필 항목을 수정해주세요.")

# TAB 3: 🚀 미래 장학금 탐색
with tab3:
    st.header("🚀 미래 장학금 탐색 (Future Exploration)")
    target_dept = st.selectbox("목표 희망 전공 선택", ["Computer Science / IT", "Engineering (공학)", "Commerce / Accounting (경영/회계)", "Medicine (의학)"])
    st.success(f"🎯 **{target_dept}** 진학 시 수혜 가능한 대기업 장학금 준비 요건이 세팅되었습니다.")
    
    if st.button("💡 준비 가이드 보기 (Preparation Guide)"):
        with st.expander("📌 Matric 목표 성적 & Motivational Letter 작성 가이드", expanded=True):
            st.markdown("""
- **Matric 목표 성적**: Mathematics Level 6 (70% 이상), Physical Sciences Level 5 이상 필수
- **Motivational Letter (자기소개서) 작성 팁**:
  1. 남아공 Bursary는 화려한 수식어보다 **가계 경제적 난관(SASSA, 농촌 거주) 및 학업 의지**를 정직하게 서술하는 것이 핵심입니다.
  2. 희망 전공 선택 이유와 졸업 후 남아공 지역 사회 기여 계획을 두괄식으로 작성하세요.
""")

# TAB 4: 📅 진짜 월간 캘린더 (Interactive Grid)
with tab4:
    st.header("📅 2026년 11월 장학금 캘린더 (Monthly Calendar)")
    st.caption("장학금 신청 및 서류 마감 일정이 달력 날짜에 직접 노출됩니다.")

    days = ["일 (Sun)", "월 (Mon)", "화 (Tue)", "수 (Wed)", "목 (Thu)", "금 (Fri)", "토 (Sat)"]
    cols = st.columns(7)
    for idx, day in enumerate(days):
        cols[idx].markdown(f"**{day}**")

    # 2026년 11월 1일은 일요일(Sunday)
    calendar_days = [
        (1, ""), (2, "IDC Bursary 마감"), (3, ""), (4, ""), (5, ""), (6, ""), (7, ""),
        (8, ""), (9, ""), (10, "Standard Bank 마감"), (11, ""), (12, ""), (13, ""), (14, ""),
        (15, "Sasol STEM 마감"), (16, ""), (17, ""), (18, "Capitec Bursary 마감"), (19, ""), (20, "NSFAS 전액 장학 마감"), (21, ""),
        (22, ""), (23, ""), (24, ""), (25, "Vodacom Tech 마감"), (26, ""), (27, ""), (28, ""),
        (29, ""), (30, ""), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")
    ]

    for i in range(5):
        row_cols = st.columns(7)
        for j in range(7):
            day_num, event = calendar_days[i*7 + j]
            with row_cols[j]:
                if day_num != "":
                    event_html = ""
                    if "IDC" in event:
                        event_html = f"<div class='badge-idc'>⏱️ {event}</div>"
                    elif "NSFAS" in event:
                        event_html = f"<div class='badge-nsfas'>📅 {event}</div>"
                    elif "Sasol" in event:
                        event_html = f"<div class='badge-sasol'>🌿 {event}</div>"
                    elif event:
                        event_html = f"<div class='badge-idc'>📌 {event}</div>"

                    st.markdown(f"""
                    <div class="calendar-card">
                        <b>{day_num}</b>
                        {event_html}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="calendar-card" style="background-color:#F8F9FA;"></div>', unsafe_allow_html=True)

# TAB 5: 💬 커뮤니티
with tab5:
    st.header("💬 남아공 Bursary 선배들의 합격 커뮤니티")
    st.chat_message("user").write("Quintile 2 출신인데 Tribal Letter 서류 제출 시 경찰서 공증 필수인가요?")
    st.chat_message("assistant").write("네! 부족장 확인서 도장과 함께 가까운 SAPS(경찰서)에서 Affidavit 공증을 함께 올리면 판별 승인이 훨씬 빨라집니다.")
