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
# 1. 설정 및 스타일 (원본 유지)
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
    .guide-box {{ flex: 1; background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; }}
    .mentor-box {{ background-color: #f0fdfa; border-left: 6px solid #0d9488; padding: 25px; border-radius: 12px; margin-bottom: 30px; }}
    .assumption-pass {{ background-color: #dcfce7; color: #166534; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #bbf7d0; font-weight: 600; font-size: 0.95rem; }}
    .assumption-fail {{ background-color: #fee2e2; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid #fecaca; font-weight: 600; font-size: 0.95rem; }}
    .section-title {{ font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 50px; margin-bottom: 25px; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; }}
    .step-badge {{ background: #0d9488; color: white; border-radius: 8px; padding: 4px 15px; font-size: 0.9rem; margin-right: 15px; vertical-align: middle; }}
    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 20px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: #0d9488; color: white; font-weight: 700; height: 3.8em; border: none; transition: 0.4s; }}
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 유틸리티 함수
# -----------------------------------------------------------------------------
def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"
def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

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
        doc.add_paragraph("해당 분석 기법은 별도의 가정 검정이 필요하지 않습니다.")

    # 2. Results
    doc.add_heading('2. Statistical Results', level=1)
    if r_df is not None:
        t = doc.add_table(r_df.shape[0]+1, r_df.shape[1]); t.style = 'Table Grid'
        for j, c in enumerate(r_df.columns): t.cell(0,j).text = str(c)
        for i in range(r_df.shape[0]):
            for j in range(r_df.shape[1]): t.cell(i+1,j).text = str(r_df.values[i,j])
    
    if extra_info: doc.add_paragraph(f"\n[Additional Metrics]\n{extra_info}")
    
    # 3. Visualization
    if plot_b:
        doc.add_heading('3. Visualization', level=1)
        doc.add_picture(plot_b, width=Inches(3.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 4. Guide
    doc.add_heading('4. Writing Guide (APA Style)', level=1)
    doc.add_paragraph(interpretation.replace("<b>", "").replace("</b>", ""))
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

STAT_MENTOR = {
    "기술통계": {"purpose": "데이터 분포 요약", "indicator": "Mean, SD, Skewness", "check": "정규성(왜도/첨도)"},
    "빈도분석": {"purpose": "범주별 빈도 파악", "indicator": "Frequency(n), Percent(%)", "check": "결측치"},
    "카이제곱 검정": {"purpose": "범주 변수 간 연관성", "indicator": "Chi2, p-value", "check": "기대빈도 5 미만 셀 비율"},
    "단일표본 T-검정": {"purpose": "기준값과 평균 비교", "indicator": "t, p-value", "check": "정규성(Shapiro-Wilk)"},
    "독립표본 T-검정": {"purpose": "두 집단 간 차이 비교", "indicator": "t, p, Cohen's d", "check": "정규성, 등분산성(Levene)"},
    "대응표본 T-검정": {"purpose": "전후 차이 비교", "indicator": "t, p-value", "check": "차이값의 정규성"},
    "분산분석(ANOVA)": {"purpose": "세 집단 이상 비교", "indicator": "F, Eta-squared", "check": "등분산성, 잔차 정규성"},
    "상관분석": {"purpose": "변수 간 선형 관계", "indicator": "Pearson r", "check": "선형성"},
    "신뢰도 분석": {"purpose": "도구 일관성 평가", "indicator": "Cronbach α", "check": "문항 적합도"},
    "회귀분석": {"purpose": "인과관계 추정", "indicator": "R2, Beta", "check": "다중공선성, 독립성"}
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
    st.code("nncj91@snu.ac.kr", language="text")
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 4. 메인 로직
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">STATERA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수치적 결과 산출을 넘어, 연구 논리와 학술적 해석의 과정을 체득하는 통계 학습 플랫폼입니다.</div>', unsafe_allow_html=True)

up_file = st.file_uploader("파일 업로드", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    num_cols = df.select_dtypes(include=[np.number]).columns
    all_cols = df.columns
    st.success(f"데이터 로드 완료 (N={len(df)})")

    # Step 1
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 분석 기법 선택</div>', unsafe_allow_html=True)
    group = st.selectbox("분석 범주 선택", ["기초 데이터 분석", "집단 간 차이 검정", "관계 및 영향력 분석", "척도 신뢰도 분석"])
    
    if "기초" in group: m_list = ["기술통계", "빈도분석"]
    elif "차이" in group: m_list = ["단일표본 T-검정", "독립표본 T-검정", "대응표본 T-검정", "분산분석(ANOVA)"]
    elif "관계" in group: m_list = ["카이제곱 검정", "상관분석", "회귀분석"]
    else: m_list = ["신뢰도 분석"]
    
    method = st.radio("상세 기법", m_list, horizontal=True)
    m_info = STAT_MENTOR[method]
    st.markdown(f'<div class="mentor-box"><div class="mentor-title">👨‍🏫 {method} 가이드</div><div class="mentor-content"><b>목적:</b> {m_info["purpose"]}<br><b>지표:</b> {m_info["indicator"]}<br><b>점검:</b> {m_info["check"]}</div></div>', unsafe_allow_html=True)

    # Step 2
    st.markdown('<div class="section-title"><span class="step-badge">02</span> 변수 설정 및 실행</div>', unsafe_allow_html=True)
    final_df, p_val, interp, plot_img, assump_report = None, None, "", None, []
    extra_metric_text, anova_info, reg_anova_df = None, None, None

    if method == "기술통계":
        v = st.selectbox("변수 (연속형)", num_cols)
        if st.button("분석 실행"):
            final_df = df[[v]].describe().T.reset_index().rename(columns={
                'index':'Variable (변수명)', 'count':'N (사례수)', 'mean':'Mean (평균)', 'std':'SD (표준편차)',
                'min':'Min (최소)', 'max':'Max (최대)'
            }).round(3)
            skew, kurt = df[v].skew(), df[v].kurt()
            if abs(skew)<3 and abs(kurt)<10: assump_report.append(f'<div class="assumption-pass">✅ 왜도({skew:.2f})/첨도({kurt:.2f}) 기준 충족 (정규성 만족)</div>')
            else: assump_report.append(f'<div class="assumption-fail">⚠️ 왜도/첨도 기준 초과 (정규성 위배 가능성)</div>')
            plt.figure(figsize=(6,3)); sns.histplot(df[v].dropna(), kde=True, color="#0d9488"); plot_img = get_plot_buffer()
            interp = f"📌 {v}의 평균은 {df[v].mean():.2f}(SD={df[v].std():.2f})입니다."

    elif method == "빈도분석":
        vs = st.multiselect("변수 (범주형)", all_cols)
        if st.button("분석 실행") and vs:
            res = []
            for c in vs:
                counts = df[c].value_counts().reset_index()
                counts.columns = ['Category (범주)', 'Frequency (빈도)']
                counts['Percent (%)'] = (counts['Frequency (빈도)'] / counts['Frequency (빈도)'].sum() * 100).round(1)
                counts.insert(0, 'Variable (변수명)', c); res.append(counts)
            final_df = pd.concat(res); interp = "각 범주의 빈도(n)와 비율(%)을 확인하십시오."

    elif method == "카이제곱 검정":
        r = st.selectbox("행 변수", all_cols); c = st.selectbox("열 변수", all_cols)
        if st.button("분석 실행"):
            ct = pd.crosstab(df[r], df[c]); chi2, p, _, exp = stats.chi2_contingency(ct)
            p_val = p; final_df = ct.astype(str) + " (" + (ct/ct.sum()*100).round(1).astype(str) + "%)"
            
            under_5 = (exp < 5).sum(); total_cells = exp.size; pct_under_5 = (under_5 / total_cells) * 100
            if pct_under_5 <= 20: assump_report.append(f'<div class="assumption-pass">✅ 기대빈도 5 미만 셀 {pct_under_5:.1f}% (20% 이하 충족)</div>')
            else: assump_report.append(f'<div class="assumption-fail">⚠️ 기대빈도 5 미만 셀 {pct_under_5:.1f}% (20% 초과, Fisher 권장)</div>')
            
            interp = f"📌 두 변수 간 유의한 연관성이 {'있습니다' if p < 0.05 else '없습니다'} (p={format_p(p)})."

    elif method == "단일표본 T-검정":
        y = st.selectbox("검정 변수", num_cols); ref = st.number_input("기준값", value=0.0)
        if st.button("분석 실행"):
            data = df[y].dropna(); stat, p = stats.ttest_1samp(data, ref); p_val = p
            if stats.shapiro(data)[1] > 0.05: assump_report.append('<div class="assumption-pass">✅ 정규성 가정 충족 (Shapiro-Wilk)</div>')
            else: assump_report.append('<div class="assumption-fail">⚠️ 정규성 가정 위배 (비모수 검정 고려)</div>')
            
            final_df = pd.DataFrame({
                "Variable (변수명)":[y], "Test Value (기준값)":[ref], "Mean (평균)":[data.mean()], 
                "t (t값)":[stat], "p (유의확률)":[format_p(p)]
            }).round(3)
            diff_dir = "높았습니다" if data.mean() > ref else "낮았습니다"
            interp = f"📌 표본의 평균({data.mean():.2f})은 기준값({ref})보다 통계적으로 유의하게 {diff_dir if p<0.05 else '차이가 없었습니다'} (p={format_p(p)})."

    elif method == "독립표본 T-검정":
        g = st.selectbox("집단(2범주)", all_cols); y = st.selectbox("변수", num_cols)
        if st.button("분석 실행"):
            gps = df[g].unique()
            if len(gps) == 2:
                g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                
                # Levene & Welch Logic
                levene_p = stats.levene(g1, g2)[1]
                equal_var = levene_p > 0.05
                stat, p = stats.ttest_ind(g1, g2, equal_var=equal_var); p_val = p
                
                if equal_var: assump_report.append(f'<div class="assumption-pass">✅ 등분산성 가정 충족 (Levene p={levene_p:.3f})</div>')
                else: assump_report.append(f'<div class="assumption-fail">⚠️ 등분산성 위배 (p={levene_p:.3f}) → Welch-test 적용</div>')
                
                d = abs((g1.mean()-g2.mean())/np.sqrt(((len(g1)-1)*g1.var()+(len(g2)-1)*g2.var())/(len(g1)+len(g2)-2)))
                final_df = pd.DataFrame({
                    "Group (집단)": gps, "N (사례수)": [len(g1), len(g2)], 
                    "Mean (평균)": [g1.mean(), g2.mean()], "SD (표준편차)": [g1.std(), g2.std()]
                }).round(3)
                extra_metric_text = f"Effect Size (Cohen's d): {d:.3f}"
                plt.figure(figsize=(5,4)); sns.boxplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
                
                m_diff = "높게" if g1.mean() > g2.mean() else "낮게"
                sig_txt = f"{gps[0]} 집단이 {gps[1]}보다 유의하게 {m_diff} 나타났습니다" if p < 0.05 else "집단 간 유의한 차이가 없었습니다"
                interp = f"📌 분석 결과, {sig_txt} (t={stat:.3f}, p={format_p(p)})."

    elif method == "대응표본 T-검정":
        y1 = st.selectbox("사전 변수", num_cols); y2 = st.selectbox("사후 변수", num_cols)
        if st.button("분석 실행"):
            tmp = df[[y1, y2]].dropna(); diff = tmp[y2] - tmp[y1]
            stat, p = stats.ttest_rel(tmp[y1], tmp[y2]); p_val = p
            
            if stats.shapiro(diff)[1] > 0.05: assump_report.append('<div class="assumption-pass">✅ 차이값의 정규성 충족</div>')
            else: assump_report.append('<div class="assumption-fail">⚠️ 정규성 위배 (Wilcoxon 권장)</div>')
            
            final_df = pd.DataFrame({
                "Pair (변수쌍)": [f"{y1} - {y2}"], "Mean Diff (평균차이)": [diff.mean()], 
                "t (t값)": [stat], "p (유의확률)": [format_p(p)]
            }).round(3)
            change = "증가" if diff.mean() > 0 else "감소"
            interp = f"📌 사후 점수는 사전 점수보다 유의하게 {change}했습니다 (p={format_p(p)})."

    elif method == "분산분석(ANOVA)":
        g = st.selectbox("집단(3범주+)", all_cols); y = st.selectbox("변수", num_cols)
        if st.button("분석 실행"):
            model = ols(f'{y} ~ C({g})', data=df).fit(); res = anova_lm(model, typ=2); p_val = res.iloc[0,3]
            eta = model.rsquared; final_df = res.reset_index().rename(columns={
                'index':'Source (변동원)', 'sum_sq':'Sum of Squares (제곱합)', 'df':'df (자유도)', 
                'mean_sq':'Mean Square (평균제곱)', 'F':'F (F값)', 'PR(>F)':'p (유의확률)'
            }).round(3)
            
            grps = [df[df[g]==k][y].dropna() for k in df[g].unique()]
            if stats.levene(*grps)[1] > 0.05: assump_report.append('<div class="assumption-pass">✅ 등분산성 가정 충족</div>')
            else: assump_report.append('<div class="assumption-fail">⚠️ 등분산성 위배 (Welch ANOVA 권장)</div>')
            
            anova_info = f"- **Effect Size (η²):** {eta:.3f}"
            extra_metric_text = anova_info.replace("**", "")
            if p_val < 0.05: 
                tukey = pairwise_tukeyhsd(df[y].dropna(), df[g].dropna()); st.text(str(tukey))
                interp = f"📌 집단 간 평균 차이가 통계적으로 유의했습니다 (p={format_p(p_val)}). 사후검정 결과(상단)를 참고하십시오."
            else: interp = f"📌 집단 간 통계적으로 유의한 차이가 발견되지 않았습니다 (p={format_p(p_val)})."

    elif method == "상관분석":
        vs = st.multiselect("변수군", num_cols)
        if st.button("분석 실행") and len(vs)>=2:
            corr_m = df[vs].corr().round(3)
            p_m = pd.DataFrame([[format_p(stats.pearsonr(df[i].dropna(), df[j].dropna())[1]) if i!=j else "-" for j in vs] for i in vs], index=vs, columns=vs)
            final_df = corr_m.astype(str) + " (p=" + p_m.astype(str) + ")"
            plt.figure(figsize=(6,5)); sns.heatmap(corr_m, annot=True, cmap="coolwarm"); plot_img = get_plot_buffer()
            interp = "📌 상관계수(r)와 유의확률(p) 행렬입니다."

    elif method == "신뢰도 분석":
        vs = st.multiselect("문항군", num_cols)
        if st.button("분석 실행") and len(vs)>=2:
            it = df[vs].dropna(); k = it.shape[1]; alpha = (k/(k-1)) * (1 - (it.var(ddof=1).sum() / it.sum(axis=1).var(ddof=1)))
            final_df = pd.DataFrame({"Cronbach α (계수)": [f"{alpha:.3f}"]})
            interp = f"📌 크론바흐 알파 계수는 {alpha:.3f}로, {'신뢰도가 높습니다' if alpha >= 0.7 else '신뢰도가 낮아 문항 수정이 필요합니다'}."

    elif method == "회귀분석":
        rtype = st.radio("유형", ["선형", "로지스틱"])
        xs = st.multiselect("독립변수", num_cols); y = st.selectbox("종속변수", num_cols)
        if st.button("분석 실행") and xs:
            reg_d = df[list(xs)+[y]].dropna(); X = sm.add_constant(reg_d[xs])
            if "선형" in rtype:
                model = sm.OLS(reg_d[y], X).fit(); p_val = model.f_pvalue
                beta = model.params[1:] * (reg_d[xs].std() / reg_d[y].std())
                
                vifs = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
                if max(vifs[1:]) < 10: assump_report.append(f'<div class="assumption-pass">✅ 다중공선성 없음 (Max VIF={max(vifs[1:]):.2f})</div>')
                else: assump_report.append(f'<div class="assumption-fail">⚠️ 다중공선성 경고 (Max VIF={max(vifs[1:]):.2f})</div>')
                
                final_df = pd.DataFrame({
                    "Variable (변수명)": ["(Intercept)"] + list(xs), "B (비표준화 계수)": model.params.values,
                    "Beta (표준화 계수)": [np.nan] + list(beta.values), "t (t값)": model.tvalues.values, "p (유의확률)": model.pvalues.apply(format_p).values
                }).round(3)
                
                if durbin_watson(model.resid) > 1.5: assump_report.append('<div class="assumption-pass">✅ 잔차 독립성 충족 (Durbin-Watson)</div>')
                interp = f"📌 회귀모형은 통계적으로 {'유의합니다' if p_val < 0.05 else '유의하지 않습니다'} (R²={model.rsquared:.3f})."
            else:
                model = sm.Logit(reg_d[y], X).fit(disp=False); p_val = model.llr_pvalue
                final_df = pd.DataFrame({
                    "Variable (변수명)": model.params.index, "B (Coeff)": model.params.values, 
                    "OR (Odds Ratio)": np.exp(model.params.values), "p (Sig)": model.pvalues.apply(format_p).values
                }).round(3)
                interp = f"📌 로지스틱 모형 유의확률 p={format_p(p_val)}."

    # --- Step 3 ---
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">03</span> 분석 결과</div>', unsafe_allow_html=True)
        if assump_report:
            with st.expander("🔍 가정 검정 결과", expanded=True):
                for m in assump_report: st.markdown(m, unsafe_allow_html=True)
        
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        if anova_info: st.info(anova_info)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_L, col_R = st.columns([1, 1])
        with col_L:
            status_bg = "#dcfce7" if (p_val is not None and p_val < 0.05) else "#f1f5f9"
            st.markdown(f'<div style="background-color: {status_bg}; padding: 20px; border-radius: 12px; border: 1px solid #cbd5e1;">{interp}</div>', unsafe_allow_html=True)
            if extra_metric_text: st.markdown(f"**지표 정보:** {extra_metric_text}")
        
        with col_R:
            st.write("") 
            st.download_button("📄 워드 리포트 다운로드", data=create_pro_report(method, final_df, interp, plot_img, assump_report, extra_metric_text), file_name=f"STATERA_{method}.docx", type="primary", use_container_width=True)

        if plot_img:
            st.markdown("<br>", unsafe_allow_html=True)
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
