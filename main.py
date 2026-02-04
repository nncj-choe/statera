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

    .assumption-pass {{ background-color: #dcfce7; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #bbf7d0; font-weight: 600; font-size: 0.95rem; }}
    .assumption-fail {{ background-color: #fee2e2; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #fecaca; font-weight: 600; font-size: 0.95rem; }}
    
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .ethics-title {{ color: #c2410c; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }}
    .ethics-text {{ color: #9a3412; font-size: 0.9rem; line-height: 1.6; }}

    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 20px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: #0d9488; color: white; font-weight: 700; height: 3.8em; border: none; transition: 0.4s; }}
    
    thead tr th:first-child {{ display:none }}
    tbody th {{ display:none }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 통계 멘토 가이드 데이터 및 유틸리티
# -----------------------------------------------------------------------------
def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"
def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

STAT_MENTOR = {
    "기술통계": {"purpose": "데이터의 중심 경향성과 분포 특성을 요약합니다.", "indicator": "평균은 자료의 수준을, 표준편차는 산포 정도를 나타냅니다.", "check": "왜도와 첨도를 통해 정규분포 가정을 검토하십시오."},
    "빈도분석": {"purpose": "범주형 변수의 빈도와 비율을 파악합니다.", "indicator": "사례 수(n)와 유효 백분율(%)을 산출하여 제시합니다.", "check": "결측치가 전체 비중에 미치는 영향을 확인하십시오."},
    "카이제곱 검정": {"purpose": "범주형 변수 간의 통계적 관련성(연관성) 유무를 확인합니다.", "indicator": "기대빈도 가정 충족 여부에 따라 분석 결과의 타당성을 평가합니다.", "check": "기대빈도 5 미만 셀 비율이 20%를 초과하는지 검토하십시오."},
    "단일표본 T-검정": {"purpose": "표본 평균을 특정 기준값과 비교하여 차이를 검증합니다.", "indicator": "t값과 유의확률을 통해 기준치와의 통계적 거리를 판정합니다.", "check": "집단의 정규성 가정을 사전에 확인하십시오."},
    "독립표본 T-검정": {"purpose": "서로 독립적인 두 집단 간의 평균 차이를 비교 분석합니다.", "indicator": "두 집단 간 평균값 차이가 유의미한 수준인지 판정합니다.", "check": "두 집단의 정규성과 등분산성 가정을 확인하십시오."},
    "대응표본 T-검정": {"purpose": "동일 집단의 처치 전후(사전-사후) 평균 변화를 비교합니다.", "indicator": "사전-사후 점수 차이가 0에서 얼마나 벗어났는지 검증합니다.", "check": "차이값의 정규성 분포를 검토하십시오."},
    "분산분석(ANOVA)": {"purpose": "세 집단 이상의 평균 차이를 비교하고 변량 차이를 분석합니다.", "indicator": "F값으로 유의성을 판정한 후 사후분석(Tukey 등)을 수행합니다.", "check": "집단별 정규성과 등분산성 가정을 확인하십시오."},
    "상관분석": {"purpose": "두 연속형 변수 간의 선형적 관계의 강도를 파악합니다.", "indicator": "상관계수(r)를 통해 변수 간 관계의 방향과 밀접도를 평가합니다.", "check": "변수 간의 관계가 선형적인지 산점도를 검토하십시오."},
    "신뢰도 분석": {"purpose": "측정 도구의 문항들이 일관성 있게 측정되는지 평가합니다.", "indicator": "Cronbach α 계수가 0.7 이상일 때 신뢰도가 확보된 것으로 간주합니다.", "check": "역코딩 문항이 분석 전 적절히 변환되었는지 확인하십시오."},
    "회귀분석": {"purpose": "독립변수가 종속변수에 미치는 영향력을 수치화합니다.", "indicator": "R2로 모형 설명력을, Beta로 영향력의 크기를 평가합니다.", "check": "다중공선성(VIF < 10)과 잔차 가정을 검토하십시오."}
}

def create_pro_report(m_name, r_df, interpretation, guide, plot_b=None, assump=""):
    doc = Document(); doc.styles['Normal'].font.name = 'Malgun Gothic'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Malgun Gothic')
    doc.add_heading(f'STATERA Report: {m_name}', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    if assump: 
        doc.add_heading('1. Assumption Checks', level=1)
        clean_assump = assump.replace('<div class="assumption-pass">', '').replace('<div class="assumption-fail">', '').replace('</div>', '')
        doc.add_paragraph(clean_assump).italic = True
    
    doc.add_heading('2. Statistical Results', level=1)
    if r_df is not None:
        t = doc.add_table(r_df.shape[0]+1, r_df.shape[1]); t.style = 'Table Grid'
        for j, c in enumerate(r_df.columns): t.cell(0,j).text = str(c)
        for i in range(r_df.shape[0]):
            for j in range(r_df.shape[1]): t.cell(i+1,j).text = str(r_df.values[i,j])
            
    if plot_b: doc.add_heading('3. Visualization', level=1); doc.add_picture(plot_b, width=Inches(4.5))
    
    doc.add_heading('4. Writing Guide (APA Style)', level=1)
    doc.add_paragraph("※ This guide serves as a scaffold for your manuscript. Please verify and refine.")
    doc.add_paragraph(interpretation)
    
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

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
# 4. 메인 어플리케이션 레이아웃
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">STATERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수치적 결과 산출을 넘어, 연구 논리와 학술적 해석의 과정을 체득하는 통계 학습 플랫폼입니다.</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box">
        <div class="guide-label">🔒 데이터 보안 안내</div>
        <div class="guide-text">업로드된 데이터는 분석 즉시 메모리에서 삭제되며, 서버에 저장되지 않아 보안이 철저히 유지됩니다.</div>
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

    st.markdown('<div class="section-title"><span class="step-badge">01</span> 연구 목적에 따른 분석 기법 선택</div>', unsafe_allow_html=True)
    
    group = st.selectbox("분석 범주를 선택하십시오.", [
        "기초 데이터 분석 (Descriptive/Frequency)", 
        "집단 간 차이 검정 (T-test/ANOVA)", 
        "관계 및 영향력 분석 (Chi2/Corr/Regression)",
        "척도 신뢰도 분석 (Reliability)"
    ])
    
    if "기초" in group: m_list = ["기술통계", "빈도분석"]
    elif "차이" in group: m_list = ["단일표본 T-검정", "독립표본 T-검정", "대응표본 T-검정", "분산분석(ANOVA)"]
    elif "관계" in group: m_list = ["카이제곱 검정", "상관분석", "회귀분석"]
    else: m_list = ["신뢰도 분석"]
    
    method = st.radio("상세 분석 기법 선택", m_list, horizontal=True)
    m_info = STAT_MENTOR.get(method.split(" (")[0] if " (" in method else method, {"purpose": "데이터 분석 수행", "indicator": "지표 산출", "check": "가정 검토"})
    
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

    st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 변수 설정 및 실행</div>', unsafe_allow_html=True)
    final_df, p_val, interp, plot_img, assump_report = None, None, "", None, []
    anova_model_info = None  
    reg_anova_df = None 
    extra_metric = None 

    if method == "기술통계":
        v = st.selectbox("분석할 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            desc = df[[v]].describe().T.reset_index()
            final_df = desc.rename(columns={
                'index': 'Variable (변수명)', 'count': 'N (사례수)', 'mean': 'Mean (평균)', 'std': 'SD (표준편차)',
                'min': 'Min (최소)', 'max': 'Max (최대)'
            }).round(4)
            skew = df[v].skew(); kurt = df[v].kurt()
            if abs(skew) < 3 and abs(kurt) < 10:
                assump_report.append(f'<div class="assumption-pass">✅ 정규성 가정 충족: 왜도({skew:.2f})와 첨도({kurt:.2f})가 기준 이내입니다.</div>')
            else:
                assump_report.append(f'<div class="assumption-fail">⚠️ 정규성 가정 위배: 왜도/첨도 기준 초과.</div>')
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True, color="#0d9488"); plot_img = get_plot_buffer()
            interp = f"📌 {v}의 평균은 {df[v].mean():.2f}(SD={df[v].std():.2f})입니다."

    elif method == "빈도분석":
        vs = st.multiselect("분석할 변수들 (범주형)", all_cols)
        if st.button("통계 분석 실행") and vs:
            res = []
            for c in vs:
                counts = df[c].value_counts().reset_index(); counts.columns = ['Category (범주)', 'Frequency (빈도)']
                counts['Percent (비율)'] = (counts['Frequency (빈도)'] / counts['Frequency (빈도)'].sum() * 100).round(1)
                counts.insert(0, 'Variable (변수명)', c); res.append(counts)
            final_df = pd.concat(res)
            interp = "대상자의 일반적 분포를 확인하십시오."

    elif method == "독립표본 T-검정":
        g = st.selectbox("집단 변수 (범주형: 2집단)", all_cols)
        y = st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            if len(df[g].unique()) != 2: st.error("집단 변수는 정확히 2개의 범주를 가져야 합니다.")
            else:
                gps = df[g].unique(); g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                _, lp = stats.levene(g1, g2)
                equal_v = lp > 0.05
                stat, p = stats.ttest_ind(g1, g2, equal_var=equal_v)
                
                # [Expert Update] 효과 크기 Cohen's d 계산
                n1, n2 = len(g1), len(g2); v1, v2 = g1.var(), g2.var()
                pooled_sd = np.sqrt(((n1-1)*v1 + (n2-1)*v2) / (n1+n2-2))
                d = (g1.mean() - g2.mean()) / pooled_sd
                
                p_val = p
                final_df = pd.DataFrame({
                    "Group (집단)": [gps[0], gps[1]], "N (사례수)": [n1, n2], 
                    "Mean (평균)": [g1.mean(), g2.mean()], "SD (표준편차)": [g1.std(), g2.std()]
                }).round(3)
                extra_metric = {"label": "Effect Size (Cohen's d)", "value": f"{abs(d):.3f} ({'Large' if abs(d)>0.8 else 'Medium' if abs(d)>0.5 else 'Small'})"}
                plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
                interp = f"📌 두 집단 간 {y}의 평균 차이는 t={stat:.3f}, p={format_p(p)}로 {'유의합니다' if p < 0.05 else '유의하지 않습니다'}."

    elif method == "분산분석(ANOVA)":
        g = st.selectbox("집단 변수 (범주형: 3집단 이상)", all_cols)
        y = st.selectbox("검정 변수 (연속형)", num_cols)
        if st.button("통계 분석 실행"):
            model = ols(f'{y} ~ C({g})', data=df).fit()
            res = anova_lm(model, typ=2)
            p_val = res.iloc[0, 3]
            eta_sq = model.rsquared 
            
            final_df = res.reset_index().rename(columns={'index': 'Source', 'PR(>F)': 'p-value'}).round(3)
            # [Expert Update] 효과 크기 η² 및 해석 추가
            es_eval = "Large" if eta_sq > 0.14 else "Medium" if eta_sq > 0.06 else "Small"
            anova_model_info = f"- **효과 크기 (η²):** {eta_sq:.3f} ({es_eval} Effect)\n- **설명력:** 모델이 전체 변동의 {eta_sq*100:.1f}%를 설명합니다."
            
            if p_val < 0.05:
                tukey = pairwise_tukeyhsd(df[y].dropna(), df[g].dropna()); st.text(str(tukey))
            interp = f"📌 집단 간 차이 유의성 p={format_p(p_val)}"

    elif method == "상관분석":
        sel_vs = st.multiselect("분석할 변수군 선택", num_cols)
        if st.button("통계 분석 실행") and len(sel_vs) >= 2:
            # [Expert Update] 상관계수와 유의확률을 동시에 계산
            corr_m = df[sel_vs].corr().round(3)
            p_m = pd.DataFrame(index=sel_vs, columns=sel_vs)
            for i in sel_vs:
                for j in sel_vs:
                    if i == j: p_m.loc[i,j] = "-"
                    else: _, p = stats.pearsonr(df[i].dropna(), df[j].dropna()); p_m.loc[i,j] = format_p(p)
            
            st.markdown("##### 📊 상관계수(r) 및 유의확률(p) Matrix")
            final_df = corr_m.astype(str) + " (p=" + p_m.astype(str) + ")"
            plt.figure(figsize=(7, 5)); sns.heatmap(corr_m, annot=True, cmap="coolwarm"); plot_img = get_plot_buffer()
            interp = "변수 간 상관계수와 유의확률입니다. p < .05인 경우 통계적으로 유의합니다."

    elif method == "회귀분석":
        xs = st.multiselect("독립변수군", num_cols); y = st.selectbox("종속변수", num_cols)
        if st.button("통계 분석 실행") and xs:
            reg_data = df[list(xs) + [y]].dropna()
            X = sm.add_constant(reg_data[xs])
            model = sm.OLS(reg_data[y], X).fit()
            
            # [Expert Update] 표준화 계수(Beta) 계산
            std_beta = model.params[1:] * (reg_data[xs].std() / reg_data[y].std())
            
            final_df = pd.DataFrame({
                "Variable": ["(Intercept)"] + list(xs),
                "B (비표준화)": model.params.values,
                "Beta (표준화)": [np.nan] + list(std_beta.values),
                "t": model.tvalues.values, "p": model.pvalues.values
            }).round(3)
            final_df['p'] = final_df['p'].apply(format_p)
            p_val = model.f_pvalue
            interp = f"📌 모델의 설명력(R²)은 {model.rsquared:.3f}이며, 모형의 유의성은 p={format_p(p_val)}입니다."

    # Step 03: 결과 대시보드
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">03</span> 분석 결과 요약 및 학술적 해석</div>', unsafe_allow_html=True)
        if assump_report:
            with st.expander("🔍 필수 가정 검정 결과 확인"):
                for msg in assump_report: st.markdown(msg, unsafe_allow_html=True)
        
        col_main_L, col_main_R = st.columns([1.3, 1]) 
        with col_main_L:
            st.dataframe(final_df, use_container_width=True, hide_index=True)
            if anova_model_info: st.info(anova_model_info)
            
        with col_main_R:
            status_bg = "#dcfce7" if (p_val is not None and p_val < 0.05) else "#f1f5f9"
            st.markdown(f'<div style="background-color: {status_bg}; padding: 20px; border-radius: 12px; border: 1px solid #cbd5e1;">{interp}</div>', unsafe_allow_html=True)
            if extra_metric:
                st.markdown(f'<div style="background-color: #f0fdfa; padding: 15px; margin-top: 10px; border-radius: 10px;"><b>{extra_metric["label"]}:</b> {extra_metric["value"]}</div>', unsafe_allow_html=True)
            
            st.download_button("📄 워드 리포트 다운로드", data=create_pro_report(method, final_df, interp, ""), file_name=f"STATERA_{method}.docx", use_container_width=True, type="primary")

        if plot_img: st.image(plot_img, use_container_width=True)

st.markdown('<div class="ethics-container"><div class="ethics-title">⚠️ 연구 윤리 가이드</div><div class="ethics-text">본 결과는 유의수준 0.05 기준입니다. Writing Guide는 템플릿일 뿐 고찰은 연구자가 직접 작성해야 합니다.</div></div>', unsafe_allow_html=True)
