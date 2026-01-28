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
# 1. UI 스타일링: 전문성과 신뢰감을 주는 학술적 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA: 학술 통계 가이드", page_icon="🎓", layout="wide")

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

st.markdown(f"""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {{ font-family: 'Pretendard', sans-serif; }}
    .main-header {{ color: #0d9488; text-align: center; font-size: 2.8rem; font-weight: 800; margin-bottom: 5px; }}
    .sub-header {{ text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 40px; }}
    
    .mentor-box {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
    .mentor-title {{ color: #0f766e; font-size: 1.3rem; font-weight: 700; margin-bottom: 12px; }}
    .mentor-content {{ color: #1e293b; font-size: 1rem; line-height: 1.8; }}

    .section-title {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 50px; margin-bottom: 25px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
    .step-badge {{ background: #0d9488; color: white; border-radius: 8px; padding: 4px 15px; font-size: 0.9rem; margin-right: 15px; vertical-align: middle; }}

    .interpretation-box {{ background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 25px; border-radius: 15px; font-size: 1.1rem; line-height: 1.7; color: #1e40af; }}
    .tip-box {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 18px; margin-top: 15px; color: #9a3412; font-size: 0.95rem; }}
    
    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 20px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: #0d9488; color: white; font-weight: 700; height: 3.8em; border: none; transition: 0.4s; }}
    .stButton>button:hover {{ background: #0f766e; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3); }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 학술 멘토링 데이터: 정제된 전문 용어 반영
# -----------------------------------------------------------------------------
STAT_MENTOR = {
    "기술통계": {
        "purpose": "연구 대상자의 주요 변수들이 가진 수치적 특성을 요약하고 정규성 분포를 확인합니다.",
        "indicator": "평균은 데이터의 중심 경향성을, 표준편차는 평균을 중심으로 한 자료의 산포도를 나타냅니다.",
        "data_check": "왜도와 첨도 수치를 통해 데이터가 정규분포 가정을 충족하는지 검토하십시오."
    },
    "빈도분석": {
        "purpose": "성별, 학력 등 명목척도로 측정된 변수들의 빈도와 상대적 비중을 파악합니다.",
        "indicator": "각 범주에 해당하는 사례 수(n)와 전체 대비 백분율(%)을 산출하여 대상자 분포를 제시합니다.",
        "data_check": "누락된 데이터(결측치)가 결과값의 비중에 영향을 주지 않는지 확인하십시오."
    },
    "카이제곱 검정": {
        "purpose": "두 범주형 변수 간의 독립성 및 통계적인 관련성 여부를 검정합니다.",
        "indicator": "교차표의 기대빈도가 5 미만인 셀이 전체의 20%를 초과할 경우 Fisher의 정확 검정 결과를 보고하십시오.",
        "data_check": "변수 간의 선후 관계보다는 두 속성 간의 결합 분포에 집중하여 해석하십시오."
    },
    "T-검정": {
        "purpose": "두 집단 간의 평균값 차이가 우연에 의한 것인지, 통계적으로 유의미한 수준인지 비교합니다.",
        "indicator": "유의확률(p)이 0.05 미만일 때 집단 간 평균 차이가 유의미하다고 해석합니다.",
        "data_check": "Levene의 검정을 통해 두 집단의 분산이 동일한지(등분산성) 먼저 확인하십시오."
    },
    "분산분석(ANOVA)": {
        "purpose": "세 개 이상의 집단 간 평균값 차이를 비교하고, 집단 간 변량의 차이를 분석합니다.",
        "indicator": "전체적인 차이가 유의할 경우, 구체적으로 어느 집단 간에 차이가 있는지 사후분석(Post-hoc)을 수행합니다.",
        "data_check": "각 집단별 사례 수가 최소 3개 이상 확보되었는지 확인하십시오."
    },
    "상관분석": {
        "purpose": "두 연속형 변수 간의 직선적인 관계가 얼마나 밀접하게 나타나는지 그 방향성과 강도를 확인합니다.",
        "indicator": "상관계수(r)는 -1에서 1 사이의 값을 가지며, 절대값이 클수록 관계의 강도가 높음을 의미합니다.",
        "data_check": "두 변수의 관계가 높더라도 이것이 반드시 직접적인 인과관계를 의미하지는 않음에 유의하십시오."
    },
    "신뢰도 분석": {
        "purpose": "동일한 개념을 측정하는 문항들이 얼마나 일관성 있게 구성되었는지 내적 일관성을 평가합니다.",
        "indicator": "Cronbach's alpha 계수가 0.7 이상일 때 측정 도구의 신뢰도가 확보된 것으로 간주합니다.",
        "data_check": "부정문이나 역코딩 문항이 분석 전에 적절히 변환되었는지 재확인하십시오."
    },
    "회귀분석": {
        "purpose": "독립변수가 종속변수에 미치는 영향력을 수치화하여 인과관계의 모형을 검증합니다.",
        "indicator": "결정계수(R²)는 모형의 설명력을, 표준화 계수(Beta)는 영향력의 상대적 크기를 나타냅니다.",
        "data_check": "독립변수들 간의 강한 상관관계로 인한 다중공선성(VIF < 10) 문제가 없는지 검토하십시오."
    }
}

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"
def get_stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

# -----------------------------------------------------------------------------
# 3. 사이드바: 연구자를 위한 브랜딩 및 안내
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h2 style='color:#0d9488;'>STATERA MENTOR</h2>", unsafe_allow_html=True)
    st.caption("STATistical Engine for Research & Analysis")
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.info("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다. 현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("### 📬 도움말 및 오류제보")
    st.write("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 4. 메인 어플리케이션 레이아웃
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">STATERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">데이터 분석의 수치적 정확성과 학술적 해석의 논리를 동시에 제공합니다.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box"><div class="guide-label">🔒 데이터 보안 안내</div><div class="guide-text">분석 즉시 데이터를 메모리에서 삭제하며, 서버에 저장되지 않습니다.</div></div>
    <div class="guide-box"><div class="guide-label">📄 데이터 형식 가이드</div><div class="guide-text">파일의 첫 번째 행에는 반드시 변수명이 포함되어야 시스템이 인식합니다.</div></div>
</div>
""", unsafe_allow_html=True)

up_file = st.file_uploader("XLSX 또는 CSV 파일을 업로드하여 분석을 시작하십시오.", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    num_cols = df.select_dtypes(include=[np.number]).columns; all_cols = df.columns
    st.success(f"데이터 로드 완료: 분석 대상 사례 수 N={len(df)}")

    # Step 01: 분석 목적 및 기법 선택
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 연구 목적에 따른 분석 기법 선택</div>', unsafe_allow_html=True)
    group = st.selectbox("수행하고자 하는 분석의 범주를 선택하십시오.", 
                        ["대상자의 일반적 특성 요약 (기초분석)", "집단 간 평균 및 속성 차이 비교 (차이검정)", "변수 간 상관성 및 인과관계 규명 (관계/회귀)"])
    
    if "기초" in group: m_list = ["기술통계", "빈도분석"]
    elif "차이" in group: m_list = ["T-검정", "분산분석(ANOVA)", "카이제곱 검정"]
    else: m_list = ["상관분석", "신뢰도 분석", "회귀분석"]
    
    method = st.radio("상세 분석 기법을 선택하십시오.", m_list, horizontal=True)

    # 정제된 언어의 멘토링 박스 노출
    m_guide = STAT_MENTOR.get(method)
    st.markdown(f"""
    <div class="mentor-box">
        <div class="mentor-title">👨‍🏫 {method} 분석 가이드</div>
        <div class="mentor-content">
            <b>분석 목적:</b> {m_guide['purpose']}<br>
            <b>핵심 지표 해석:</b> {m_guide['indicator']}<br>
            <b>데이터 점검 사항:</b> {m_guide['data_check']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 02: 변수 선택 및 실행
    st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 변수 설정 및 실행</div>', unsafe_allow_html=True)
    final_df, p_val, interp, plot_img, assump_text = None, None, "", None, ""

    if method == "기술통계":
        v = st.selectbox("연속형 변수 선택", num_cols)
        if st.button("통계 분석 실행"):
            final_df = df[[v]].describe().T.reset_index().rename(columns={'index':'변수명'}).round(2)
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True, color="#0d9488"); plot_img = get_plot_buffer()
            interp = f"📌 {v}의 평균은 {df[v].mean():.2f}(SD={df[v].std():.2f})이며, 최소값 {df[v].min():.2f}에서 최대값 {df[v].max():.2f}의 분포를 보입니다."

    elif method == "빈도분석":
        vs = st.multiselect("범주형 변수 선택", all_cols)
        if st.button("통계 분석 실행") and vs:
            res = []
            for c in vs:
                counts = df[c].value_counts().reset_index(); counts.columns = ['범주', 'n']
                counts['%'] = (counts['n'] / counts['n'].sum() * 100).round(1)
                counts.insert(0, '변수명', c); res.append(counts)
            final_df = pd.concat(res); interp = "대상자의 특성별 빈도(n)와 비율(%) 분포입니다. 논문의 Table 1 구성에 활용하십시오."

    elif method == "카이제곱 검정":
        r, c = st.selectbox("행 변수 (특성)", all_cols), st.selectbox("열 변수 (집단)", all_cols)
        if st.button("통계 분석 실행"):
            ct = pd.crosstab(df[r], df[c]); chi2, p, dof, exp = stats.chi2_contingency(ct)
            ct_pct = pd.crosstab(df[r], df[c], normalize='columns').mul(100).round(1)
            final_df = ct.astype(str) + " (" + ct_pct.astype(str) + "%)"
            p_val = p; exp_p = (exp < 5).sum()/exp.size*100; assump_text = f"기대빈도 5 미만 셀 비율: {exp_p:.1f}%"
            sig_res = "통계적으로 유의미한 관련성이 확인되었습니다" if p < 0.05 else "통계적으로 유의미한 관련성이 확인되지 않았습니다"
            interp = f"📌 {r}와 {c} 간의 연관성을 분석한 결과, {sig_res}. (chi-square={chi2:.3f}, p={format_p(p)})"
            plt.figure(figsize=(6,4)); sns.heatmap(ct, annot=True, fmt='d', cmap="YlGnBu"); plot_img = get_plot_buffer()

    elif method == "T-검정":
        g, y = st.selectbox("집단 변수 (2분류)", all_cols), st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행") and len(df[g].unique()) == 2:
            gps = df[g].unique(); g1 = df[df[g]==gps[0]][y].dropna(); g2 = df[df[g]==gps[1]][y].dropna()
            stat, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2)[1] > 0.05)
            final_df = pd.DataFrame({"방법": ["독립표본 T-검정"], "t-value": [stat], "p-value": [format_p(p)]}).round(3)
            p_val = p; higher = gps[0] if g1.mean() > g2.mean() else gps[1]
            sig_res = "통계적으로 유의미한 차이가 확인되었습니다" if p < 0.05 else "통계적으로 유의미한 차이가 확인되지 않았습니다"
            interp = f"📌 {g}에 따른 {y}의 평균 차이를 분석한 결과, {higher} 집단의 점수가 상대적으로 높으며 이 차이는 {sig_res}. (p={format_p(p)})"
            plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df, palette="mako"); plot_img = get_plot_buffer()

    elif method == "회귀분석":
        rtype = st.radio("분석 유형", ["선형 회귀분석 (연속형 종속변수)", "로지스틱 회귀분석 (이분형 종속변수)"])
        xs, y = st.multiselect("독립변수군 선택", num_cols), st.selectbox("종속변수 선택", num_cols)
        if st.button("통계 분석 실행") and xs:
            if "선형" in rtype:
                res = sm.OLS(df[y], sm.add_constant(df[xs])).fit(); p_val = res.f_pvalue
                final_df = pd.DataFrame({"B": res.params, "p-value": res.pvalues}).reset_index().round(3)
                interp = f"📌 회귀모형의 설명력(R²)은 {res.rsquared:.3f}이며, 모형의 통계적 유의성은 p={format_p(p_val)}입니다."
            else:
                res = sm.Logit(df[y], sm.add_constant(df[xs])).fit(); p_val = res.llr_pvalue
                final_df = pd.DataFrame({"OR": np.exp(res.params), "p-value": res.pvalues}).reset_index().round(3)
                interp = f"📌 로지스틱 회귀모형의 유의성 검정 결과 p={format_p(p_val)}로 확인되었습니다."

    # Step 03: 결과 대시보드
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">03</span> 통계 결과 요약 및 해석 가이드</div>', unsafe_allow_html=True)
        
        if p_val is not None:
            if p_val < 0.05:
                st.markdown(f'<div class="result-pass">✅ 분석 결과가 유의수준 0.05에서 통계적으로 유의미합니다. (p={format_p(p_val)})</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-fail">❌ 분석 결과가 유의수준 0.05에서 통계적으로 유의미하지 않습니다. (p={format_p(p_val)})</div>', unsafe_allow_html=True)
        
        if assump_text: st.warning(f"🔍 통계적 가정 검정 결과: {assump_text}")

        c_res, c_viz = st.columns([1.5, 1])
        with c_res:
            st.write("📊 분석 결과 수치")
            st.table(final_df)
            st.markdown(f'<div class="interpretation-box">{interp}</div>', unsafe_allow_html=True)
        with c_viz:
            if plot_img: st.write("📈 결과 시각화 자료"); st.image(plot_img)
            st.markdown("""<div class="tip-box"><b>💡 학술적 기술 팁</b><br>통계적 유의성(p)이 확보된 변수는 논문 본문에서 그 임상적/실무적 의미를 함께 기술하는 것이 중요합니다.</div>""", unsafe_allow_html=True)

else:
    st.markdown('<div style="text-align:center; padding:100px; color:#64748b;">데이터를 업로드하면 STATERA의 학술 통계 멘토링이 활성화됩니다.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 연구 윤리 안내 및 하단 푸터
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="ethics-container">
    <div class="ethics-title">⚠️ 연구자 유의사항</div>
    <div class="ethics-text">
        1. 본 서비스에서 산출된 결과는 유의수준 0.05를 기준으로 한 통계적 판정입니다.<br>
        2. 통계적 유의성만으로 연구의 모든 결론을 도출하기보다, 선행 연구 및 이론적 배경과 연계하여 해석하십시오.<br>
        3. 최종 분석 결과의 정확성을 검토하고 보고서를 작성할 책임은 연구자 본인에게 있습니다.
    </div>
</div>
<div style='text-align: center; color: #cbd5e1; margin-top: 20px; font-size: 0.8rem;'>
    STATistical Engine for Research & Analysis | ANDA Lab | nncj91@snu.ac.kr
</div>
""", unsafe_allow_html=True)
