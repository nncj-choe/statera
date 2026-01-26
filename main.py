import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import io
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
from docx.shared import Inches

# -----------------------------------------------------------------------------
# 1. 환경 설정 및 정체성 정의
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="📊", layout="wide")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

# 그래프 스타일 설정
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

st.markdown(f"""
<style>
    .main-header {{ color: #0f766e; text-align: center; font-size: 2.8rem; font-weight: 700; margin-bottom: 0px; }}
    .acronym-header {{ text-align: center; color: #1e293b; font-size: 1.1rem; font-style: italic; margin-bottom: 2rem; }}
    .stButton>button {{ width: 100%; border-radius: 8px; background-color: #0f766e; color: white; font-weight: bold; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 (정보, 보안, 가이드, 연락처)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("STATERA 📊")
    st.markdown(f"**{ACRONYM_FULL}**")
    
    st.markdown("---")
    st.info("**🔒 데이터 보안 안내**\n본 서비스는 분석 즉시 데이터를 삭제합니다. 어떤 데이터도 서버에 저장되지 않습니다.")
    st.warning("**📄 데이터 형식 가이드**\n파일의 첫 번째 행(Row 1)에는 반드시 변수명이 있어야 합니다.")
    
    st.markdown("---")
    method = st.radio("분석 방법 선택", ["기술통계", "T-test", "ANOVA", "상관분석", "회귀분석"])
    
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.caption("""
    본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다.
    현재 분석 알고리즘의 타당도 검증 및 학술 논문 투고 절차를 진행 중입니다.
    """)
    
    st.markdown("### 📬 Contact & Feedback")
    st.caption("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.caption("메일 앱이 실행되지 않나요? 아래 주소를 복사하세요.")
    st.code("nncj91@snu.ac.kr", language="text")
    
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 3. 통계 엔진 및 리포트 유틸리티
# -----------------------------------------------------------------------------

def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p):
    return "<.001" if p < .001 else f"{p:.3f}"

def get_plot_buffer():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    plt.close()
    return buf

def create_word_report(df, interpretation, plot_buf=None):
    doc = Document()
    doc.add_heading(f'STATERA Analysis Report', 0)
    doc.add_paragraph(f"Engine: {ACRONYM_FULL}")
    
    doc.add_heading('1. Statistical Results', level=1)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
            
    if plot_buf:
        doc.add_heading('2. Visualization', level=1)
        doc.add_picture(plot_buf, width=Inches(5.5))
        
    doc.add_heading('3. AI Interpretation', level=1)
    doc.add_paragraph(interpretation)
    
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# -----------------------------------------------------------------------------
# 4. 메인 UI 및 분석 로직
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

guide_dict = {
    "기술통계": "평균, 표준편차 등을 통해 데이터의 전체 특성을 파악합니다.",
    "T-test": "두 집단(실험군/대조군 등) 간의 평균 차이를 비교합니다.",
    "ANOVA": "세 개 이상의 집단 간 평균 차이를 비교합니다.",
    "상관분석": "두 연속형 변수 사이의 관련성을 분석합니다.",
    "회귀분석": "원인(X)이 결과(Y)에 미치는 영향력을 분석합니다."
}
with st.expander(f"💡 {method} 분석이란?"):
    st.write(guide_dict[method])

up_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    num_cols = df.select_dtypes(include=[np.number]).columns
    final_df, interpretation, plot_img = None, "", None

    if method == "기술통계":
        sel_v = st.multiselect("변수 선택", num_cols)
        if st.button("기술통계 실행") and sel_v:
            final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
            final_df.columns = ['Variable', 'N', 'Mean', 'SD', 'Min', 'Max']
            interpretation = "데이터의 기술통계량입니다."
            plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v]); plot_img = get_plot_buffer()

    elif method == "T-test":
        t_mode = st.radio("유형", ["독립표본", "대응표본", "단일표본"], horizontal=True)
        if t_mode == "독립표본":
            g, y = st.selectbox("집단변수", df.columns), st.selectbox("결과변수", num_cols)
            if st.button("T-test 실행"):
                gps = df[g].unique()
                g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                final_df = pd.DataFrame({"Variable": [y], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"검정 결과 p={format_p(p)}입니다."
                plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
        elif t_mode == "대응표본":
            v1, v2 = st.selectbox("사전", num_cols), st.selectbox("사후", num_cols)
            if st.button("T-test 실행"):
                t, p = stats.ttest_rel(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"Pair": [f"{v1}-{v2}"], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"변화량 검정 결과 p={format_p(p)}입니다."
                plt.figure(figsize=(6, 5)); sns.pointplot(data=df[[v1, v2]]); plot_img = get_plot_buffer()

    elif method == "상관분석":
        v1, v2 = st.selectbox("변수1", num_cols), st.selectbox("변수2", num_cols)
        if st.button("상관분석 실행"):
            r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
            final_df = pd.DataFrame({"Variables": [f"{v1} & {v2}"], "r": [f"{r:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
            interpretation = f"상관분석 결과 상관계수는 {r:.2f}입니다."
            plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df, line_kws={'color':'red'}); plot_img = get_plot_buffer()

    if final_df is not None:
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Result Table")
            st.table(final_df)
            st.info(f"📝 Interpretation: {interpretation}")
        with c2:
            st.subheader("Visualization")
            st.image(plot_img)
        
        report = create_word_report(final_df, interpretation, plot_img)
        st.download_button("📄 워드 리포트 다운로드", data=report, file_name=f"STATERA_Report.docx")

st.markdown("<div style='text-align: center; color: #888; margin-top: 50px;'>Developed by <strong>ANDA Lab Jeongin Choe</strong></div>", unsafe_allow_html=True)
