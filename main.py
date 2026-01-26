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
# 1. UI 스타일링 및 프리미엄 테마 설정 (Pretendard 적용)
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

    .sub-method-info {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 0.95rem; color: #334155; }}
    
    .ethics-container {{ background-color: #fff7ed; border: 1px solid #ffedd5; border-radius: 12px; padding: 20px; margin-top: 50px; margin-bottom: 30px; }}
    .ethics-title {{ color: #c2410c; font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; }}
    .ethics-text {{ color: #9a3412; font-size: 0.9rem; line-height: 1.6; }}

    div[data-testid="stRadio"] > div {{ flex-direction: row; gap: 25px; overflow-x: auto; }}
    .stButton>button {{ width: 100%; border-radius: 12px; background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); color: white; font-weight: 700; height: 3.8em; border: none; font-size: 1rem; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 (정보 및 연락처)
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
# 3. 분석 방법론 가이드 데이터
# -----------------------------------------------------------------------------
METHOD_GUIDES = {
    "기술통계": {
        "title": "📈 기술통계 (Descriptive Statistics)",
        "desc": "연속형 변수의 평균, 표준편차 등을 산출하여 데이터의 전반적인 경향을 파악합니다.",
        "독립": "해당 없음", "종속": "연속형 변수",
        "use": "연구 대상자의 주요 수치형 지표를 요약할 때 사용합니다."
    },
    "빈도분석": {
        "title": "📊 빈도분석 (Frequency Analysis)",
        "desc": "범주형 변수의 빈도와 백분율을 산출하여 대상자의 분포를 확인합니다.",
        "독립": "해당 없음", "종속": "범주형 변수",
        "use": "성별, 학력 등 대상자의 일반적 특성을 보고할 때 사용합니다."
    },
    "T-검정": {
        "title": "👥 T-검정 (T-test)",
        "desc": "집단 간 평균 차이를 비교하여 통계적으로 의미가 있는지 확인합니다.",
        "독립": "범주형 (2집단)", "종속": "연속형 변수",
        "use": "두 그룹 간의 결과값 차이를 비교하고 싶을 때 사용합니다."
    },
    "분산분석": {
        "title": "🏫 분산분석 (ANOVA)",
        "desc": "세 개 이상의 그룹들 사이에 평균 차이가 존재하는지 확인합니다.",
        "독립": "범주형 (3집단 이상)", "종속": "연속형 변수",
        "use": "학력이나 연령대별 점수 차이 분석 시 사용합니다."
    },
    "상관분석": {
        "title": "🔗 상관분석 (Correlation Analysis)",
        "desc": "두 연속형 변수가 서로 얼마나 같은 방향 혹은 반대 방향으로 변화하는지 분석합니다.",
        "독립": "연속형 변수", "종속": "연속형 변수",
        "use": "한 변수가 증가할 때 다른 변수도 같이 변화하는 경향이 있는지 확인 시 사용합니다."
    },
    "회귀분석": {
        "title": "🎯 회귀분석 (Regression Analysis)",
        "desc": "독립변수가 종속변수에 어느 정도의 영향력을 미치는지 예측합니다.",
        "독립": "연속형 또는 범주형", "종속": "연속형(선형) 또는 이분 범주형(로지스틱)",
        "use": "특정 요인이 결과에 미치는 영향의 크기를 수치화할 때 사용합니다."
    }
}

TTEST_SUB_GUIDES = {
    "독립표본": "서로 다른 두 집단의 평균을 비교합니다. (예: 남성 vs 여성)",
    "대응표본": "동일 집단의 전/후 평균 변화를 비교합니다. (예: 교육 전 vs 교육 후)",
    "단일표본": "집단의 평균을 특정 기준값과 비교합니다. (예: 우리 반 평균 vs 기준 점수)"
}

# -----------------------------------------------------------------------------
# 4. 유틸리티 및 해석 엔진
# -----------------------------------------------------------------------------
def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"

def get_auto_interpretation(method, p_val, r_val=None, t_type=None):
    is_sig = p_val < 0.05
    sig_text = "통계적으로 유의한 것으로 나타났습니다(p < .05)." if is_sig else "통계적으로 유의하지 않은 것으로 나타났습니다(p >= .05)."
    
    if method == "T-검정":
        prefix = f"{t_type} T-검정 결과, "
        if t_type == "독립표본": body = f"두 집단 간의 평균 차이는 {sig_text}"
        elif t_type == "대응표본": body = f"사전과 사후의 평균 변화는 {sig_text}"
        else: body = f"집단의 평균과 기준값 사이의 차이는 {sig_text}"
        return prefix + body
    elif method == "분산분석":
        return f"일원배치 분산분석(ANOVA) 결과, 설정된 집단들 간의 평균 차이는 {sig_text}"
    elif method == "상관분석":
        direction = "양(+)의 관계" if r_val > 0 else "음(-)의 관계"
        return f"상관분석 결과, 두 변수 간의 {direction}는 {sig_text}"
    elif method == "회귀분석":
        return f"회귀분석 결과, 설정된 독립 변수가 종속 변수에 미치는 영향은 {sig_text}"
    return f"분석 결과 p값이 {format_p(p_val)}로 산출되었습니다."

def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

def create_word_report(df, interpretation, plot_buf=None):
    doc = Document(); doc.add_heading('STATERA Analysis Report', 0)
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
    if plot_buf: doc.add_heading('Visualization', level=1); doc.add_picture(plot_buf, width=Inches(5.5))
    doc.add_heading('AI Interpretation', level=1); doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

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
    method = st.radio("수행할 통계 기법을 클릭하세요", list(METHOD_GUIDES.keys()), horizontal=True, label_visibility="collapsed")

    guide = METHOD_GUIDES[method]
    st.markdown(f"""
    <div class="method-info">
        <div class="method-title">{guide['title']}</div>
        <div class="method-desc">
            {guide['desc']}<br>
            <span class="var-badge">독립 변수</span> {guide['독립']} &nbsp; <span class="var-badge">종속 변수</span> {guide['종속']}<br>
            <b>활용 예시:</b> {guide['use']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    num_cols = df.select_dtypes(include=[np.number]).columns
    all_cols = df.columns
    final_df, interpretation, plot_img = None, "", None

    # 1) 기술통계
    if method == "기술통계":
        sel_v = st.multiselect("분석할 연속형 변수를 선택하세요", num_cols)
        if st.button("분석 실행") and sel_v:
            final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
            final_df.columns = ['변수명', 'N (사례 수)', '평균', '표준편차', '최솟값', '최댓값']
            interpretation = "선택된 변수들의 분포와 중심 경향성에 관한 분석 결과입니다."
            plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v], palette="Set2"); plot_img = get_plot_buffer()

    # 2) 빈도분석
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
            interpretation = "각 범주별 빈도와 상대적 비중을 확인하기 위한 분석 결과입니다."
            plt.figure(figsize=(10, 5)); sns.countplot(x=sel_v[0], data=df, palette="pastel"); plot_img = get_plot_buffer()

    # 3) T-검정 (모든 유형 포함)
    elif method == "T-검정":
        t_mode = st.radio("세부 유형 선택", list(TTEST_SUB_GUIDES.keys()), horizontal=True)
        st.markdown(f'<div class="sub-method-info">💡 {TTEST_SUB_GUIDES[t_mode]}</div>', unsafe_allow_html=True)
        
        if t_mode == "독립표본":
            g, y = st.selectbox("집단 변수 (범주형)", all_cols), st.selectbox("결과과 변수 (연속형)", num_cols)
            if st.button("분석 실행"):
                gps = df[g].unique()
                g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                t_stat, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                final_df = pd.DataFrame({"변수명": [y], "t값": [f"{t_stat:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = get_auto_interpretation("T-검정", p, t_type="독립표본")
                plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df, palette="mako"); plot_img = get_plot_buffer()
        
        elif t_mode == "대응표본":
            v1, v2 = st.selectbox("사전 변수 (연속형)", num_cols), st.selectbox("사후 변수 (연속형)", num_cols)
            if st.button("분석 실행"):
                t_stat, p = stats.ttest_rel(df[v1].dropna(), df[v2].dropna())
                final_df = pd.DataFrame({"비교": [f"{v1} vs {v2}"], "t값": [f"{t_stat:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = get_auto_interpretation("T-검정", p, t_type="대응표본")
                plt.figure(figsize=(6, 5)); sns.pointplot(data=df[[v1, v2]], palette="flare"); plot_img = get_plot_buffer()
        
        elif t_mode == "단일표본":
            v, mu = st.selectbox("분석 변수 (연속형)", num_cols), st.number_input("검정 기준값", value=0.0)
            if st.button("분석 실행"):
                t_stat, p = stats.ttest_1samp(df[v].dropna(), mu)
                final_df = pd.DataFrame({"변수명": [v], "t값": [f"{t_stat:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
                interpretation = get_auto_interpretation("T-검정", p, t_type="단일표본")
                plt.figure(figsize=(6, 5)); sns.histplot(df[v], kde=True); plt.axvline(mu, color='red', ls='--'); plot_img = get_plot_buffer()

    # 4) 분산분석
    elif method == "분산분석":
        g, y = st.selectbox("집단 변수 (3집단 이상 범주형)", all_cols), st.selectbox("결과 변수 (연속형)", num_cols)
        if st.button("분석 실행"):
            groups = [df[df[g]==val][y].dropna() for val in df[g].unique()]
            f_val, p = stats.f_oneway(*groups)
            final_df = pd.DataFrame({"변수명": [y], "F값": [f"{f_val:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
            interpretation = get_auto_interpretation("분산분석", p)
            plt.figure(figsize=(8, 5)); sns.boxplot(x=g, y=y, data=df, palette="viridis"); plot_img = get_plot_buffer()

    # 5) 상관분석
    elif method == "상관분석":
        v1, v2 = st.selectbox("변수 1 (연속형)", num_cols), st.selectbox("변수 2 (연속형)", num_cols)
        if st.button("분석 실행"):
            r, p = stats.pearsonr(df[v1].dropna(), df[v2].dropna())
            final_df = pd.DataFrame({"분석 변수": [f"{v1} & {v2}"], "상관계수(r)": [f"{r:.2f}"], "p값": [f"{format_p(p)}{get_stars(p)}"]})
            interpretation = get_auto_interpretation("상관분석", p, r_val=r)
            plt.figure(figsize=(7, 5)); sns.regplot(x=v1, y=v2, data=df, line_kws={'color':'#0d9488'}); plot_img = get_plot_buffer()

    # 6) 회귀분석
    elif method == "회귀분석":
        reg_t = st.radio("유형", ["선형 회귀 (결과가 수치일 때)", "로지스틱 회귀 (결과가 발생여부일 때)"], horizontal=True)
        x_vars, y_var = st.multiselect("독립 변수 선택", num_cols), st.selectbox("종속 변수 선택", num_cols)
        if st.button("분석 실행") and x_vars:
            X = sm.add_constant(df[x_vars])
            if "선형" in reg_t:
                model = sm.OLS(df[y_var], X).fit(); p_val = model.f_pvalue
                final_df = pd.DataFrame({"B (계수)": model.params, "표준오차": model.bse, "t값": model.tvalues, "p값": model.pvalues}).reset_index()
            else:
                model = sm.Logit(df[y_var], X).fit(disp=0); p_val = model.llr_pvalue; conf = model.conf_int()
                final_df = pd.DataFrame({"B": model.params, "OR (오즈비)": np.exp(model.params), "Lower CI": np.exp(conf[0]), "Upper CI": np.exp(conf[1]), "p": model.pvalues}).reset_index()
            interpretation = get_auto_interpretation("회귀분석", p_val); plt.figure(figsize=(8, 4)); sns.heatmap(df[x_vars + [y_var]].corr(), annot=True, cmap="YlGnBu"); plot_img = get_plot_buffer()
            final_df['p값'] = final_df.iloc[:, -1].apply(lambda x: f"{format_p(x)}{get_stars(x)}")

    # 결과 출력
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 결과 및 리포트</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1.5, 1])
        with c1: 
            st.table(final_df)
            st.info(f"결과 해석 안내: {interpretation}")
        with c2: 
            if plot_img: st.image(plot_img)
        st.download_button("📄 워드 리포트 다운로드", data=create_word_report(final_df, interpretation, plot_img), file_name=f"STATERA_Report.docx")

else:
    st.markdown("""<div class="landing-zone"><div style="font-size: 3.5rem; margin-bottom: 20px;">⬆️</div><h3 style="color: #0f172a; margin-bottom: 10px;">분석을 시작하려면 파일을 업로드하세요</h3><p style="color: #64748b;">파일이 로드되면 전문 통계 가이드와 분석 옵션이 활성화됩니다.</p></div>""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. 연구 윤리 안내 (최하단 고정)
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
""", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #cbd5e1; margin-top: 20px; font-size: 0.8rem;'>STATistical Engine for Research & Analysis | ANDA Lab Jeongin Choe</div>", unsafe_allow_html=True)
