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
# 1. 페이지 설정 
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="📊", layout="wide")

# 그래프 한글 및 스타일 설정
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

st.markdown(f"""
<style>
    .main-header {{ color: #0f766e; text-align: center; font-size: 3rem; font-weight: 800; margin-bottom: 0px; }}
    .acronym-header {{ text-align: center; color: #475569; font-size: 1.1rem; font-style: italic; margin-bottom: 30px; }}
    .guide-card {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; margin-bottom: 30px; }}
    .guide-title {{ color: #0f766e; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px; }}
    .guide-item {{ margin-bottom: 8px; font-size: 0.95rem; color: #334155; }}
    .upload-waiting {{ text-align: center; padding: 50px; border: 2px dashed #cbd5e1; border-radius: 15px; color: #64748b; margin-top: 20px; }}
    .step-header {{ color: #0f766e; font-size: 1.5rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #f0fdfa; padding-bottom: 5px; }}
    .stButton>button {{ width: 100%; border-radius: 8px; background-color: #0f766e; color: white; font-weight: bold; height: 3em; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 통계 엔진 및 리포트 유틸리티
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
        
    doc.add_heading('3. Interpretation', level=1)
    doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio

# -----------------------------------------------------------------------------
# 3. 사이드바 (정보 및 연락처)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("STATERA 📊")
    st.markdown(f"**{ACRONYM_FULL}**")
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.caption("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다. 현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("### 📬 Contact & Feedback")
    st.caption("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 4. 메인 워크플로우
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

# 가이드 카드
st.markdown("""
<div class="guide-card">
    <div class="guide-title">🔍 분석 시작 전 확인해 주세요</div>
    <div class="guide-item">🔒 <b>데이터 보안 안내:</b> 분석 즉시 데이터를 삭제하며, 서버에 저장되지 않습니다.</div>
    <div class="guide-item">📄 <b>데이터 형식 가이드:</b> 첫 번째 행(Row 1)에는 반드시 변수명이 있어야 합니다.</div>
</div>
""", unsafe_allow_html=True)

up_file = st.file_uploader("연구 데이터를 업로드하세요", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    st.success(f"✔️ 데이터 로드 완료 (N={len(df)})")
    with st.expander("📊 데이터 미리보기"):
        st.dataframe(df.head())

    st.markdown('<div class="step-header">STEP 2. 분석 방법 선택</div>', unsafe_allow_html=True)
    method = st.selectbox("수행할 통계 분석을 선택하세요", ["분석 선택 안 함", "기술통계", "T-test", "ANOVA", "상관분석", "회귀분석"])

    if method != "분석 선택 안 함":
        num_cols = df.select_dtypes(include=[np.number]).columns
        final_df, interpretation, plot_img = None, "", None

        if method == "기술통계":
            sel_v = st.multiselect("변수 선택", num_cols)
            if st.button("분석 실행") and sel_v:
                final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
                final_df.columns = ['Variable', 'N', 'Mean', 'SD', 'Min', 'Max']
                interpretation = "기술통계 분석 결과입니다."
                plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v]); plot_img = get_plot_buffer()

        elif method == "T-test":
            t_mode = st.radio("유형", ["독립표본", "대응표본", "단일표본"], horizontal=True)
            if t_mode == "독립표본":
                g, y = st.selectbox("집단 변수", df.columns), st.selectbox("결과 변수", num_cols)
                if st.button("분석 실행"):
                    gps = df[g].unique()
                    g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                    t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                    final_df = pd.DataFrame({"Variable": [y], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"독립표본 T-검정 결과 p={format_p(p)}입니다."
                    plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
            elif t_mode == "대응표본":
                v1, v2 = st.selectbox("사전", num_cols), st.selectbox("사후", num_cols)
                if st.button("분석 실행"):
                    t, p = stats.ttest_rel(df[v1].dropna(), df[v2].dropna())
                    final_df = pd.DataFrame({"Pair": [f"{v1}-{v2}"], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"대응표본 T-검정 결과 p={format_p(p)}입니다."
                    plt.figure(figsize=(6, 5)); sns.pointplot(data=df[[v1, v2]]); plot_img = get_plot_buffer()
            elif t_mode == "단일표본":
                v, mu = st.selectbox("변수", num_cols), st.number_input("검정값", value=0.0)
                if st.button("분석 실행"):
                    t, p = stats.ttest_1samp(df[v].dropna(), mu)
                    final_df = pd.DataFrame({"Variable": [v], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"단일표본 T-검정 결과 p={format_p(p)}입니다."
                    plt.figure(figsize=(6, 5)); sns.histplot(df[v], kde=True); plt.axvline(mu, color='red'); plot_img = get_plot_buffer()

        elif method == "ANOVA":
            g, y = st.selectbox("집단 변수", df.columns), st.selectbox("결과 변수", num_cols)
            if st.button("분석 실행"):
                groups = [df[df[g]==val][y].dropna() for val in df[g].unique()]
                f_stat, p = stats.f_oneway(*groups)
                final_df = pd.DataFrame({"Variable": [y], "F": [f"{f_stat:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"일원배치 분산분석 결과 p={format_p(p)}입니다."
                plt.figure(figsize=(8, 5)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()

        elif method == "상관분석":
            v1, v2 = st.selectbox("변수 1", num_cols), st.selectbox("변수 2", num_cols)
            if st.button("분석 실행"):
                r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"Variables": [f"{v1} & {v2}"], "r": [f"{r:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"상관분석 결과 r={r:.2f}입니다."
                plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df); plot_img = get_plot_buffer()

        elif method == "회귀분석":
            reg_t = st.radio("유형", ["선형", "로지스틱"], horizontal=True)
            x_v, y_v = st.multiselect("독립변수(X)", num_cols), st.selectbox("종속변수(Y)", num_cols)
            if st.button("분석 실행") and x_v:
                X = sm.add_constant(df[x_v])
                if reg_t == "선형":
                    model = sm.OLS(df[y_v], X).fit()
                    final_df = pd.DataFrame({"B": model.params, "p": model.pvalues}).reset_index()
                    interpretation = f"선형회귀 결과 R²={model.rsquared:.3f}입니다."
                else:
                    model = sm.Logit(df[y_v], X).fit(disp=0)
                    final_df = pd.DataFrame({"OR": np.exp(model.params), "p": model.pvalues}).reset_index()
                    interpretation = f"로지스틱 회귀 결과 Pseudo R²={model.prsquared:.3f}입니다."
                final_df['p'] = final_df['p'].apply(lambda x: f"{format_p(x)}{get_stars(x)}")
                plt.figure(figsize=(8, 5)); sns.heatmap(df[x_v + [y_v]].corr(), annot=True); plot_img = get_plot_buffer()

        if final_df is not None:
            st.markdown('<div class="step-header">STEP 3. 분석 결과</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1.2, 1])
            with c1:
                st.table(final_df)
                st.info(f"📝 {interpretation}")
            with c2: st.image(plot_img)
            
            report = create_word_report(final_df, interpretation, plot_img)
            st.download_button("📄 워드 리포트 다운로드", data=report, file_name=f"STATERA_Report.docx")
else:
    st.markdown('<div class="upload-waiting">⬆️ 분석을 시작하려면 상단의 업로드 영역에 파일을 올려주세요.</div>', unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #888; margin-top: 50px;'>Developed by <strong>ANDA Lab Jeongin Choe</strong></div>", unsafe_allow_html=True)
