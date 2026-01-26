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
    .var-badge {{ background-color: #ccfbf1; color: #0f766e; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 0.9rem; margin-right: 8px; }}

    /* T-test 세부 가이드 박스 */
    .sub-method-info {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 0.95rem; color: #334155; }}

    .landing-zone {{ text-align: center; padding: 60px 20px; background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 20px; margin-top: 20px; }}
    .section-title {{ font-size: 1.7rem; font-weight: 700; color: #0f172a; margin: 40px 0 20px 0; display: flex; align-items: center; }}
    .step-badge {{ background: #0d9488; color: white; padding: 4px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; margin-right: 12px; }}
    
    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 25px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; font-weight: 700; height: 3.8em; border: none; font-size: 1rem; }}
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
    # 줄바꿈 적용
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
# 3. 분석 방법론 가이드 데이터
# -----------------------------------------------------------------------------
METHOD_GUIDES = {
    "기술통계": {
        "title": "📈 기술통계 (Descriptive Statistics)",
        "desc": "연속형 변수의 평균, 표준편차 등을 산출하여 데이터의 전반적인 경향을 파악합니다.",
        "원인": "해당 없음", "결과": "연속형 변수",
        "use": "연구 대상자의 주요 수치형 지표를 요약할 때 사용합니다."
    },
    "빈도분석": {
        "title": "📊 빈도분석 (Frequency Analysis)",
        "desc": "범주형 변수의 빈도와 백분율을 산출하여 대상자의 분포를 확인합니다.",
        "원인": "해당 없음", "결과": "범주형 변수",
        "use": "성별, 학력, 질병 유무 등 대상자의 일반적 특성을 보고할 때 사용합니다."
    },
    "T-검정": {
        "title": "👥 T-검정 (T-test)",
        "desc": "집단 간 평균 차이를 비교하여 통계적으로 유의미한지 확인합니다.",
        "iv": "범주형 (2집단)", "dv": "연속형 변수",
        "use": "두 그룹 간의 결과값 차이 분석 시 사용합니다."
    },
    "분산분석": {
        "title": "🏫 분산분석 (ANOVA)",
        "desc": "세 개 이상의 그룹 간 평균 차이를 비교하여 통계적으로 유의미한지 확인합니다.",
        "원인": "범주형 (3집단 이상)", "결과": "연속형 변수",
        "use": "학력별 점수 차이나 연령대별 차이 분석 시 사용합니다."
    },
    "상관분석": {
        "title": "🔗 상관분석 (Correlation Analysis)",
        "desc": "두 연속형 변수가 서로 얼마나 같은 방향으로 변화(양의 관계), 반대 방향으로 변화(음의 관계)하는지 관련성을 분석합니다.",
        "원인": "연속형 변수", "결과": "연속형 변수",
        "use": "스트레스와 수면 시간 사이의 관련성 등을 확인할 때 사용합니다."
    },
    "회귀분석": {
        "title": "🎯 회귀분석 (Regression Analysis)",
        "desc": "원인이 되는 변수가 결과에 얼마나 영향을 미치는지 예측합니다.",
        "원인": "연속형 또는 범주형", "결과": "연속형(선형) 또는 이분 범주형(로지스틱)",
        "use": "원인 변수가 결과에 미치는 영향력의 크기를 분석할 때 사용합니다."
    }
}

# T-test 세부 가이드
TTEST_SUB_GUIDES = {
    "독립표본": "서로 다른 두 집단의 평균을 비교합니다. (예: 남성 vs 여성의 만족도 비교)",
    "대응표본": "동일한 집단의 전/후 평균을 비교합니다. (예: 교육 전 vs 교육 후 점수 변화)",
    "단일표본": "한 집단의 평균을 특정 기준값과 비교합니다. (예: 우리 반 평균 vs 전국 평균 70점)"
}

# -----------------------------------------------------------------------------
# 4. 유틸리티 함수
# -----------------------------------------------------------------------------
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
# 5. 메인 워크플로우
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="guide-container">
    <div class="guide-box"><div class="guide-label">🔒 데이터 보안 안내</div><div class="guide-text">분석 즉시 데이터를 메모리에서 삭제하며, 서버에 저장되지 않습니다.</div></div>
    <div class="guide-box"><div class="guide-label">📄 데이터 형식 가이드</div><div class="guide-text">파일의 첫 번째 행에는 반드시 변수명이 포함되어야 시스템이 인식합니다.</div></div>
</div>
""", unsafe_allow_html=True)

up_file = st.file_uploader("Upload Data", type=["xlsx", "csv"], label_visibility="collapsed")

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    st.success(f"데이터 로드 완료: 총 {len(df)}건의 사례가 인식되었습니다.")
    
    st.markdown('<div class="section-title"><span class="step-badge">01</span> 분석 방법 선택</div>', unsafe_allow_html=True)
    method = st.radio("수행할 통계 기법을 선택하세요", list(METHOD_GUIDES.keys()), horizontal=True, label_visibility="collapsed")

    guide = METHOD_GUIDES[method]
    st.markdown(f"""
    <div class="method-info">
        <div class="method-title">{guide['title']}</div>
        <div class="method-desc">
            {guide['desc']}<br>
            <span class="var-badge">원인 변수(독립변수)</span> {guide.get('iv', guide.get('원인', ''))} &nbsp; 
            <span class="var-badge">결과 변수(종속변수)</span> {guide.get('dv', guide.get('결과', ''))}<br>
            <b>활용 예시:</b> {guide['use']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=[np.number]).columns
    all_cols = df.columns
    final_df, interpretation, plot_img = None, "", None

    # --- 분석 로직 ---
    if method == "기술통계":
        sel_v = st.multiselect("분석할 연속형 변수를 선택하세요", num_cols)
        if st.button("분석 실행") and sel_v:
            final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
            final_df.columns = ['변수명', 'N (사례 수)', '평균', '표준편차', '최솟값', '최댓값']
            interpretation = "선택한 변수들의 기술통계 분포입니다."
            plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v], palette="Set2"); plot_img = get_plot_buffer()

    elif method == "빈도분석":
        sel_v = st.multiselect("분석할 범주형 변수를 선택하세요", all_cols)
        if st.button("분석 실행") and sel_v:
            res_list = []
            for col in sel_v:
                c = df[col].value_counts().reset_index()
                c.columns = ['범주', '빈도(N)']
                c['비율(%)'] = (c['빈도(N)'] / c['빈도(N)'].sum() * 100).round(1)
                c.insert(0, '변수명', col)
                res_list.append(c)
            final_df = pd.concat(res_list)
            interpretation = "선택한 변수들에 대한 빈도와 백분율입니다."
            plt.figure(figsize=(10, 5)); sns.countplot(x=sel_v[0], data=df, palette="pastel"); plot_img = get_plot_buffer()

    elif method == "T-검정":
        t_mode = st.radio("세부 유형 선택", list(TTEST_SUB_GUIDES.keys()), horizontal=True)
        # 세부 유형 가이드 출력
        st.markdown(f'<div class="sub-method-info">💡 {TTEST_SUB_GUIDES[t_mode]}</div>', unsafe_allow_html=True)
        
        if t_mode == "독립표본":
            g, y = st.selectbox("집단 변수 (범주형)", all_cols), st.selectbox("결과 변수 (연속형)", num_cols)
            if st.button("분석 실행"):
                gps = df[g].unique()
                g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                final_df = pd.DataFrame({"변수명": [y], "t값": [f"{t:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"검정 결과 p={format_p(p)}이며, 집단 간 차이는 {'유의함' if p < .05 else '유의하지 않음'}으로 나타났습니다."
                plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df, palette="mako"); plot_img = get_plot_buffer()
        elif t_mode == "대응표본":
            v1, v2 = st.selectbox("사전 변수", num_cols), st.selectbox("사후 변수", num_cols)
            if st.button("분석 실행"):
                t, p = stats.ttest_rel(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"비교": [f"{v1} vs {v2}"], "t값": [f"{t:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = "사전-사후 평균 변화에 대한 분석 결과입니다."
                plt.figure(figsize=(6, 5)); sns.pointplot(data=df[[v1, v2]], palette="flare"); plot_img = get_plot_buffer()
        elif t_mode == "단일표본":
            v, mu = st.selectbox("분석 변수", num_cols), st.number_input("검정 목표값", value=0.0)
            if st.button("분석 실행"):
                t, p = stats.ttest_1samp(df[v].dropna(), mu)
                final_df = pd.DataFrame({"변수명": [v], "t값": [f"{t:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = f"평균값과 기준값({mu}) 사이의 차이를 분석한 결과입니다."
                plt.figure(figsize=(6, 5)); sns.histplot(df[v], kde=True); plt.axvline(mu, color='red', ls='--'); plot_img = get_plot_buffer()

    elif method == "분산분석":
        g, y = st.selectbox("집단 변수 (3집단 이상)", all_cols), st.selectbox("결과 변수 (연속형)", num_cols)
        if st.button("분석 실행"):
            groups = [df[df[g]==val][y].dropna() for val in df[g].unique()]
            f_val, p = stats.f_oneway(*groups)
            final_df = pd.DataFrame({"변수명": [y], "F값": [f"{f_val:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
            interpretation = f"집단 간 평균 차이 검정 결과 p={format_p(p)}입니다."
            plt.figure(figsize=(8, 5)); sns.boxplot(x=g, y=y, data=df, palette="viridis"); plot_img = get_plot_buffer()

    elif method == "상관분석":
        v1, v2 = st.selectbox("변수 1", num_cols), st.selectbox("변수 2", num_cols)
        if st.button("분석 실행"):
            r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
            final_df = pd.DataFrame({"분석 변수": [f"{v1} & {v2}"], "상관계수(r)": [f"{r:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
            interpretation = f"상관분석 결과 r={r:.2f}로 산출되었습니다."
            plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df, line_kws={'color':'#0d9488'}); plot_img = get_plot_buffer()

    elif method == "회귀분석":
        reg_t = st.radio("유형 선택", ["선형 회귀 (결과가 수치일 때)", "로지스틱 회귀 (결과가 예/아니오일 때)"], horizontal=True)
        x_vars = st.multiselect("원인 변수 선택", num_cols)
        y_var = st.selectbox("결과 변수 선택", num_cols)
        if st.button("분석 실행") and x_vars:
            X = sm.add_constant(df[x_vars])
            if "선형" in reg_t:
                model = sm.OLS(df[y_var], X).fit()
                final_df = pd.DataFrame({"B (계수)": model.params, "표준오차": model.bse, "t값": model.tvalues, "p값": model.pvalues}).reset_index()
                interpretation = f"선형회귀 분석 결과 설명력(R2)은 {model.rsquared:.3f}입니다."
                plt.figure(figsize=(8, 4)); sns.heatmap(df[x_vars + [y_var]].corr(), annot=True, cmap="YlGnBu"); plot_img = get_plot_buffer()
            else:
                model = sm.Logit(df[y_var], X).fit(disp=0)
                conf = model.conf_int()
                final_df = pd.DataFrame({
                    "B": model.params, "OR (오즈비)": np.exp(model.params),
                    "Lower CI": np.exp(conf[0]), "Upper CI": np.exp(conf[1]), "p": model.pvalues
                }).reset_index()
                interpretation = f"로지스틱 회귀 결과 Pseudo R2는 {model.prsquared:.3f}입니다."
                plt.figure(figsize=(8, 4)); sns.barplot(x=final_df.iloc[1:]['index'], y=final_df.iloc[1:]['OR (오즈비)'], palette="flare"); plot_img = get_plot_buffer()
            final_df['p값'] = final_df.iloc[:, -1].apply(lambda x: f"{format_p(x)}{get_stars(x)}")

    # --- 결과 출력 ---
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 결과 및 리포트</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1.5, 1])
        with c1: st.table(final_df); st.info(f"결과 해석 안내: {interpretation}")
        with c2: 
            if plot_img: st.image(plot_img)
        st.download_button("📄 워드 리포트 다운로드", data=create_word_report(final_df, interpretation, plot_img), file_name=f"STATERA_Report.docx")

else:
    st.markdown("""
    <div class="landing-zone">
        <div style="font-size: 3.5rem; margin-bottom: 20px;">⬆️</div>
        <h3 style="color: #0f172a; margin-bottom: 10px;">분석을 시작하려면 파일을 업로드하세요</h3>
        <p style="color: #64748b;">파일이 업로드되면 전문 통계 가이드와 분석 옵션이 활성화됩니다.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #cbd5e1; margin-top: 100px; font-size: 0.8rem;'>Professional Statistical Engine | ANDA Lab Jeongin Choe</div>", unsafe_allow_html=True)
