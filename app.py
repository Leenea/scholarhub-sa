import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="ScholarHub (Southern Africa)", page_icon="🎓", layout="wide")

# Session State Initialization (신청 중 & 수혜 확정 상태 구분)
if "applied_bursaries" not in st.session_state:
    st.session_state.applied_bursaries = [] # 신청 진행 중 목록
if "accepted_bursaries" not in st.session_state:
    st.session_state.accepted_bursaries = [] # 수혜 최종 확정 목록

# Custom CSS
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

# 3. Dummy Data & Dynamic Matching Engine
raw_data = [
    {
        "id": "nsfas",
        "name": "NSFAS Bursary Scheme", 
        "min_inc": "NSFAS 대상 (R350k 이하)", 
        "min_math": 1, 
        "req_quintile": False,
        "coverage_percent": 100,
        "full_fund": True, "init_grant": False, "special": False, 
        "desc": "등록금+주거비+월 생활비 전액 지원 (100% 커버)",
        "deadline": "2026-11-20"
    },
    {
        "id": "idc",
        "name": "IDC Rural Youth Bursary", 
        "min_inc": "전체", 
        "min_math": 4, 
        "req_quintile": True,
        "coverage_percent": 100,
        "full_fund": True, "init_grant": True, "special": False, 
        "desc": "Quintile 1~3 무상교 출신 최우선 선발 풀펀딩 Bursary (100% 커버)",
        "deadline": "2026-11-02"
    },
    {
        "id": "sasol",
        "name": "Sasol STEM Engineering Bursary", 
        "min_inc": "전체", 
        "min_math": 6, 
        "req_quintile": False,
        "coverage_percent": 80,
        "full_fund": True, "init_grant": False, "special": False, 
        "desc": "수학/과학 STEM 전공자 등록금 및 연구비 지원 (80% 커버)",
        "deadline": "2026-11-15"
    },
    {
        "id": "standard",
        "name": "Standard Bank Chairman Grant", 
        "min_inc": "Missing Middle 이하", 
        "min_math": 3, 
        "req_quintile": False,
        "coverage_percent": 30,
        "full_fund": False, "init_grant": True, "special": False, 
        "desc": "대학 입학 전형료 및 초기 상경 교통비 보조 (30% 커버)",
        "deadline": "2026-11-10"
    },
    {
        "id": "vodacom",
        "name": "Vodacom Women in Tech Bursary", 
        "min_inc": "전체", 
        "min_math": 5, 
        "req_quintile": False,
        "coverage_percent": 75,
        "full_fund": True, "init_grant": True, "special": True, 
        "desc": "여성 및 IT 전공자 지원금 (75% 커버)",
        "deadline": "2026-11-25"
    },
    {
        "id": "capitec",
        "name": "Capitec Social Impact Bursary", 
        "min_inc": "NSFAS 대상 (R350k 이하)", 
        "min_math": 2, 
        "req_quintile": False,
        "coverage_percent": 60,
        "full_fund": True, "init_grant": False, "special": True, 
        "desc": "한부모/SASSA 수혜 가구 전용 지원금 (60% 커버)",
        "deadline": "2026-11-18"
    }
]

matched_bursaries = []
for b in raw_data:
    inc_pass = False
    if b["min_inc"] == "전체":
        inc_pass = True
    elif b["min_inc"] == "NSFAS 대상 (R350k 이하)" and income == "NSFAS 대상 (R350k 이하)":
        inc_pass = True
    elif b["min_inc"] == "Missing Middle 이하" and income in ["NSFAS 대상 (R350k 이하)", "Missing Middle (R350k-R600k)"]:
        inc_pass = True

    math_pass = math_lvl >= b["min_math"]
    quin_pass = True
    if b["req_quintile"] and not is_quintile_no_fee:
        quin_pass = False

    if inc_pass and math_pass and quin_pass:
        matched_bursaries.append(b)

accepted_items = [b for b in raw_data if b["id"] in st.session_state.accepted_bursaries]
applied_items = [b for b in raw_data if b["id"] in st.session_state.applied_bursaries]

actual_coverage = sum(item["coverage_percent"] for item in accepted_items)
actual_coverage = min(actual_coverage, 100)

# Header
st.title("🎓 ScholarHub (Southern Africa)")
st.caption("남아프리카공화국 청년 맞춤형 장학금 매칭 & 디지털 케어 플랫폼")

col_head1, col_head2 = st.columns([3, 1])
with col_head2:
    st.info(f"🔔 **신청 진행 중**: {len(applied_items)}건 | **수혜 확정**: {len(accepted_items)}건")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 대시보드", "🔍 맞춤 장학금 탐색", "🚀 미래 장학금 탐색", "📅 내 캘린더", "💬 커뮤니티"])

# TAB 1: 대시보드
with tab1:
    st.header("🏠 내 실시간 장학금 수혜 현황")
    
    col_dash1, col_dash2 = st.columns([1, 1])
    with col_dash1:
        if not lite_mode:
            fig = px.pie(
                names=["수혜 확정 커버리지", "잔여 부담금"], 
                values=[actual_coverage, 100 - actual_coverage], 
                hole=0.65, 
                color_discrete_sequence=["#2B8A3E" if actual_coverage > 0 else "#495057", "#E9ECEF"]
            )
            fig.update_layout(showlegend=True, title=f"현재 최종 수혜 확정 비율: {actual_coverage}%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.metric(label="📊 [Lite Mode] 현재 확정 학비 면제 비율", value=f"{actual_coverage}%")

    with col_dash2:
        st.subheader(f"👋 반갑습니다, {name}님!")
        st.write(f"- **자격 충족 장학금**: 총 **{len(matched_bursaries)}건** 지원 가능")
        st.write(f"- **현재 신청 진행 중**: **{len(applied_items)}건**")
        st.write(f"- **최종 수혜 확정**: **{len(accepted_items)}건** (학비 {actual_coverage}% 면제)")
        
        if len(accepted_items) > 0 or len(applied_items) > 0:
            if st.button("🔄 내역 전체 초기화"):
                st.session_state.applied_bursaries = []
                st.session_state.accepted_bursaries = []
                st.rerun()

    st.divider()

    # 클릭해서 확장해보는 2개의 대시보드 목록
    with st.expander("🏆 [클릭] 수혜 확정된 장학금 목록 보기", expanded=True):
        if accepted_items:
            for item in accepted_items:
                st.success(f"🎉 **{item['name']}** — 학비 +{item['coverage_percent']}% 확정 지원")
        else:
            st.info("아직 수혜 확정된 장학금이 없습니다. 탐색 탭에서 [수혜 확정 등록]을 눌러보세요.")

    with st.expander("📑 [클릭] 현재 신청 진행 중인 장학금 목록 보기", expanded=False):
        if applied_items:
            for item in applied_items:
                st.warning(f"⏳ **{item['name']}** — 서류 검수 및 심사 진행 중 (마감일: {item['deadline']})")
        else:
            st.info("현재 심사 진행 중인 장학금이 없습니다.")

# TAB 2: 맞춤 장학금 탐색
with tab2:
    st.header("🔍 100% 맞춤 장학금 탐색 및 상태 관리")
    st.caption("각 장학금의 [지원 신청] 또는 [수혜 확정] 버튼을 누르면 대시보드 목록과 차트에 즉시 반영됩니다.")
    
    if matched_bursaries:
        for b in matched_bursaries:
            with st.container(border=True):
                is_applied = b["id"] in st.session_state.applied_bursaries
                is_accepted = b["id"] in st.session_state.accepted_bursaries
                
                st.subheader(f"{b['name']}")
                st.write(f"**상세 설명**: {b['desc']}")
                st.write(f"**지원 자격 조건**: 소득({b['min_inc']}) | 수학 최소 Level {b['min_math']}")
                
                col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
                with col_b1:
                    if st.button(f"📑 지원 신청하기", key=f"app_{b['id']}", disabled=is_applied):
                        if b["id"] not in st.session_state.applied_bursaries:
                            st.session_state.applied_bursaries.append(b["id"])
                            st.toast(f"📑 {b['name']} 신청 진행 중 목록에 추가되었습니다.")
                            st.rerun()
                
                with col_b2:
                    if st.button(f"🏆 수혜 확정 등록 (+{b['coverage_percent']}% 커버)", key=f"acc_{b['id']}", disabled=is_accepted):
                        if b["id"] not in st.session_state.accepted_bursaries:
                            st.session_state.accepted_bursaries.append(b["id"])
                            st.toast(f"🎉 축하합니다! {b['name']} 수혜 확정 목록에 추가되었습니다.")
                            st.rerun()

                with col_b3:
                    status_text = ""
                    if is_accepted:
                        status_text = "🟢 **수혜 확정됨**"
                    elif is_applied:
                        status_text = "🟡 **심사 진행 중**"
                    else:
                        status_text = "⚪ 지원 미신청"
                    st.markdown(f"**현재 상태**: {status_text}")
    else:
        st.error("조건을 만족하는 장학금이 없습니다.")

# TAB 3: 미래 장학금 탐색
with tab3:
    st.header("🚀 미래 장학금 탐색 (Future Exploration)")
    target_dept = st.selectbox("목표 희망 전공 선택", ["Computer Science / IT", "Engineering (공학)", "Commerce / Accounting (경영/회계)", "Medicine (의학)"])
    st.success(f"🎯 **{target_dept}** 진학 시 수혜 가능한 대기업 장학금 준비 요건이 세팅되었습니다.")

# TAB 4: 월간 캘린더
with tab4:
    st.header("📅 2026년 11월 장학금 캘린더")
    days = ["일 (Sun)", "월 (Mon)", "화 (Tue)", "수 (Wed)", "목 (Thu)", "금 (Fri)", "토 (Sat)"]
    cols = st.columns(7)
    for idx, day in enumerate(days):
        cols[idx].markdown(f"**{day}**")

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

# TAB 5: 커뮤니티
with tab5:
    st.header("💬 남아공 Bursary 선배들의 합격 커뮤니티")
    st.chat_message("user").write("Quintile 2 출신인데 Tribal Letter 서류 제출 시 경찰서 공증 필수인가요?")
    st.chat_message("assistant").write("네! 부족장 확인서 도장과 함께 가까운 SAPS(경찰서)에서 Affidavit 공증을 받아 올리면 승인 절차가 빨라집니다.")
