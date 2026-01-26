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
# 1. UI 스타일링 및 테마 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="📊", layout="wide")

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="white")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    .main-header {{ color: #0d9488; text-align: center; font-size: 3.5rem; font-weight: 800; margin-bottom: 0px; letter-spacing: -1px; }}
    .acronym-header {{ text-align: center; color: #64748b; font-size: 1rem; font-weight: 400; margin-bottom: 40px; text-transform: uppercase; letter-spacing: 2px; }}
    
    /* 가이드 카드 디자인 */
    .guide-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
    .guide-box {{ flex: 1; background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }}
    .guide-label {{ font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
    .guide-text {{ font-size: 0.9rem; color: #64748b; line-height: 1.6; }}

    /* 방법론 안내 박스 */
    .method-info {{ background-color: #f0fdfa; border-left: 5px solid #0d9488; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
    .method-title {{ color: #0f766e; font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; }}
    .method-desc {{ color: #1e293b; font-size: 0.95rem; line-height: 1.6; }}
    .var-badge {{ background-color: #ccfbf1; color: #0f766e; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.85rem; margin-right: 5px; }}

    .landing-zone {{ text-align: center; padding: 60px 20px; background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 20px; margin-top: 20px; }}
    .step-badge {{ background: #0d9488; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-right: 10px; }}
    .section-title {{ font-size: 1.6rem; font-weight: 700; color: #0f172a; margin: 30px 0 20px 0; display: flex; align-items: center; }}
    .stButton>button {{ width: 100%; border-radius: 10px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; font-weight: 700; height: 3.5em; border: none; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#0d9488;'>STATERA 📊</h2>", unsafe_allow_html=True)
    st.caption(ACRONYM_FULL)
    st.markdown("---")
    st.markdown("#### 🚧 Research Beta Version")
    st.info("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다. 현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("#### 📬 Contact & Feedback")
    st.write("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.caption("주소 복사:")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 3. 통계 엔진 및 리포트 함수
# -----------------------------------------------------------------------------
METHOD_GUIDES = {
    "기술통계": {
        "title": "📈 기술통계 (Descriptive Statistics)",
        "desc": "데이터의 기초 정보를 파악합니다. 사례 수(N), 평균, 표준편차 등을 산출합니다.",
        "use": "연구 대상자의 일반적 특성을 요약하거나 변수의 경향성을 보고할 때 사용합니다."
    },
    "T-test": {
        "title": "👥 T-검정 (T-test)",
        "desc": "두 그룹 사이의 평균 차이를 확인합니다.",
        "iv": "범주형 (2집단)", "dv": "연속형 변수",
        "use": "성별에 따른 만족도 차이, 실험 전/후 점수 비교 등에 사용합니다."
    },
    "ANOVA": {
        "title": "🏫 분산분석 (ANOVA)",
        "desc": "세 개 이상의 그룹 사이의 평균 차이를 확인합니다.",
        "iv": "범주형 (3집단 이상)", "dv": "연속형 변수",
        "use": "학력이나 연령대별 직무 소진 차이 분석 등에 사용합니다."
    },
    "상관분석": {
        "title": "🔗 상관분석 (Correlation Analysis)",
        "desc": "두 변수가 서로 얼마나 닮은 방향으로 움직이는지 분석합니다.",
        "iv": "연속형 변수", "dv": "연속형 변수",
        "use": "두 변수가 비례(함께 증가)하거나 반비례(반대로 감소)하는지 확인할 때 사용합니다."
    },
    "회귀분석": {
        "title": "🎯 회귀분석 (Regression Analysis)",
        "desc": "어떤 원인이 결과에 얼마나 영향을 미치는지 수치로 예측합니다.",
        "iv": "연속형 또는 범주형", "dv": "연속형(선형) 또는 이분 범주형(로지스틱)",
        "use": "원인 변수가 결과 변수의 발생 여부나 점수를 얼마나 예측하는지 분석할 때 사용합니다."
    }
}

def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"

def get_plot_buffer():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    plt.close()
    return buf

def create_word_report(df, interpretation, plot_buf=None):
    doc = Document()
    doc.add_heading('STATERA: Statistical Analysis Report', 0)
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
    if plot_buf:
        doc.add_heading('Visualization', level=1); doc.add_picture(plot_buf, width=Inches(5.5))
    doc.add_heading('Interpretation', level=1); doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio

# -----------------------------------------------------------------------------
# 4. 메인 워크플로우
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box"><div class="guide-label">🔒 데이터 보안 안내</div><div class="guide-text">분석 즉시 데이터를 메모리에서 삭제하며, 서버에 저장되지 않습니다.</div></div>
    <div class="guide-box"><div class="guide-label">📄 데이터 형식 가이드</div><div class="guide-text">파일의 첫 번째 행에는 반드시 변수명이 포함되어야 합니다.</div></div>
</div>
""", unsafe_allow_html=True)



up_file = st.file_uploader("Upload Data", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    st.success(f"✔️ {len(df)}건의 데이터가 성공적으로 로드되었습니다.")
    with st.expander("🔍 데이터 미리보기 및 변수 확인"): st.dataframe(df.head(), use_container_width=True)

    st.markdown('<div class="section-title"><span class="step-badge">01</span> 분석 방법 선택</div>', unsafe_allow_html=True)
    method = st.selectbox("수행할 통계 기법을 선택하세요", ["분석 선택 안 함"] + list(METHOD_GUIDES.keys()), label_visibility="collapsed")

    if method != "분석 선택 안 함":
        guide = METHOD_GUIDES[method]
        st.markdown(f"""
        <div class="method-info">
            <div class="method-title">{guide['title']}</div>
            <div class="method-desc">
                {guide['desc']}<br>
                <span class="var-badge">원인변수(IV)</span> {guide['iv']} &nbsp; <span class="var-badge">결과변수(DV)</span> {guide['dv']}<br>
                <b>활용:</b> {guide['use']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        num_cols = df.select_dtypes(include=[np.number]).columns
        final_df, interpretation, plot_img = None, "", None

        if method == "기술통계":
            sel_v = st.multiselect("분석 변수 선택", num_cols)
            if st.button("통계 분석 실행") and sel_v:
                # [업데이트] 건수(N, Count)를 포함한 기술통계 산출
                final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
                final_df.columns = ['Variable', 'N (Count)', 'Mean', 'SD', 'Min', 'Max']
                interpretation = "주요 변수의 기술통계 결과입니다."
                plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v], palette="Set2"); plot_img = get_plot_buffer()

        elif method == "T-test":
            t_mode = st.radio("유형 선택", ["독립표본", "대응표본", "단일표본"], horizontal=True)
            if t_mode == "독립표본":
                g, y = st.selectbox("집단변수 (범주형)", df.columns), st.selectbox("결과변수 (연속형)", num_cols)
                if st.button("분석 실행"):
                    gps = df[g].unique()
                    g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                    t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                    final_df = pd.DataFrame({"Variable": [y], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"검정 결과 p={format_p(p)}이며, 집단 간 평균 차이는 유의미합니다." if p < .05 else f"집단 간 유의미한 차이는 발견되지 않았습니다."
                    plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df, palette="mako"); plot_img = get_plot_buffer()

        elif method == "상관분석":
            v1, v2 = st.selectbox("변수 1 (연속형)", num_cols), st.selectbox("변수 2 (연속형)", num_cols)
            if st.button("분석 실행"):
                r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"Variables": [f"{v1} & {v2}"], "r": [f"{r:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"상관분석 결과 상관계수는 r={r:.2f}로 산출되었습니다."
                plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df, line_kws={'color':'#0d9488'}); plot_img = get_plot_buffer()

        elif method == "회귀분석":
            reg_t = st.radio("분석 유형", ["선형 회귀 (결과가 점수일 때)", "로지스틱 회귀 (결과가 발생여부일 때)"], horizontal=True)
            x_vars = st.multiselect("원인변수(IV) 선택", num_cols)
            y_var = st.selectbox("결과변수(DV) 선택", num_cols)
            if st.button("분석 실행") and x_vars:
                X = sm.add_constant(df[x_vars])
                if "선형" in reg_t:
                    model = sm.OLS(df[y_var], X).fit()
                    final_df = pd.DataFrame({"B": model.params, "SE": model.bse, "t": model.tvalues, "p": model.pvalues}).reset_index()
                    interpretation = f"선형회귀 결과 모델의 설명력은 {model.rsquared:.3f}입니다."
                    plt.figure(figsize=(8, 4)); sns.heatmap(df[x_vars + [y_var]].corr(), annot=True, cmap="YlGnBu"); plot_img = get_plot_buffer()
                else: # 로지스틱 회귀 (OR 및 95% CI 포함)
                    model = sm.Logit(df[y_var], X).fit(disp=0)
                    conf = model.conf_int()
                    final_df = pd.DataFrame({
                        "B": model.params, "OR (Odds Ratio)": np.exp(model.params),
                        "Lower CI": np.exp(conf[0]), "Upper CI": np.exp(conf[1]), "p": model.pvalues
                    }).reset_index()
                    interpretation = f"로지스틱 회귀 결과 모델의 Pseudo R2는 {model.prsquared:.3f}입니다."
                    plt.figure(figsize=(8, 4)); sns.barplot(x=final_df.iloc[1:]['index'], y=final_df.iloc[1:]['OR (Odds Ratio)'], palette="flare"); plot_img = get_plot_buffer()
                final_df['p'] = final_df['p'].apply(lambda x: f"{format_p(x)}{get_stars(x)}")

        if final_df is not None:
            st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 결과 및 리포트</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1.5, 1])
            with c1: st.table(final_df); st.info(f"결과 해석: {interpretation}")
            with c2: 
                if plot_img: st.image(plot_img)
            
            report = create_word_report(final_df, interpretation, plot_img)
            st.download_button("📄 워드 리포트 다운로드", data=report, file_name=f"STATERA_{method}_Report.docx")

else:
    st.markdown("""
    <div class="landing-zone">
        <div style="font-size: 3.5rem; margin-bottom: 20px;">⬆️</div>
        <h3 style="color: #0f172a; margin-bottom: 10px;">분석을 시작하려면 파일을 업로드하세요</h3>
        <p style="color: #64748b;">파일이 로드되면 전문 통계 가이드와 분석 옵션이 활성화됩니다.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #cbd5e1; margin-top: 100px; font-size: 0.8rem;'>Professional Statistical Engine | ANDA Lab Jeongin Choe</div>", unsafe_allow_html=True)
