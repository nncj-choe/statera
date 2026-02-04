import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
import io
import matplotlib.pyplot as plt
import seaborn as sns
import platform
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# -----------------------------------------------------------------------------
# 1. 설정 및 스타일 
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="🎓", layout="wide")

# 한글 폰트 설정
system_name = platform.system()
if system_name == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif system_name == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font=plt.rcParams['font.family'])

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

st.markdown(f"""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * {{ font-family: 'Pretendard', sans-serif; }}
    .main-header {{ color: #0d9488; text-align: center; font-size: 2.8rem; font-weight: 800; margin-bottom: 5px; }}
    .sub-header {{ text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 40px; }}
    .guide-container {{ display: flex; gap: 20px; margin-bottom: 30px; }}
    .guide-box {{ flex: 1; background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }}
    .mentor-box {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
    .assumption-pass {{ background-color: #dcfce7; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #bbf7d0; font-weight: 600; font-size: 0.95rem; }}
    .assumption-fail {{ background-color: #fee2e2; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #fecaca; font-weight: 600; font-size: 0.95rem; }}
    .section-title {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 50px; margin-bottom: 25px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
    .step-badge {{ background: #0d9488; color: white; border-radius: 8px; padding: 4px 15px; font-size: 0.9rem; margin-right: 15px; vertical-align: middle; }}
    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 20px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: #0d9488; color: white; font-weight: 700; height: 3.8em; border: none; transition: 0.4s; }}
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .guide-label {{ font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 8px; }}
    .guide-text {{ font-size: 0.9rem; color: #64748b; line-height: 1.6; }}
    
    /* 테이블 헤더 숨김 처리 */
    thead tr th:first-child {{ display:none }}
    tbody th {{ display:none }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수
# -----------------------------------------------------------------------------
def format_p(p): return "< .001" if p < .001 else f"= {p:.3f}"
def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

def interpret_cohen_d(d):
    d = abs(d)
    if d < 0.2: return "거의 없음 (Negligible)"
    elif d < 0.5: return "작음 (Small)"
    elif d < 0.8: return "중간 (Medium)"
    else: return "큼 (Large)"

def create_pro_report(m_name, r_df, interpretation, plot_b=None, assump_list=None, extra_info=None):
    doc = Document()
    doc.styles['Normal'].font.name = 'Malgun Gothic'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_heading(f'STATERA Report: {m_name}', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 1. Assumption
    doc.add_heading('1. Assumption Checks', level=1)
    if assump_list:
        for msg in assump_list:
            clean = msg.replace('<div class="assumption-pass">', '').replace('<div class="assumption-fail">', '').replace('</div>', '')
            doc.add_paragraph(clean, style='List Bullet')
    else:
        doc.add_paragraph("본 분석에는 별도의 가정 검정이 요구되지 않습니다.")

    # 2. Results
    doc.add_heading('2. Statistical Results', level=1)
    if extra_info: doc.add_paragraph(f"Note: {extra_info}")
    
    if r_df is not None:
        t = doc.add_table(r_df.shape[0]+1, r_df.shape[1]); t.style = 'Table Grid'
        for j, c in enumerate(r_df.columns): t.cell(0,j).text = str(c)
        for i in range(r_df.shape[0]):
            for j in range(r_df.shape[1]): t.cell(i+1,j).text = str(r_df.values[i,j])
            
    # 3. Visualization
    if plot_b:
        doc.add_heading('3. Visualization', level=1)
        doc.add_picture(plot_b, width=Inches(3.8))
    
    # 4. Guide
    doc.add_heading('4. Writing Guide (APA Style)', level=1)
    doc.add_paragraph("※ This guide serves as a scaffold for your manuscript. Please verify and refine.")
    doc.add_paragraph(interpretation.replace("<b>", "").replace("</b>", ""))
    
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

# [Scaffolding 적용]
STAT_MENTOR = {
    "기술통계": {
        "purpose": "수집된 데이터가 전반적으로 어떻게 생겼는지(분포) 요약해서 보여줍니다.",
        "indicator": "평균(Mean)은 중심 위치를, 표준편차(SD)는 데이터가 퍼진 정도를 나타냅니다.",
        "check": "데이터가 종 모양의 정규분포를 따르는지(왜도/첨도) 확인해야 합니다."
    },
    "빈도분석": {
        "purpose": "각 항목(범주)에 응답한 사람이 몇 명이고, 몇 퍼센트인지 확인합니다.",
        "indicator": "빈도(n)와 백분율(%)을 통해 가장 많은/적은 응답이 무엇인지 파악합니다.",
        "check": "응답이 누락된 결측치가 분석에 포함되었는지 확인해야 합니다."
    },
    "카이제곱 검정": {
        "purpose": "두 범주형 변수(예: 성별)가 서로 관련이 있는지, 독립적인지 봅니다.",
        "indicator": "p < 0.05라면 두 변수는 서로 통계적으로 유의한 관련성이 있습니다.",
        "check": "기대빈도가 5보다 작은 셀이 전체의 20%를 넘지 않아야 신뢰할 수 있습니다."
    },
    "단일표본 T-검정": {
        "purpose": "우리 데이터의 평균이 특정 기준값(예: 전국 평균)과 다른지 비교합니다.",
        "indicator": "t값의 절대값이 클수록, p < 0.05일수록 기준값과 확실히 차이가 있다는 뜻입니다.",
        "check": "데이터가 정규분포(종 모양)를 따라야 한다는 가정을 만족해야 합니다."
    },
    "독립표본 T-검정": {
        "purpose": "서로 다른 두 집단(예: 남/녀, 실험군/대조군)의 평균 차이를 비교합니다.",
        "indicator": "Cohen's d는 차이의 크기를 말해줍니다(0.2:작음, 0.5:중간, 0.8:큼).",
        "check": "두 집단의 분산(퍼짐 정도)이 비슷한지(등분산성) 먼저 확인해야 합니다."
    },
    "대응표본 T-검정": {
        "purpose": "같은 집단의 전과 후(예: 교육 전/후) 점수 변화를 비교합니다.",
        "indicator": "변화량의 평균이 0보다 유의하게 큰지/작은지를 p값으로 판단합니다.",
        "check": "'사후 점수 - 사전 점수'의 차이값이 정규분포를 따르는지 확인합니다."
    },
    "분산분석(ANOVA)": {
        "purpose": "세 개 이상의 집단 간에 평균 차이가 존재하는지 한 번에 비교합니다.",
        "indicator": "η²(에타제곱)은 집단 간 차이가 전체 변동의 몇 %를 설명하는지 보여줍니다.",
        "check": "모든 집단의 분산이 비슷해야 하며(등분산성), 잔차가 정규성을 띄어야 합니다."
    },
    "상관분석": {
        "purpose": "두 변수가 함께 증가(양)하거나, 서로 반대 방향으로 움직이는(음) 직선 관계인지 확인합니다.",
        "indicator": "상관계수 r이 +1에 가까우면 강한 양의 관계, -1이면 강한 음의 관계입니다.",
        "check": "두 변수의 관계가 곡선이 아닌 직선 형태인지 산점도로 확인해야 합니다."
    },
    "신뢰도 분석": {
        "purpose": "설문 문항들이 일관성 있게 같은 개념을 측정하고 있는지 평가합니다.",
        "indicator": "Cronbach α가 0.7 이상이면 문항들이 서로 믿을만하다고(일관적) 판단합니다.",
        "check": "점수가 반대인 문항(역코딩)이 제대로 변환되었는지 꼭 확인해야 합니다."
    },
    "회귀분석": {
        "purpose": "원인 변수(X)가 결과 변수(Y)에 얼마나 영향을 미치는지 예측합니다.",
        "indicator": "R²는 설명력을, Beta는 영향력의 강도를 뜻합니다. (p < 0.05여야 유의)",
        "check": "변수끼리 너무 비슷하지 않은지(다중공선성 VIF < 10) 확인해야 합니다."
    }
}

# -----------------------------------------------------------------------------
# 3. 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<h1 style='color:#0d9488;'>STATERA 📊</h1>", unsafe_allow_html=True)
    st.caption(ACRONYM_FULL)
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.info("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 학습 솔루션입니다. 현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("### 📬 Contact & Feedback")
    st.write("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.caption("주소 복사:")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 4. 메인 로직
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">STATERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수치적 결과 산출을 넘어, 연구 논리와 학술적 해석의 과정을 체득하는 통계 학습 플랫폼입니다.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box">
        <div class="guide-label">🔒 데이터 보안 안내</div>
        <div class="guide-text">업로드된 데이터는 분석 즉시 메모리에서 삭제되며 서버에 저장되지 않아 보안이 철저히 유지됩니다.</div>
    </div>
    <div class="guide-box">
        <div class="guide-label">📄 데이터 형식 가이드</div>
        <div class="guide-text">첫 번째 행에는 반드시 변수명이 포함되어야 하며, XLSX 또는 CSV 형식의 파일만 인식 가능합니다.</div>
    </div>
</div>
""", unsafe_allow_html=True)

up_file = st.file_uploader("파일을 업로드하여 분석을 시작하십시오.", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    try:
        df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
        num_cols = df.select_dtypes(include=[np.number]).columns
        all_cols = df.columns
        st.success(f"데이터 로드 완료: 분석 대상 사례 수 N={len(df)}")
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        st.stop()

    # Step 1: 분석 기법 선택
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 연구 목적에 따른 분석 기법 선택</div>', unsafe_allow_html=True)
    group = st.selectbox("분석 범주를 선택하십시오.", [
        "기초 데이터 분석", 
        "집단 간 차이 검정", 
        "관계 및 영향력 분석",
        "척도 신뢰도 분석"
    ])
    
    if "기초" in group: m_list = ["기술통계", "빈도분석"]
    elif "차이" in group: m_list = ["단일표본 T-검정", "독립표본 T-검정", "대응표본 T-검정", "분산분석(ANOVA)"]
    elif "관계" in group: m_list = ["카이제곱 검정", "상관분석", "회귀분석"]
    else: m_list = ["신뢰도 분석"]
    
    method = st.radio("상세 분석 기법 선택", m_list, horizontal=True)
    m_info = STAT_MENTOR[method]
    
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

    # Step 2: 변수 설정 및 실행
    st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 변수 설정 및 실행</div>', unsafe_allow_html=True)
    final_df, p_val, interp, plot_img, assump_report = None, None, "", None, []
    extra_metric_text, anova_info, reg_anova_df = None, None, None

    if method == "기술통계":
        v = st.selectbox("분석할 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            final_df = df[[v]].describe().T.reset_index().rename(columns={
                'index':'Variable (변수명)', 'count':'N (사례수)', 'mean':'Mean (평균)', 'std':'SD (표준편차)',
                'min':'Min (최소)', 'max':'Max (최대)'
            }).round(3)
            skew, kurt = df[v].skew(), df[v].kurt()
            if abs(skew)<3 and abs(kurt)<10: assump_report.append(f'<div class="assumption-pass">✅ 왜도({skew:.2f})/첨도({kurt:.2f}) 기준 충족 (정규성 만족)</div>')
            else: assump_report.append(f'<div class="assumption-fail">⚠️ 왜도/첨도 기준 초과 (정규성 위배 가능성)</div>')
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True, color="#0d9488"); plot_img = get_plot_buffer()
            interp = f"📌 [기술통계 해석 가이드]<br>'{v}' 변수의 평균은 {df[v].mean():.2f}, 표준편차는 {df[v].std():.2f}입니다. 왜도와 첨도가 기준 절대값(왜도<3, 첨도<10) 이내에 있다면 정규분포를 따른다고 가정할 수 있습니다."

    elif method == "빈도분석":
        vs = st.multiselect("분석할 변수들 (범주형)", all_cols)
        if st.button("통계 분석 실행") and vs:
            res = []
            for c in vs:
                counts = df[c].value_counts().reset_index()
                counts.columns = ['Category (범주)', 'Frequency (빈도)']
                counts['Percent (%)'] = (counts['Frequency (빈도)'] / counts['Frequency (빈도)'].sum() * 100).round(1)
                counts.insert(0, 'Variable (변수명)', c); res.append(counts)
            final_df = pd.concat(res); interp = "📌 [빈도분석 해석 가이드]<br>각 범주의 빈도(n)와 비율(%)을 확인하십시오. 비율이 한 쪽으로 지나치게 쏠려 있지 않은지 점검하는 것이 중요합니다."

    elif method == "카이제곱 검정":
        r = st.selectbox("행 변수 (범주형)", all_cols); c = st.selectbox("열 변수 (범주형)", all_cols)
        if st.button("통계 분석 실행"):
            ct = pd.crosstab(df[r], df[c]); chi2, p, _, exp = stats.chi2_contingency(ct)
            p_val = p; final_df = ct.astype(str) + " (" + (ct/ct.sum()*100).round(1).astype(str) + "%)"
            under_5 = (exp < 5).sum(); pct_under_5 = (under_5 / exp.size) * 100
            if pct_under_5 <= 20: assump_report.append(f'<div class="assumption-pass">✅ 기대빈도 가정 충족 (5미만 셀 {pct_under_5:.1f}%)</div>')
            else: assump_report.append(f'<div class="assumption-fail">⚠️ 기대빈도 가정 위배 ({pct_under_5:.1f}% > 20%)</div>')
            
            sig_txt = "유의한 연관성이 있습니다" if p < 0.05 else "유의한 연관성이 없습니다"
            interp = f"📌 [카이제곱 검정 해석]<br>분석 결과, **'{r}'**와 **'{c}'** 변수 간에는 통계적으로 **{sig_txt}** (χ²={chi2:.3f}, p{format_p(p)})."

    elif method == "단일표본 T-검정":
        y = st.selectbox("검정 변수 (연속형)", num_cols); ref = st.number_input("비교할 기준값 (Test Value)", value=0.0)
        if st.button("통계 분석 실행"):
            data = df[y].dropna(); stat, p = stats.ttest_1samp(data, ref); p_val = p
            if stats.shapiro(data)[1] > 0.05: assump_report.append('<div class="assumption-pass">✅ 정규성 가정 충족</div>')
            else: assump_report.append('<div class="assumption-fail">⚠️ 정규성 가정 위배 (비모수 검정 고려)</div>')
            se = data.std(ddof=1) / np.sqrt(len(data)); ci = stats.t.interval(0.95, len(data)-1, loc=data.mean(), scale=se)
            final_df = pd.DataFrame({
                "Dependent Var. (종속변수)":[y], "Test Value (기준값)":[ref], "Mean (평균)":[data.mean()], 
                "t (t값)":[stat], "p (유의확률)":[format_p(p)], "95% CI Lower":[ci[0]], "95% CI Upper":[ci[1]]
            }).round(3)
            
            diff_dir = "높게" if data.mean() > ref else "낮게"
            sig_txt = f"통계적으로 유의하게 {diff_dir} 나타났습니다" if p < 0.05 else "통계적으로 유의한 차이가 없었습니다"
            interp = f"📌 [단일표본 T-검정 해석]<br>표본의 평균({data.mean():.2f})은 기준값({ref})보다 **{sig_txt}** (t={stat:.3f}, p{format_p(p)})."

    elif method == "독립표본 T-검정":
        g = st.selectbox("집단 변수 (범주형: 2집단)", all_cols); y = st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            gps = df[g].unique()
            if len(gps) == 2:
                g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                levene_p = stats.levene(g1, g2)[1]
                equal_var = levene_p > 0.05
                if equal_var: assump_report.append(f'<div class="assumption-pass">✅ 등분산성 충족 (p={levene_p:.3f})</div>')
                else: assump_report.append(f'<div class="assumption-fail">⚠️ 등분산성 위배 (p={levene_p:.3f}) → Welch t-test 수행</div>')
                stat, p = stats.ttest_ind(g1, g2, equal_var=equal_var); p_val = p
                
                n1, n2 = len(g1), len(g2); s_pooled = np.sqrt(((n1-1)*g1.var()+(n2-1)*g2.var())/(n1+n2-2))
                d = abs(g1.mean()-g2.mean())/s_pooled
                cm = sm.stats.CompareMeans(sm.stats.DescrStatsW(g1), sm.stats.DescrStatsW(g2))
                ci = cm.tconfint_diff(usevar='pooled' if equal_var else 'unequal')
                
                final_df = pd.DataFrame({
                    "Grouping Var. (독립변수)": gps, "Mean (평균)": [g1.mean(), g2.mean()], "SD (표준편차)": [g1.std(), g2.std()],
                    "95% CI Lower": [ci[0], ""], "95% CI Upper": [ci[1], ""]
                }).round(3)
                extra_metric_text = f"Effect Size (Cohen's d): {d:.3f} [{interpret_cohen_d(d)}]"
                plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
                
                comp = "높게" if g1.mean() > g2.mean() else "낮게"
                res_txt = f"{gps[0]} 집단(M={g1.mean():.2f})이 {gps[1]} 집단(M={g2.mean():.2f})보다 유의하게 {comp} 나타났습니다" if p < 0.05 else "두 집단 간 유의한 차이가 없었습니다"
                interp = f"📌 [독립표본 T-검정 해석]<br>분석 결과, **{res_txt}** (t={stat:.3f}, p{format_p(p)}). 효과 크기(Cohen's d)는 {d:.2f}로 {interpret_cohen_d(d)} 수준입니다."

    elif method == "대응표본 T-검정":
        y1 = st.selectbox("사전 변수 (연속형)", num_cols); y2 = st.selectbox("사후 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            tmp = df[[y1, y2]].dropna(); diff = tmp[y2] - tmp[y1]
            stat, p = stats.ttest_rel(tmp[y1], tmp[y2]); p_val = p
            if stats.shapiro(diff)[1] > 0.05: assump_report.append('<div class="assumption-pass">✅ 차이값 정규성 충족</div>')
            else: assump_report.append('<div class="assumption-fail">⚠️ 정규성 위배 (Wilcoxon 권장)</div>')
            se = diff.std(ddof=1)/np.sqrt(len(diff))
            ci = stats.t.interval(0.95, len(diff)-1, loc=diff.mean(), scale=se)
            final_df = pd.DataFrame({
                "Pair (변수쌍)": [f"{y1}-{y2}"], "Mean Diff (평균차이)": [diff.mean()], "t (t값)": [stat], "p (유의확률)": [format_p(p)],
                "95% CI Lower": [ci[0]], "95% CI Upper": [ci[1]]
            }).round(3)
            
            change = "증가" if diff.mean() > 0 else "감소"
            sig_txt = f"통계적으로 유의하게 {change}했습니다" if p < 0.05 else "통계적으로 유의한 변화가 없었습니다"
            interp = f"📌 [대응표본 T-검정 해석]<br>사후 점수는 사전 점수에 비해 **{sig_txt}** (t={stat:.3f}, p{format_p(p)})."

    elif method == "분산분석(ANOVA)":
        g = st.selectbox("집단 변수 (범주형: 3집단 이상)", all_cols); y = st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            # 데이터 전처리 및 모델링
            sub_df = df[[g, y]].dropna()
            model = ols(f'Q("{y}") ~ C(Q("{g}"))', data=sub_df).fit()
            res = anova_lm(model, typ=2); p_val = res.iloc[0,3]
            
            # 가정 검정
            resid = model.resid
            if len(resid) >= 3:
                _, p_norm = stats.shapiro(resid)
                if p_norm > 0.05: assump_report.append(f'<div class="assumption-pass">✅ 잔차 정규성 충족 (p={p_norm:.3f})</div>')
                else: assump_report.append(f'<div class="assumption-fail">⚠️ 잔차 정규성 위배 (p={p_norm:.3f})</div>')
            
            grps = [sub_df[sub_df[g]==k][y] for k in sub_df[g].unique()]
            _, p_levene = stats.levene(*grps)
            if p_levene > 0.05: assump_report.append(f'<div class="assumption-pass">✅ 등분산성 충족 (p={p_levene:.3f})</div>')
            else: assump_report.append(f'<div class="assumption-fail">⚠️ 등분산성 위배 (p={p_levene:.3f})</div>')

            # 결과 정리
            eta = model.rsquared; es_eval = "Large" if eta > 0.14 else "Medium" if eta > 0.06 else "Small"
            anova_info = f"- **Effect Size (η²):** {eta:.3f} ({es_eval})"
            
            final_df = res.reset_index().rename(columns={'index':'Source (변동원)', 'PR(>F)':'p (유의확률)'}).round(3)
            
            # Writing Guide (Scaffolded)
            df1, df2 = int(res.iloc[0,1]), int(res.iloc[1,1]); f_val = res.iloc[0,2]
            sig_txt = "통계적으로 유의한 차이가 있었습니다" if p_val < 0.05 else "통계적으로 유의한 차이가 없었습니다"
            interp = (f"📌 [ANOVA 해석 가이드]<br>"
                      f"일원배치 분산분석 결과, 집단 간 **{y}**의 평균은 **{sig_txt}** "
                      f"(F({df1}, {df2}) = {f_val:.3f}, p {format_p(p_val)}). "
                      f"효과 크기(η²)는 {eta:.3f}로 **{es_eval}** 수준입니다.")
            
            if p_val < 0.05:
                tukey = pairwise_tukeyhsd(sub_df[y], sub_df[g]); st.info("💡 사후검정(Tukey) 결과"); st.text(str(tukey))

    elif method == "상관분석":
        vs = st.multiselect("분석할 변수군 선택 (연속형)", num_cols)
        if st.button("통계 분석 실행") and len(vs)>=2:
            corr_m = df[vs].corr().round(3)
            p_m = pd.DataFrame([[format_p(stats.pearsonr(df[i].dropna(), df[j].dropna())[1]) if i!=j else "-" for j in vs] for i in vs], index=vs, columns=vs)
            final_df = corr_m.astype(str) + " (p=" + p_m.astype(str) + ")"
            plt.figure(figsize=(6,5)); sns.heatmap(corr_m, annot=True, cmap="coolwarm"); plot_img = get_plot_buffer()
            interp = "📌 [상관분석 해석]<br>상관계수(r)가 0.7 이상이면 강한 양의 상관, -0.7 이하이면 강한 음의 상관관계가 있다고 해석합니다. p < .05 인 경우 해당 관계는 통계적으로 유의합니다."

    elif method == "신뢰도 분석":
        vs = st.multiselect("신뢰도 분석할 문항군 선택 (연속형)", num_cols)
        if st.button("통계 분석 실행") and len(vs)>=2:
            it = df[vs].dropna(); k = it.shape[1]; alpha = (k/(k-1)) * (1 - (it.var(ddof=1).sum() / it.sum(axis=1).var(ddof=1)))
            final_df = pd.DataFrame({"Cronbach α (계수)": [f"{alpha:.3f}"]})
            rel_txt = "매우 양호" if alpha > 0.8 else "양호" if alpha > 0.7 else "부족"
            interp = f"📌 [신뢰도 해석]<br>Cronbach's α 계수는 **{alpha:.3f}**로, 도구의 신뢰도는 **'{rel_txt}'**한 수준입니다."

    elif method == "회귀분석":
        rtype = st.radio("회귀 유형", ["선형 회귀분석 (Linear)", "로지스틱 회귀분석 (Logistic)"])
        xs = st.multiselect("독립변수군 (연속형/더미)", num_cols); y = st.selectbox("종속변수", num_cols)
        if st.button("통계 분석 실행") and xs:
            reg_d = df[list(xs)+[y]].dropna(); X = sm.add_constant(reg_d[xs])
            if "선형" in rtype:
                model = sm.OLS(reg_d[y], X).fit(); p_val = model.f_pvalue
                beta = model.params[1:] * (reg_d[xs].std() / reg_d[y].std())
                conf = model.conf_int(); conf.columns = ['Lower', 'Upper']
                
                vifs = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
                if max(vifs[1:]) < 10: assump_report.append(f'<div class="assumption-pass">✅ 다중공선성 없음 (Max VIF={max(vifs[1:]):.2f})</div>')
                else: assump_report.append(f'<div class="assumption-fail">⚠️ 다중공선성 경고 (Max VIF={max(vifs[1:]):.2f})</div>')
                dw = durbin_watson(model.resid)
                assump_report.append(f'<div class="{"assumption-pass" if 1.5<dw<2.5 else "assumption-fail"}">✅ 잔차 독립성 (DW={dw:.2f})</div>')
                
                st.info(f"🎯 분석 대상 종속변수(Dependent Variable): {y}")
                final_df = pd.DataFrame({
                    "Predictor (독립변수)": ["(Constant)"] + list(xs), "B (비표준화 계수)": model.params.values,
                    "Beta (표준화 계수)": [np.nan] + list(beta.values), "p (유의확률)": model.pvalues.apply(format_p).values,
                    "95% CI Lower": conf['Lower'], "95% CI Upper": conf['Upper']
                }).round(3).reset_index(drop=True)
                
                reg_anova_df = pd.DataFrame({"Source": ["Regression", "Residual"], "df": [model.df_model, model.df_resid], "F": [model.fvalue, ""]})
                if len(xs)==1: 
                    plt.figure(figsize=(6,5)); sns.regplot(x=reg_d[xs[0]], y=reg_d[y], line_kws={"color":"red"}); plot_img = get_plot_buffer()
                else:
                    plt.figure(figsize=(6,5)); plt.scatter(model.fittedvalues, model.resid); plt.title("Residual vs Fitted"); plot_img = get_plot_buffer()
                
                sig_txt = "유의하게 설명하고 있습니다" if p_val < 0.05 else "유의하게 설명하지 못하고 있습니다"
                interp = f"📌 [회귀분석 해석]<br>회귀모형은 종속변수({y})를 통계적으로 **{sig_txt}** (F={model.fvalue:.3f}, p{format_p(p_val)}). 모델의 설명력(R²)은 **{model.rsquared:.3f}**입니다."
            else:
                if reg_d[y].dtype == 'object':
                    from sklearn.preprocessing import LabelEncoder
                    le = LabelEncoder(); reg_d[y] = le.fit_transform(reg_d[y])
                    st.warning(f"ℹ️ 종속변수 '{y}'가 텍스트여서 0과 1로 변환했습니다.")

                model = sm.Logit(reg_d[y], X).fit(disp=False); p_val = model.llr_pvalue
                final_df = pd.DataFrame({
                    "Predictor (독립변수)": model.params.index, "B (Coeff)": model.params.values, 
                    "OR (Odds Ratio)": np.exp(model.params.values), "p (Sig)": model.pvalues.apply(format_p).values
                }).round(3).reset_index(drop=True)
                interp = f"📌 [로지스틱 회귀 해석]<br>모형의 유의확률은 **p{format_p(p_val)}**입니다. OR(오즈비)이 1보다 크면 해당 변수가 증가할수록 사건 발생 확률이 높아짐을 의미합니다."

    # --- Step 03: 결과 대시보드 ---
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">03</span> 분석 결과 요약 및 학술적 해석</div>', unsafe_allow_html=True)
        if assump_report:
            with st.expander("🔍 필수 가정 검정 (Assumption Check) 결과 확인", expanded=True):
                for m in assump_report: st.markdown(m, unsafe_allow_html=True)
        
        st.markdown("###")
        col_main_L, col_main_R = st.columns([1.3, 1]) 
        
        with col_main_L:
            if reg_anova_df is not None:
                st.markdown("##### 📊 분산분석표 (ANOVA Table)")
                st.dataframe(reg_anova_df, use_container_width=True, hide_index=True)
            st.markdown("##### 📋 통계량 상세표")
            st.dataframe(final_df, use_container_width=True, hide_index=True)
            if anova_info: st.info(f"📊 모형 요약 정보\n{anova_info}")
            
        with col_main_R:
            st.markdown("##### 💡 Writing Guide")
            st.caption("아래 문구는 학술적 기술을 돕기 위한 비계(Scaffolding)입니다. 연구자의 고찰을 담아 수정하여 사용하십시오.")
            
            status_bg = "#dcfce7" if (p_val is not None and p_val < 0.05) else "#f1f5f9"
            st.markdown(f"""
            <div style="background-color: {status_bg}; padding: 20px; border-radius: 12px; border: 1px solid #cbd5e1; margin-bottom: 15px;">
                <div style="font-size: 0.95rem; color: #475569; line-height: 1.6;">{interp}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if extra_metric_text and "분산분석" not in method:
                st.markdown(f"""
                <div style="background-color: #f0fdfa; padding: 15px; border-radius: 10px; border: 1px solid #ccfbf1; margin-top: 10px;">
                    <div style="font-size: 0.9rem; color: #0f766e; font-weight: 700;">📌 {extra_metric_text}</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("") 
            st.download_button(
                label="📄 워드 리포트 다운로드",
                data=create_pro_report(method, final_df, interp, plot_b=plot_img, assump_list=assump_report, extra_info=extra_metric_text),
                file_name=f"STATERA_{method}.docx",
                use_container_width=True, 
                type="primary"
            )

        if plot_img:
            st.markdown("###")
            st.markdown("##### 📊 시각화 결과")
            st.image(plot_img, use_container_width=True)

# -----------------------------------------------------------------------------
# 5. 연구 윤리 가이드 
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="ethics-container">
    <div class="ethics-title">⚠️ 연구 윤리 가이드</div>
    <div class="ethics-text">
        1. 본 서비스에서 산출된 결과는 유의수준 0.05를 기준으로 한 통계적 판정입니다.<br>
        2. 제공된 'Writing Guide'는 결과(Results)의 객관적 서술을 돕기 위한 템플릿이며, 고찰(Discussion)은 연구자가 직접 작성해야 합니다.
    </div>
</div>
<div style='text-align: center; color: #cbd5e1; margin-top: 20px; font-size: 0.8rem;'>
    STATERA | ANDA Lab | nncj91@snu.ac.kr
</div>
""", unsafe_allow_html=True)
