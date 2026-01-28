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
st.set_page_config(page_title="STATERA", page_icon="🎓", layout="wide")

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

st.markdown(f"""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {{ font-family: 'Pretendard', sans-serif; }}
    .main-header {{ color: #0d9488; text-align: center; font-size: 2.8rem; font-weight: 800; margin-bottom: 5px; }}
    .sub-header {{ text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 40px; }}
    
    .guide-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
    .guide-box {{ flex: 1; background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); }}
    .guide-label {{ font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 8px; display: flex; align-items: center; }}
    .guide-text {{ font-size: 0.9rem; color: #64748b; line-height: 1.6; }}

    .mentor-box {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
    .mentor-title {{ color: #0f766e; font-size: 1.3rem; font-weight: 700; margin-bottom: 12px; }}
    .mentor-content {{ color: #1e293b; font-size: 1rem; line-height: 1.8; }}

    .section-title {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 50px; margin-bottom: 25px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; display: flex; align-items: center; }}
    .step-badge {{ background: #0d9488; color: white; border-radius: 8px; padding: 4px 15px; font-size: 0.9rem; margin-right: 15px; vertical-align: middle; }}

    .assumption-box {{ background-color: #f8fafc; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; margin-bottom: 20px; font-size: 0.95rem; line-height: 1.6; }}
    .interpretation-box {{ background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 25px; border-radius: 15px; font-size: 1.1rem; line-height: 1.7; color: #1e40af; }}
    
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .ethics-title {{ color: #c2410c; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }}
    .ethics-text {{ color: #9a3412; font-size: 0.9rem; line-height: 1.6; }}

    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 20px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: #0d9488; color: white; font-weight: 700; height: 3.8em; border: none; transition: 0.4s; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 통계 유틸리티 및 가이드 데이터
# -----------------------------------------------------------------------------
def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"
def get_stars(p): return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""
def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

STAT_MENTOR = {
    "기술통계": {"purpose": "연속형 변수의 중심 경향성과 분포 특성을 요약합니다.", "indicator": "평균은 자료의 수준을, 표준편차는 자료의 산포 정도를 나타냅니다.", "check": "왜도와 첨도를 통해 정규분포 가정을 검토하십시오."},
    "빈도분석": {"purpose": "범주형 변수의 빈도와 비율을 통해 인구통계적 특성을 파악합니다.", "indicator": "사례 수(n)와 유효 백분율(%)을 산출하여 제시합니다.", "check": "결측치가 전체 비중에 미치는 영향을 확인하십시오."},
    "카이제곱 검정": {"purpose": "두 범주형 변수 간의 통계적 관련성 유무를 확인합니다.", "indicator": "기대빈도 5 미만 셀 비율에 따라 Pearson 또는 Fisher 검정을 선택합니다.", "check": "교차표의 기대빈도 가정이 충족되는지 검토하십시오."},
    "단일표본 T-검정": {"purpose": "한 집단의 평균을 특정 기준값과 비교합니다.", "indicator": "표본 평균이 설정된 기준치와 유의미하게 차이가 나는지 판정합니다.", "check": "집단의 정규성 가정을 사전에 확인하십시오."},
    "독립표본 T-검정": {"purpose": "서로 독립적인 두 집단 간의 평균 차이를 비교 분석합니다.", "indicator": "t값과 유의확률을 통해 집단 간 차이의 유의성을 판정합니다.", "check": "두 집단의 정규성과 등분산성 가정을 확인하십시오."},
    "대응표본 T-검정": {"purpose": "동일 집단의 처치 전후(사전-사후) 평균 변화를 비교합니다.", "indicator": "사전-사후 점수 차이의 평균이 0과 다른지 검증합니다.", "check": "사전-사후 차이값의 정규성 분포를 검토하십시오."},
    "분산분석(ANOVA)": {"purpose": "세 집단 이상의 평균 차이를 비교하고 변량 차이를 분석합니다.", "indicator": "F값으로 유의성을 판정한 후 Tukey 등으로 사후분석을 수행합니다.", "check": "집단별 정규성과 등분산성 가정을 확인하십시오."},
    "상관분석": {"purpose": "두 연속형 변수 간의 직선적인 관계의 강도를 파악합니다.", "indicator": "상관계수(r)를 통해 변수 간 관계의 방향과 밀접도를 평가합니다.", "check": "변수 간의 관계가 선형적인지 산점도를 검토하십시오."},
    "신뢰도 분석": {"purpose": "측정 도구의 문항들이 얼마나 일관성 있게 측정되는지 평가합니다.", "indicator": "Cronbach α 계수가 0.7 이상일 때 신뢰도가 확보된 것으로 간주합니다.", "check": "역코딩 문항이 분석 전 적절히 변환되었는지 확인하십시오."},
    "회귀분석": {"purpose": "독립변수가 종속변수에 미치는 인과관계와 영향력을 분석합니다.", "indicator": "R2로 모형 설명력을, Beta로 영향력의 크기를 평가합니다.", "check": "다중공선성(VIF < 10)과 잔차의 독립성을 확인하십시오."}
}

# -----------------------------------------------------------------------------
# 3. 사이드바 및 메인 레이아웃
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h1 style='color:#0d9488;'>STATERA 📊</h1>", unsafe_allow_html=True)
    st.caption(ACRONYM_FULL)
    st.markdown("---")
    st.markdown("### 🚧 Research Beta")
    st.info("학생들의 연구 역량 강화를 위해 개발된 웹 기반 통계 솔루션입니다. 
    
            현재 알고리즘 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("### 📬 Contact")
    st.code("nncj91@snu.ac.kr", language="text")
    st.caption("Developed by ANDA Lab | Jeongin Choe")

st.markdown('<div class="main-header">STATERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수치적 정확성과 학술적 해석의 논리를 동시에 제공하는 연구용 통계 솔루션입니다.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box">
        <div class="guide-label">🔒 데이터 보안 안내</div>
        <div class="guide-text">업로드된 데이터는 분석 즉시 메모리에서 삭제되며 서버에 저장되지 않아 보안이 유지됩니다.</div>
    </div>
    <div class="guide-box">
        <div class="guide-label">📄 데이터 형식 가이드</div>
        <div class="guide-text">첫 행에는 반드시 변수명이 포함되어야 하며 XLSX 또는 CSV 형식을 권장합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

up_file = st.file_uploader("파일을 업로드하여 분석을 시작하십시오.", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    num_cols = df.select_dtypes(include=[np.number]).columns; all_cols = df.columns
    st.success(f"데이터 로드 완료: N={len(df)}")

    # Step 01: 기법 선택
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 분석 목적 및 기법 선택</div>', unsafe_allow_html=True)
    group = st.selectbox("분석 범주를 선택하십시오.", ["기초 데이터 분석", "집단 간 차이 검정", "상관성 및 인과관계 규명"])
    
    if "기초" in group: m_list = ["기술통계", "빈도분석", "카이제곱 검정"]
    elif "차이" in group: m_list = ["단일표본 T-검정", "독립표본 T-검정", "대응표본 T-검정", "분산분석(ANOVA)"]
    else: m_list = ["상관분석", "신뢰도 분석", "회귀분석"]
    
    method = st.radio("상세 분석 기법 선택", m_list, horizontal=True)
    m_info = STAT_MENTOR.get(method.split(" ")[0]) if " " in method else STAT_MENTOR.get(method)
    
    st.markdown(f"""
    <div class="mentor-box">
        <div class="mentor-title">👨‍🏫 {method} 학술 가이드</div>
        <div class="mentor-content">
            <b>분석 목적:</b> {m_info['purpose']}<br>
            <b>핵심 지표 해석:</b> {m_info['indicator']}<br>
            <b>데이터 점검 사항:</b> {m_info['check']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Step 02: 변수 선택 및 실행
    st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 변수 설정 및 실행</div>', unsafe_allow_html=True)
    final_df, p_val, interp, plot_img, assump_report = None, None, "", None, []

    if method == "기술통계":
        v = st.selectbox("연속형 변수", num_cols)
        if st.button("통계 분석 실행"):
            final_df = df[[v]].describe().T.reset_index().round(2)
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True); plot_img = get_plot_buffer()
            interp = f"📌 {v}의 평균은 {df[v].mean():.2f}(SD={df[v].std():.2f})입니다."

    elif method == "빈도분석":
        vs = st.multiselect("범주형 변수", all_cols)
        if st.button("통계 분석 실행") and vs:
            res = []
            for c in vs:
                counts = df[c].value_counts().reset_index(); counts.columns = ['범주', 'n']
                counts['%'] = (counts['n'] / counts['n'].sum() * 100).round(1)
                counts.insert(0, '변수명', c); res.append(counts)
            final_df = pd.concat(res); interp = "대상자 분포를 확인하십시오."

    elif method == "카이제곱 검정":
        r, c = st.selectbox("행 변수", all_cols), st.selectbox("열 변수", all_cols)
        if st.button("통계 분석 실행"):
            ct = pd.crosstab(df[r], df[c]); chi2, p, _, exp = stats.chi2_contingency(ct)
            assump_report.append(f"기대빈도 5 미만 비율: {(exp < 5).sum()/exp.size*100:.1f}%")
            final_df = ct.astype(str) + " (" + (ct/ct.sum()*100).round(1).astype(str) + "%)"
            p_val = p; interp = f"📌 {r}와 {c} 간 연관성 유의확률: p={format_p(p)}"

    elif method == "단일표본 T-검정":
        y = st.selectbox("검정 변수", num_cols); ref_v = st.number_input("기준값", value=0.0)
        if st.button("통계 분석 실행"):
            data = df[y].dropna(); _, sp = stats.shapiro(data)
            assump_report.append(f"정규성 검정 (Shapiro-Wilk): p={format_p(sp)}")
            stat, p = stats.ttest_1samp(data, ref_v); p_val = p
            final_df = pd.DataFrame({"방법": [method], "t값": [stat], "p값": [format_p(p)]})
            interp = f"📌 {y}의 평균과 기준값 간의 차이는 {'유의합니다' if p < 0.05 else '유의하지 않습니다'}."

    elif method == "독립표본 T-검정":
        g, y = st.selectbox("집단 변수(2분류)", all_cols), st.selectbox("검정 변수", num_cols)
        if st.button("통계 분석 실행") and len(df[g].unique()) == 2:
            gps = df[g].unique(); g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
            _, lp = stats.levene(g1, g2); assump_report.append(f"등분산성 검정 (Levene): p={format_p(lp)}")
            stat, p = stats.ttest_ind(g1, g2, equal_var=(lp >= 0.05)); p_val = p
            final_df = pd.DataFrame({"방법": [method], "t값": [stat], "p값": [format_p(p)]})
            plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
            interp = f"📌 집단 간 {y}의 차이는 {'유의합니다' if p < 0.05 else '유의하지 않습니다'}."

    elif method == "대응표본 T-검정":
        y1, y2 = st.selectbox("사전 변수", num_cols), st.selectbox("사후 변수", num_cols)
        if st.button("통계 분석 실행"):
            diff = df[y2] - df[y1]; _, sp = stats.shapiro(diff.dropna())
            assump_report.append(f"차이값 정규성 검정: p={format_p(sp)}")
            stat, p = stats.ttest_rel(df[y1].dropna(), df[y2].dropna()); p_val = p
            final_df = pd.DataFrame({"방법": [method], "t값": [stat], "p값": [format_p(p)]})
            interp = f"📌 사전 대비 사후의 수치 변화는 {'유의합니다' if p < 0.05 else '유의하지 않습니다'}."

    elif method == "분산분석(ANOVA)":
        g, y = st.selectbox("집단 변수(3분류+)", all_cols), st.selectbox("검정 변수", num_cols)
        if st.button("통계 분석 실행"):
            model = ols(f'{y} ~ C({g})', data=df).fit(); res = anova_lm(model, typ=2); p_val = res.iloc[0,3]
            final_df = res.reset_index().round(3)
            if p_val < 0.05: st.text(str(pairwise_tukeyhsd(df[y].dropna(), df[g].dropna())))
            interp = f"📌 집단 간 차이 유의성 p={format_p(p_val)}"

    elif method == "상관분석":
        sel_vs = st.multiselect("변수군 선택", num_cols)
        if st.button("통계 분석 실행") and len(sel_vs) >= 2:
            final_df = df[sel_vs].corr().round(3)
            plt.figure(figsize=(7,5)); sns.heatmap(final_df, annot=True, cmap="coolwarm"); plot_img = get_plot_buffer()
            interp = "변수 간 선형적 상관계수 행렬입니다."

    elif method == "신뢰도 분석":
        sel_items = st.multiselect("문항군 선택", num_cols)
        if st.button("통계 분석 실행") and len(sel_items) >= 2:
            items = df[sel_items].dropna(); k = items.shape[1]
            alpha = (k/(k-1)) * (1 - (items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1)))
            final_df = pd.DataFrame({"지표": ["Cronbach α"], "수치": [f"{alpha:.3f}"]})
            interp = f"📌 신뢰도 계수는 {alpha:.3f}로 확인되었습니다."

    elif method == "회귀분석":
        rtype = st.radio("회귀 유형", ["선형 회귀분석 (Linear)", "로지스틱 회귀분석 (Logistic)"])
        xs, y = st.multiselect("독립변수군", num_cols), st.selectbox("종속변수", num_cols)
        if st.button("통계 분석 실행") and xs:
            if "선형" in rtype:
                X = sm.add_constant(df[xs]); model = sm.OLS(df[y], X).fit(); p_val = model.f_pvalue
                vifs = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
                assump_report.append(f"최대 VIF: {max(vifs):.2f}")
                final_df = pd.DataFrame({"B": model.params, "p": model.pvalues}).reset_index().round(3)
                interp = f"📌 R2={model.rsquared:.3f}, 모델 유의성 p={format_p(p_val)}"
            else:
                X = sm.add_constant(df[xs]); model = sm.Logit(df[y], X).fit(); p_val = model.llr_pvalue
                final_df = pd.DataFrame({"OR": np.exp(model.params), "p": model.pvalues}).reset_index().round(3)
                interp = f"📌 로지스틱 모형 유의성 p={format_p(p_val)}"

    # --- Step 03: 결과 대시보드 ---
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">03</span> 분석 결과 요약 및 학술적 해석</div>', unsafe_allow_html=True)
        if assump_report:
            with st.expander("🔍 필수 가정 검정 결과", expanded=True):
                for msg in assump_report: st.markdown(f'<div class="assumption-box">{msg}</div>', unsafe_allow_html=True)
        
        if p_val is not None:
            if p_val < 0.05: st.success(f"✅ 분석 결과가 통계적으로 유의미합니다. (p={format_p(p_val)})")
            else: st.error(f"❌ 분석 결과가 통계적으로 유의미하지 않습니다. (p={format_p(p_val)})")

        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.table(final_df); st.markdown(f'<div class="interpretation-box">{interp}</div>', unsafe_allow_html=True)
        with c2:
            if plot_img: st.image(plot_img)
            st.info("💡 학술적 조언: 가정 검정이 위배된 경우 비모수 통계 활용을 권장합니다.")

st.markdown(f"""
<div class="ethics-container">
    <div class="ethics-title">⚠️ 연구자 유의사항</div>
    <div class="ethics-text">
        1. 본 서비스의 결과는 유의수준 0.05를 기준으로 한 기계적 판정입니다.<br>
        2. 최종 분석 결과의 정확성을 검토할 책임은 연구자 본인에게 있습니다.
    </div>
</div>
<div style='text-align: center; color: #cbd5e1; margin-top: 20px; font-size: 0.8rem;'>
    STATistical Engine for Research & Analysis | ANDA Lab | nncj91@snu.ac.kr
</div>
""", unsafe_allow_html=True)
