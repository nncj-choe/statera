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

# 그래프 한글 및 스타일 설정
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

    .method-info {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 20px; border-radius: 8px; margin-bottom: 25px; }}
    .method-title {{ color: #0f766e; font-size: 1.3rem; font-weight: 700; margin-bottom: 10px; }}
    .method-desc {{ color: #1e293b; font-size: 1rem; line-height: 1.7; }}
    .var-badge {{ background-color: #ccfbf1; color: #0f766e; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; margin-right: 8px; }}

    .assumption-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; font-size: 0.95rem; color: #334155; line-height: 1.6; margin-bottom: 15px; }}
    
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .ethics-title {{ color: #c2410c; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }}
    .ethics-text {{ color: #9a3412; font-size: 0.9rem; line-height: 1.6; }}

    .stButton>button {{ width: 100%; border-radius: 12px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; font-weight: 700; height: 3.5em; border: none; font-size: 1rem; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 분석 가이드 데이터 (Methodology & Writing Guides)
# -----------------------------------------------------------------------------
METHOD_GUIDES = {
    "기술통계": {
        "title": "📈 기술통계 (Descriptive Statistics)",
        "desc": "연속형 변수의 평균, 표준편차, 왜도, 첨도 등을 산출하여 데이터의 전반적인 경향을 파악합니다.",
        "독립": "해당 없음", "종속": "연속형 변수", "use": "연구 대상자의 주요 수치형 지표를 요약할 때 사용합니다."
    },
    "빈도분석": {
        "title": "📊 빈도분석 (Frequency Analysis)",
        "desc": "범주형 변수의 빈도, 백분율, 누적 비율을 산출하여 대상자의 분포를 확인합니다.",
        "독립": "해당 없음", "종속": "범주형 변수", "use": "성별, 학력 등 대상자의 일반적 특성을 보고할 때 사용합니다."
    },
    "카이제곱 검정": {
        "title": "🎲 카이제곱 검정 (Chi-square Test)",
        "desc": "두 범주형 변수 간의 연관성 및 기대빈도 가정을 검정합니다.",
        "독립": "범주형", "종속": "범주형", "use": "집단별 속성 차이(예: 성별에 따른 흡연 유무)를 확인할 때 사용합니다."
    },
    "T-검정": {
        "title": "👥 T-검정 (T-test)",
        "desc": "두 집단 간 평균 차이와 효과크기(Cohen's d)를 분석합니다.",
        "독립": "범주형 (2집단)", "종속": "연속형 변수", "use": "두 그룹 간의 결과값 차이를 비교하고 싶을 때 사용합니다."
    },
    "분산분석(ANOVA)": {
        "title": "🏫 분산분석 (ANOVA) & 사후검정",
        "desc": "세 개 이상의 그룹 간 평균 차이와 사후 검정(Tukey HSD)을 수행합니다.",
        "독립": "범주형 (3집단 이상)", "종속": "연속형 변수", "use": "학력이나 연령대별 점수 차이 분석 시 사용합니다."
    },
    "상관분석": {
        "title": "🔗 상관분석 (Correlation Analysis)",
        "desc": "변수 간의 선형적 관련성(Pearson's r)의 강도를 분석합니다.",
        "독립": "연속형", "종속": "연속형", "use": "변수들 간의 관계성을 종합적으로 보고할 때 사용합니다."
    },
    "신뢰도 분석": {
        "title": "📏 신뢰도 분석 (Reliability Analysis)",
        "desc": "측정 도구의 문항 간 내적 일관성(Cronbach's α)을 산출합니다.",
        "독립": "다수 문항", "종속": "해당 없음", "use": "설문지 문항들이 일관되게 측정하고 있는지 확인합니다."
    },
    "회귀분석": {
        "title": "🎯 회귀분석 (Regression Analysis)",
        "desc": "독립변수의 영향력, 모형 적합도, 오즈비(OR) 등을 산출합니다.",
        "독립": "연속형/범주형", "종속": "연속형/이분형", "use": "요인이 결과에 미치는 영향력을 수치화할 때 사용합니다."
    }
}

WRITING_GUIDES = {
    "기술통계": "[본문 기술 예시] 대상자의 주요 변수를 분석한 결과, [변수명]의 평균은 M=00.00(SD=00.00)으로 나타났으며 정규성 가정을 충족하였다.",
    "빈도분석": "[본문 기술 예시] 대상자의 일반적 특성을 분석한 결과, 성별은 여성이 n=00(00.0%)으로 가장 높은 비중을 차지하였다.",
    "카이제곱 검정": "[본문 기술 예시] 변수 A와 B 간의 연관성을 분석한 결과, 통계적으로 유의한 관련성이 확인되었다(χ²=00.00, p<.05).",
    "T-검정": "[본문 기술 예시] 두 집단 간의 평균 차이를 분석한 결과, A집단(M=00, SD=00)이 B집단보다 유의하게 높았다(t=00.00, p=.000).",
    "분산분석(ANOVA)": "[본문 기술 예시] 집단 간 차이는 통계적으로 유의하였으며(F=00.00, p=.000), 사후 검정 결과 A집단이 가장 높은 것으로 나타났다.",
    "상관분석": "[본문 기술 예시] 변수 A와 B 간에는 유의한 양(+)의 상관관계가 확인되었다(r=.00, p<.05).",
    "신뢰도 분석": "[본문 기술 예시] 연구 도구의 신뢰도를 분석한 결과, Cronbach's α 계수는 .000으로 내적 일관성이 적절한 것으로 확인되었다.",
    "회귀분석": "[본문 기술 예시] 회귀모형의 설명력은 00.0%이며 모형은 유의하였다(F=00.00, p=.000). [변수A](β=.00, p<.05)가 주요 요인이었다."
}

# -----------------------------------------------------------------------------
# 3. 유틸리티 및 통계 함수
# -----------------------------------------------------------------------------
def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"

def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

def cronbach_alpha(df):
    df_item = df.dropna(); item_vars = df_item.var(ddof=1)
    total_var = df_item.sum(axis=1).var(ddof=1); k = df_item.shape[1]
    return (k / (k - 1)) * (1 - (item_vars.sum() / total_var))

def create_final_report(method_name, results_df, interpretation, guide, table_num="Table 1", plot_buf=None, assumption=""):
    doc = Document()
    doc.styles['Normal'].font.name = 'Malgun Gothic'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_heading(f'Statistical Analysis Report: {method_name}', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Table Number: {table_num}").alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if assumption:
        doc.add_heading('1. Assumption Checks', level=1); doc.add_paragraph(assumption).italic = True
    doc.add_heading('2. Statistical Results', level=1)
    table = doc.add_table(rows=results_df.shape[0] + 1, cols=results_df.shape[1]); table.style = 'Table Grid'
    for j, col in enumerate(results_df.columns): table.cell(0, j).text = str(col)
    for i in range(results_df.shape[0]):
        for j in range(results_df.shape[1]): table.cell(i+1, j).text = str(results_df.values[i, j])
    if plot_buf:
        doc.add_heading('3. Visualization', level=1); doc.add_picture(plot_buf, width=Inches(4.5))
    doc.add_heading('4. Thesis Writing Guide', level=1); doc.add_paragraph(guide)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

# -----------------------------------------------------------------------------
# 4. 메인 어플리케이션 레이아웃
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

# 상단 가이드 박스
st.markdown(f"""
<div class="guide-container">
    <div class="guide-box"><div class="guide-label">🔒 데이터 보안 안내</div><div class="guide-text">분석 즉시 데이터를 메모리에서 삭제하며, 서버에 저장되지 않습니다.</div></div>
    <div class="guide-box"><div class="guide-label">📄 데이터 형식 가이드</div><div class="guide-text">파일의 첫 번째 행에는 반드시 변수명이 포함되어야 시스템이 인식합니다.</div></div>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("<h1 style='color:#0d9488; font-size: 2rem;'>STATERA 📊</h1>", unsafe_allow_html=True)
    st.caption(ACRONYM_FULL)
    st.markdown("---")
    st.markdown("### 🚧 Research Beta Version")
    st.info("본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다. 현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.")
    st.markdown("---")
    st.markdown("### 🛠️ Analysis Steps")
    group = st.radio("Select Analysis Group", ["Step 1. 기초 분석", "Step 2. 차이 검정", "Step 3. 관계 및 신뢰도", "Step 4. 영향력 분석"])
    
    if group == "Step 1. 기초 분석":
        method = st.selectbox("Detailed Method", ["기술통계", "빈도분석"])
    elif group == "Step 2. 차이 검정":
        method = st.selectbox("Detailed Method", ["카이제곱 검정", "T-검정", "분산분석(ANOVA)"])
    elif group == "Step 3. 관계 및 신뢰도":
        method = st.selectbox("Detailed Method", ["상관분석", "신뢰도 분석"])
    else:
        method = st.selectbox("Detailed Method", ["회귀분석"])
    
    st.markdown("---")
    st.markdown("### 📬 Contact & Feedback")
    st.write("오류 제보 및 기능 제안은 언제나 환영합니다.")
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

up_file = st.file_uploader("Upload Data", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    num_cols = df.select_dtypes(include=[np.number]).columns; all_cols = df.columns
    st.success(f"데이터 로드 완료: 분석 대상 사례 수 N={len(df)}")
    
    # [방법론 가이드 블록]
    guide_info = METHOD_GUIDES[method]
    st.markdown(f"""
    <div class="method-info">
        <div class="method-title">{guide_info['title']}</div>
        <div class="method-desc">
            {guide_info['desc']}<br>
            <span class="var-badge">독립 변수</span> {guide_info['독립']} &nbsp; <span class="var-badge">종속 변수</span> {guide_info['종속']}<br>
            <b>활용 예시:</b> {guide_info['use']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    final_df, interpretation, plot_img, assumption_text = None, "", None, ""

    # --- Step 1: 기초 분석 ---
    if method == "기술통계":
        sel_v = st.selectbox("분석할 연속형 변수 선택", num_cols)
        if st.button("Run Analysis"):
            final_df = df[[sel_v]].describe().T.reset_index().round(3)
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            sns.histplot(df[sel_v].dropna(), kde=True, ax=ax[0], color="#0d9488")
            sm.qqplot(df[sel_v].dropna(), line='s', ax=ax[1]); plot_img = get_plot_buffer()
            interpretation = "왜도와 첨도가 학술적 기준 내에 있는지 시각적으로 확인하십시오."

    elif method == "빈도분석":
        sel_v = st.multiselect("범주형 변수 선택", all_cols)
        if st.button("Run Analysis") and sel_v:
            res = [df[c].value_counts().reset_index().rename(columns={'index':'Category', c:'N'}) for c in sel_v]
            for i, c in enumerate(sel_v): res[i]['%'] = (res[i]['N'] / len(df) * 100).round(1); res[i].insert(0, 'Variable', c)
            final_df = pd.concat(res)

    # --- Step 2: 차이 검정 ---
    elif method == "카이제곱 검정":
        r, c = st.selectbox("Row (행)", all_cols), st.selectbox("Column (열)", all_cols)
        if st.button("Run Analysis"):
            ct = pd.crosstab(df[r], df[c]); chi2, p, dof, exp = stats.chi2_contingency(ct)
            exp_pct = (exp < 5).sum() / exp.size * 100
            final_df = pd.DataFrame({"Statistic": ["Pearson Chi2", "p-value", "Exp<5 Ratio"], "Value": [f"{chi2:.3f}", f"{format_p(p)}{get_stars(p)}", f"{exp_pct:.1f}%"]})
            if ct.shape == (2,2): st.info(f"Fisher's Exact p: {format_p(stats.fisher_exact(ct)[1])}")
            plt.figure(figsize=(6, 4)); sns.heatmap(ct, annot=True, fmt='d', cmap="YlGnBu"); plot_img = get_plot_buffer()
            assumption_text = f"기대빈도 5 미만 셀 비율: {exp_pct:.1f}% (기준: 20% 이하)"

    elif method == "T-검정":
        g, y = st.selectbox("집단 변수 (2집단)", all_cols), st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("Run Analysis") and len(df[g].unique()) == 2:
            g1, g2 = df[df[g]==df[g].unique()[0]][y].dropna(), df[df[g]==df[g].unique()[1]][y].dropna()
            stat, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2)[1] > 0.05)
            final_df = pd.DataFrame({"t-value": [stat], "p-value": [format_p(p)+get_stars(p)]})
            plt.figure(figsize=(5, 4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()

    elif method == "분산분석(ANOVA)":
        g, y = st.selectbox("집단 변수 (3집단 이상)", all_cols), st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("Run Analysis"):
            model = ols(f'{y} ~ C({g})', data=df).fit(); final_df = anova_lm(model, typ=2).reset_index()
            if final_df.iloc[0, 3] < 0.05:
                st.markdown("**[Post-hoc: Tukey HSD]**")
                st.text(str(pairwise_tukeyhsd(df[y].dropna(), df[g].dropna())))
            plt.figure(figsize=(7, 4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()

    # --- Step 3: 관계 및 신뢰도 ---
    elif method == "상관분석":
        sel_v = st.multiselect("변수 선택 (2개 이상)", num_cols)
        if st.button("Run Analysis") and len(sel_v) >= 2:
            final_df = df[sel_v].corr().round(3); plt.figure(figsize=(8, 6)); sns.heatmap(final_df, annot=True, cmap="RdBu_r", vmin=-1, vmax=1); plot_img = get_plot_buffer()

    elif method == "신뢰도 분석":
        sel_v = st.multiselect("문항 선택", num_cols)
        if st.button("Run Analysis") and len(sel_v) > 1:
            alpha = cronbach_alpha(df[sel_v]); st.metric("Cronbach's α", f"{alpha:.3f}"); final_df = pd.DataFrame({"Index": ["Alpha"], "Value": [f"{alpha:.3f}"]})

    # --- Step 4: 영향력 분석 ---
    elif method == "회귀분석":
        rtype = st.radio("회귀 유형 선택", ["Linear Regression", "Logistic Regression"])
        xs, y = st.multiselect("독립변수(들)", num_cols), st.selectbox("종속변수", num_cols)
        if st.button("Run Analysis") and xs:
            X = sm.add_constant(df[xs])
            if "Linear" in rtype:
                res = sm.OLS(df[y], X).fit(); final_df = pd.DataFrame({"B": res.params, "p": res.pvalues}).reset_index()
            else:
                res = sm.Logit(df[y], X).fit(); final_df = pd.DataFrame({"OR": np.exp(res.params), "p": res.pvalues}).reset_index()
                plt.figure(figsize=(6, 4)); plt.errorbar(np.exp(res.params)[1:], range(len(xs)), xerr=0.1, fmt='o', color='#0d9488'); plt.axvline(1, color='red', ls='--'); plt.yticks(range(len(xs)), xs); plot_img = get_plot_buffer()

    # 공통 결과 출력
    if final_df is not None:
        st.markdown("### 📊 Result Table"); st.table(final_df)
        report_bio = create_final_report(method, final_df, interpretation, WRITING_GUIDES.get(method, ""), plot_buf=plot_img, assumption=assumption_text)
        st.download_button("📄 Download Professional Word Report", data=report_bio, file_name=f"STATERA_{method}.docx")

else:
    st.markdown('<div style="text-align:center; padding:100px; color:#64748b;">데이터 파일을 업로드하면 STATERA의 분석 엔진이 활성화됩니다.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 5. 연구 윤리 안내 및 하단 푸터
# -----------------------------------------------------------------------------
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
