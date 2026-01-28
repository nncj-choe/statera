import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor
import io
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

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
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {{ font-family: 'Pretendard', sans-serif; }}
    .main-header {{ color: #0d9488; text-align: center; font-size: 3.5rem; font-weight: 800; margin-bottom: 0px; letter-spacing: -1.5px; }}
    .acronym-header {{ text-align: center; color: #64748b; font-size: 1rem; font-weight: 400; margin-bottom: 40px; text-transform: uppercase; letter-spacing: 2px; }}
    
    .guide-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
    .guide-box {{ flex: 1; background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }}
    .guide-label {{ font-size: 1.15rem; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
    .guide-text {{ font-size: 0.95rem; color: #64748b; line-height: 1.6; }}

    .section-title {{ font-size: 1.5rem; font-weight: 800; color: #0f172a; margin-top: 40px; margin-bottom: 20px; display: flex; align-items: center; }}
    .step-badge {{ background: #0d9488; color: white; border-radius: 8px; padding: 2px 12px; font-size: 0.9rem; margin-right: 12px; }}

    .method-info {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
    .method-title {{ color: #0f766e; font-size: 1.3rem; font-weight: 700; margin-bottom: 10px; }}
    .method-desc {{ color: #1e293b; font-size: 1rem; line-height: 1.7; }}
    .var-badge {{ background-color: #ccfbf1; color: #0f766e; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; margin-right: 8px; }}

    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .ethics-title {{ color: #c2410c; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }}
    .ethics-text {{ color: #9a3412; font-size: 0.9rem; line-height: 1.6; }}

    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 15px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; font-weight: 700; height: 3.5em; border: none; font-size: 1rem; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h1 style='color:#0d9488; font-size: 2rem;'>STATERA 📊</h1>", unsafe_allow_html=True)
    st.caption(ACRONYM_FULL)
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.info("""
    본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다.
    
    현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.
    """)
    st.markdown("---")
    st.markdown("### 📬 Contact & Feedback")
    st.write("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.caption("주소 복사:")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 3. 통계 보조 함수 및 가이드 데이터
# -----------------------------------------------------------------------------
METHOD_GUIDES = {
    "기술통계": {"title": "📈 기술통계", "desc": "평균, 표준편차, 왜도, 첨도 등을 산출하여 정규성을 파악합니다.", "독립": "N/A", "종속": "연속형", "use": "데이터 요약"},
    "빈도분석": {"title": "📊 빈도분석", "desc": "범주형 변수의 빈도와 백분율을 산출합니다.", "독립": "N/A", "종속": "범주형", "use": "인구통계적 특성"},
    "카이제곱 검정": {"title": "🎲 카이제곱 및 Fisher", "desc": "범주형 변수 간 연관성 및 기대빈도 검정", "독립": "범주형", "종속": "범주형", "use": "그룹 간 연관성"},
    "T-검정": {"title": "👥 T-검정", "desc": "두 집단 간 평균 차이 및 효과크기를 분석합니다.", "독립": "범주형(2집단)", "종속": "연속형", "use": "성별 간 점수 비교"},
    "분산분석(ANOVA)": {"title": "🏫 ANOVA & 사후검정", "desc": "세 집단 이상 평균 차이 및 사후 검정을 수행합니다.", "독립": "범주형(3+)", "종속": "연속형", "use": "학력별 점수 차이"},
    "상관분석": {"title": "🔗 상관분석", "desc": "변수 간 선형적 관련성의 강도를 분석합니다.", "독립": "연속형", "종속": "연속형", "use": "변수 간 상관성"},
    "신뢰도 분석": {"title": "📏 신뢰도 분석", "desc": "측정 도구의 내적 일관성(Cronbach's α)을 산출합니다.", "독립": "다수문항", "종속": "N/A", "use": "도구 신뢰도 검증"},
    "회귀분석": {"title": "🎯 회귀분석", "desc": "독립변수의 영향력, 모형 적합도, 오즈비(OR) 등을 분석합니다.", "독립": "연속/범주", "종속": "연속/이분형", "use": "영향 요인 분석"}
}

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"
def get_stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""

def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

def create_pro_report(m_name, r_df, guide, plot_b=None, assump=""):
    doc = Document(); doc.styles['Normal'].font.name = 'Malgun Gothic'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_heading(f'STATERA Report: {m_name}', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    if assump: doc.add_heading('1. Assumption Checks', level=1); doc.add_paragraph(assump).italic = True
    doc.add_heading('2. Statistical Results', level=1)
    t = doc.add_table(r_df.shape[0]+1, r_df.shape[1]); t.style = 'Table Grid'
    for j, c in enumerate(r_df.columns): t.cell(0,j).text = str(c)
    for i in range(r_df.shape[0]):
        for j in range(r_df.shape[1]): t.cell(i+1,j).text = str(r_df.values[i,j])
    if plot_b: doc.add_heading('3. Plot', level=1); doc.add_picture(plot_b, width=Inches(4.5))
    doc.add_heading('4. Thesis Writing Guide', level=1); doc.add_paragraph(guide)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

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
    num_cols = df.select_dtypes(include=[np.number]).columns
    all_cols = df.columns
    st.success(f"데이터 로드 완료: N={len(df)}")

    # Step 01: 분석 방법 선택
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 분석 방법 선택</div>', unsafe_allow_html=True)
    group = st.radio("분석 단계를 선택하세요", ["기초 분석", "차이 검정", "관계 및 신뢰도", "영향력 분석"], horizontal=True)
    
    if "기초" in group: m_list = ["기술통계", "빈도분석"]
    elif "차이" in group: m_list = ["카이제곱 검정", "T-검정", "분산분석(ANOVA)"]
    elif "관계" in group: m_list = ["상관분석", "신뢰도 분석"]
    else: m_list = ["회귀분석"]
    
    method = st.radio("상세 기법 선택", m_list, horizontal=True)
    g_info = METHOD_GUIDES[method]
    st.markdown(f'<div class="method-info"><div class="method-title">{g_info["title"]}</div><div class="method-desc">{g_info["desc"]}<br><span class="var-badge">독립</span> {g_info["독립"]} &nbsp; <span class="var-badge">종속</span> {g_info["종속"]}</div></div>', unsafe_allow_html=True)

    final_df, interpretation, plot_img, assump_text = None, "", None, ""

    # 분석 로직 
    if method == "기술통계":
        v = st.selectbox("변수", num_cols)
        if st.button("실행"):
            final_df = df[[v]].describe().T.reset_index().round(3)
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True, color="#0d9488"); plot_img = get_plot_buffer()
            interpretation = f"📌 {v}의 평균은 {df[v].mean():.2f}(SD={df[v].std():.2f})입니다."

    elif method == "빈도분석":
        vs = st.multiselect("변수", all_cols)
        if st.button("실행") and vs:
            res = [df[c].value_counts().reset_index().rename(columns={'index':'범주', c:'n'}) for c in vs]
            for i, c in enumerate(vs): res[i]['%'] = (res[i]['n']/len(df)*100).round(1); res[i].insert(0, '변수', c)
            final_df = pd.concat(res)
            interpretation = "범주별 빈도와 비율을 확인하십시오."

    elif method == "카이제곱 검정":
        r, c = st.selectbox("행", all_cols), st.selectbox("열", all_cols)
        if st.button("실행"):
            ct = pd.crosstab(df[r], df[c]); ct_pct = pd.crosstab(df[r], df[c], normalize='columns').mul(100).round(1)
            final_df = ct.astype(str) + " (" + ct_pct.astype(str) + "%)"
            chi2, p, dof, exp = stats.chi2_contingency(ct)
            exp_p = (exp < 5).sum()/exp.size*100
            assump_text = f"기대빈도 5 미만 셀 비율: {exp_p:.1f}%"
            interpretation = f"📌 분석 결과 연관성이 {'유의하게 확인되었습니다' if p < 0.05 else '유의하지 않습니다'} (χ²={chi2:.3f}, p={format_p(p)})."
            if exp_p > 20: 
                _, f_p = stats.fisher_exact(ct) if ct.shape == (2,2) else (0,0)
                if f_p > 0: st.info(f"Fisher's Exact p: {format_p(f_p)}")
            plt.figure(figsize=(6,4)); sns.heatmap(ct, annot=True, fmt='d', cmap="YlGnBu"); plot_img = get_plot_buffer()

    elif method == "T-검정":
        g, y = st.selectbox("집단", all_cols), st.selectbox("결과", num_cols)
        if st.button("실행") and len(df[g].unique()) == 2:
            g1, g2 = df[df[g]==df[g].unique()[0]][y].dropna(), df[df[g]==df[g].unique()[1]][y].dropna()
            stat, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2)[1] > 0.05)
            final_df = pd.DataFrame({"t": [stat], "p": [format_p(p)+get_stars(p)]})
            interpretation = f"📌 두 집단 간 평균 차이가 {'유의합니다' if p < 0.05 else '유의하지 않습니다'} (t={stat:.3f}, p={format_p(p)})."
            plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()

    elif method == "분산분석(ANOVA)":
        g, y = st.selectbox("집단", all_cols), st.selectbox("결과", num_cols)
        if st.button("실행"):
            model = ols(f'{y} ~ C({g})', data=df).fit(); res = anova_lm(model, typ=2)
            final_df = res.reset_index().round(3); p = res.iloc[0,3]
            interpretation = f"📌 집단 간 차이가 {'유의합니다' if p < 0.05 else '유의하지 않습니다'} (F={res.iloc[0,2]:.3f}, p={format_p(p)})."
            if p < 0.05: st.text(str(pairwise_tukeyhsd(df[y].dropna(), df[g].dropna())))
            plt.figure(figsize=(6,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()

    elif method == "상관분석":
        vs = st.multiselect("변수", num_cols)
        if st.button("실행") and len(vs) >= 2:
            final_df = df[vs].corr().round(3)
            plt.figure(figsize=(8,6)); sns.heatmap(final_df, annot=True, cmap="coolwarm"); plot_img = get_plot_buffer()
            interpretation = "변수 간 상관관계의 방향과 강도를 확인하십시오."

    elif method == "신뢰도 분석":
        vs = st.multiselect("문항", num_cols)
        if st.button("실행") and len(vs) > 1:
            it = df[vs].dropna(); k = it.shape[1]; alpha = (k/(k-1))*(1-(it.var(ddof=1).sum()/it.sum(axis=1).var(ddof=1)))
            final_df = pd.DataFrame({"Cronbach α": [f"{alpha:.3f}"]})
            interpretation = f"📌 도구의 신뢰도는 {alpha:.3f}로 {'적절합니다' if alpha >= 0.7 else '낮은 편입니다'}."

    elif method == "회귀분석":
        xs, y = st.multiselect("독립", num_cols), st.selectbox("종속", num_cols)
        if st.button("실행") and xs:
            res = sm.OLS(df[y], sm.add_constant(df[xs])).fit()
            final_df = pd.DataFrame({"B": res.params, "p": res.pvalues}).reset_index().round(3)
            interpretation = f"📌 모델의 설명력은 {res.rsquared*100:.1f}%이며, 유의성 p={format_p(res.f_pvalue)}입니다."
            plt.figure(figsize=(6,4)); sns.regplot(x=xs[0], y=y, data=df); plot_img = get_plot_buffer()

    # Step 02: 결과 및 리포트 
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 결과 및 리포트</div>', unsafe_allow_html=True)
        if assump_text: st.warning(f"🔍 가정 검정: {assump_text}")
        c1, c2 = st.columns([1.5, 1])
        with c1: 
            st.table(final_df); st.info(interpretation)
        with c2: 
            if plot_img: st.image(plot_img)
        st.download_button("📄 리포트 다운로드", create_pro_report(method, final_df, interpretation, plot_b=plot_img, assump=assump_text), f"STATERA_{method}.docx")

# 하단 연구 윤리 안내
st.markdown(f"""
<div class="ethics-container">
    <div class="ethics-title">⚠️ 분석 결과 해석 시 유의사항</div>
    <div class="ethics-text">
        1. 본 서비스에서 제공하는 자동 해석 문구는 유의수준 0.05를 기준으로 산출된 기계적 판정 결과입니다.<br>
        2. 연구자는 통계적 유의성(p-value)뿐만 아니라, 연구 목적에 따른 실질적/임상적 의미를 반드시 함께 고려해야 합니다.<br>
        3. 최종 보고서 작성 시 본 해석의 정확성을 검토할 책임은 연구자 본인에게 있습니다.<br>
        4. 데이터의 정규성, 등분산성 등 통계적 기본 가정이 충족되었는지 사전에 확인하시기 바랍니다.
    </div>
</div>
<div style='text-align: center; color: #cbd5e1; margin-top: 20px; font-size: 0.8rem;'>
    STATistical Engine for Research & Analysis | ANDA Lab Jeongin Choe
</div>
""", unsafe_allow_html=True)
