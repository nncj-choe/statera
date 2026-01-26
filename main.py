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
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="📊", layout="wide")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

st.markdown(f"""
<style>
    .main-header {{ color: #0f766e; text-align: center; font-size: 2.8rem; font-weight: 700; margin-bottom: 0px; }}
    .acronym-header {{ text-align: center; color: #1e293b; font-size: 1.1rem; font-style: italic; margin-bottom: 2rem; }}
    .stButton>button {{ width: 100%; border-radius: 8px; background-color: #0f766e; color: white; font-weight: bold; margin-top: 10px; }}
    .step-header {{ color: #0f766e; font-size: 1.5rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #f0fdfa; padding-bottom: 5px; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 (정적 정보만 유지)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("STATERA 📊")
    st.markdown(f"**{ACRONYM_FULL}**")
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.caption("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다.")
    st.markdown("---")
    st.markdown("### 📬 Contact & Feedback")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 3. 유틸리티 함수
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
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
    if plot_buf:
        doc.add_heading('Visualization', level=1); doc.add_picture(plot_buf, width=Inches(5.5))
    doc.add_heading('AI Interpretation', level=1); doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio

# -----------------------------------------------------------------------------
# 4. 메인 워크플로우 (메인 화면)
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

# STEP 1. 파일 업로드 및 가이드
st.markdown('<div class="step-header">STEP 1. 연구 데이터 업로드</div>', unsafe_allow_html=True)
c1, c2 = st.columns([2, 1])
with c2:
    st.info("**🔒 데이터 보안**\n분석 즉시 데이터를 삭제하며, 서버에 저장되지 않습니다.")
    st.warning("**📄 데이터 형식**\n첫 번째 행(Row 1)에 반드시 변수명이 있어야 합니다.")

with c1:
    up_file = st.file_uploader("엑셀 또는 CSV 파일을 선택하세요", type=["xlsx", "csv"])

if up_file:
    # 데이터 로드 및 확인
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    st.success(f"✔️ 데이터 로드 완료! (총 {len(df)}명의 대상자)")
    with st.expander("데이터 미리보기"):
        st.dataframe(df.head(), use_container_width=True)

    # STEP 2. 분석 방법 선택
    st.markdown('<div class="step-header">STEP 2. 분석 방법 선택</div>', unsafe_allow_html=True)
    method = st.selectbox(
        "수행할 분석 방법을 선택하세요",
        ["분석 선택 안 함", "기술통계", "T-test", "ANOVA", "상관분석", "회귀분석"]
    )

    if method != "분석 선택 안 함":
        guide_dict = {
            "기술통계": "평균, 표준편차 등을 통해 데이터의 전체 특성을 파악합니다.",
            "T-test": "두 집단(실험군/대조군 등) 간의 평균 차이를 비교합니다.",
            "ANOVA": "세 개 이상의 집단 간 평균 차이를 비교합니다.",
            "상관분석": "두 연속형 변수 사이의 관련성을 분석합니다.",
            "회귀분석": "원인(X)이 결과(Y)에 미치는 영향력을 분석합니다."
        }
        st.info(f"💡 **{method} 분석이란?** {guide_dict[method]}")
        
        # 분석 옵션 설정 및 실행
        num_cols = df.select_dtypes(include=[np.number]).columns
        final_df, interpretation, plot_img = None, "", None

        if method == "기술통계":
            sel_v = st.multiselect("분석할 변수를 선택하세요", num_cols)
            if st.button("기술통계 실행") and sel_v:
                final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
                final_df.columns = ['Variable', 'N', 'Mean', 'SD', 'Min', 'Max']
                interpretation = "데이터의 기술통계량입니다."
                plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v]); plot_img = get_plot_buffer()

        elif method == "T-test":
            t_mode = st.radio("T-test 유형", ["독립표본", "대응표본", "단일표본"], horizontal=True)
            if t_mode == "독립표본":
                g, y = st.selectbox("집단변수 (2집단)", df.columns), st.selectbox("결과변수 (연속형)", num_cols)
                if st.button("분석 실행"):
                    gps = df[g].unique()
                    g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                    t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                    final_df = pd.DataFrame({"Variable": [y], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"검정 결과 p={format_p(p)}입니다."
                    plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df, capsize=.1); plot_img = get_plot_buffer()
            # ... (T-test 다른 유형 동일 로직 생략 없이 포함 가능) ...

        elif method == "상관분석":
            v1, v2 = st.selectbox("변수 1", num_cols), st.selectbox("변수 2", num_cols)
            if st.button("상관분석 실행"):
                r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"Variables": [f"{v1} & {v2}"], "r": [f"{r:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"상관분석 결과 r={r:.2f}, p={format_p(p)}입니다."
                plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df, line_kws={'color':'red'}); plot_img = get_plot_buffer()

        # STEP 3. 결과 출력
        if final_df is not None:
            st.markdown('<div class="step-header">STEP 3. 분석 결과 및 리포트</div>', unsafe_allow_html=True)
            res_c1, res_c2 = st.columns(2)
            with res_c1:
                st.table(final_df)
                st.info(f"📝 {interpretation}")
            with res_c2:
                st.image(plot_img)
            
            report = create_word_report(final_df, interpretation, plot_img)
            st.download_button("📄 분석 리포트(Word) 다운로드", data=report, file_name="STATERA_Report.docx")

else:
    st.info("⬆️ 위 업로드 박스에 파일을 끌어다 놓으세요. 분석 프로세스가 시작됩니다.")

st.markdown("<div style='text-align: center; color: #888; margin-top: 50px;'>Developed by <strong>ANDA Lab Jeongin Choe</strong></div>", unsafe_allow_html=True)
