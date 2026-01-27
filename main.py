import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import het_breuschpagan
import io
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
from docx.shared import Inches

# -----------------------------------------------------------------------------
# 1. UI 스타일링 및 테마 설정 (Pretendard 적용)
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
    
    /* 가정 검정 박스 스타일 (폰트 통일용) */
    .assumption-box {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; font-size: 0.95rem; color: #334155; line-height: 1.6; margin-bottom: 15px; }}
    
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
        "desc": "연속형 변수의 평균, 표준편차, 왜도, 첨도 등을 산출하여 데이터의 전반적인 경향을 파악합니다.",
        "독립": "해당 없음", "종속": "연속형 변수",
        "use": "연구 대상자의 주요 수치형 지표를 요약할 때 사용합니다."
    },
    "빈도분석": {
        "title": "📊 빈도분석 (Frequency Analysis)",
        "desc": "범주형 변수의 빈도, 백분율, 누적 비율을 산출하여 대상자의 분포를 확인합니다.",
        "독립": "해당 없음", "종속": "범주형 변수",
        "use": "성별, 학력 등 대상자의 일반적 특성을 보고할 때 사용합니다."
    },
    "T-검정": {
        "title": "👥 T-검정 (T-test)",
        "desc": "집단 간 평균 차이, 95% 신뢰구간, 효과크기(Cohen's d)를 분석합니다.",
        "독립": "범주형 (2집단)", "종속": "연속형 변수",
        "use": "두 그룹 간의 결과값 차이를 비교하고 싶을 때 사용합니다."
    },
    "분산분석": {
        "title": "🏫 분산분석 (ANOVA)",
        "desc": "세 개 이상의 그룹 간 평균 차이와 효과크기(Eta-squared)를 분석합니다.",
        "독립": "범주형 (3집단 이상)", "종속": "연속형 변수",
        "use": "학력이나 연령대별 점수 차이 분석 시 사용합니다."
    },
    "상관분석": {
        "title": "🔗 상관분석 (Correlation Analysis)",
        "desc": "다수 변수 간의 기술통계(평균, SD)와 Pearson 상관계수 행렬을 통합 분석합니다.",
        "독립": "연속형", "종속": "연속형",
        "use": "변수들 간의 관계성을 종합적으로 보고할 때 사용합니다."
    },
    "회귀분석": {
        "title": "🎯 회귀분석 (Regression Analysis)",
        "desc": "독립변수의 영향력, 모형 적합도(R²), 계수의 신뢰구간을 산출합니다.",
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
# 4. 유틸리티 및 [가정 검정 & 해석 엔진]
# -----------------------------------------------------------------------------
def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p): return "<.001" if p < .001 else f"{p:.3f}"

# --- 가정 검정 함수들 (강조 제거됨) ---
def check_normality_shapiro(data, name):
    """정규성 검정 (N < 30: Shapiro-Wilk, N >= 30: CLT)"""
    data = data.dropna()
    n = len(data)
    if n < 3: return "N < 3 (검정 불가)", False
    
    if n >= 30:
        return f"표본 수 {n}개로 대표본(N≥30)에 해당하여 중심극한정리(CLT)에 의해 정규성 가정을 충족한 것으로 간주합니다.", True
    else:
        stat, p = stats.shapiro(data)
        if p >= 0.05:
            return f"Shapiro-Wilk 검정 결과(p={format_p(p)}), 정규성 가정을 만족합니다.", True
        else:
            return f"Shapiro-Wilk 검정 결과(p={format_p(p)}), 정규성 가정을 위배할 가능성이 있습니다.", False

def check_homogeneity_levene(group_data_list):
    """등분산성 검정 (Levene)"""
    stat, p = stats.levene(*group_data_list)
    if p >= 0.05:
        return f"Levene 검정 결과(p={format_p(p)}), 등분산 가정을 만족합니다.", True
    else:
        return f"Levene 검정 결과(p={format_p(p)}), 등분산 가정을 위배하였습니다 (이분산).", False

def check_independence_dw(resid):
    """독립성 검정 (Durbin-Watson)"""
    dw = durbin_watson(resid)
    if 1.5 <= dw <= 2.5:
        return f"Durbin-Watson 통계량({dw:.2f})이 2에 가까워 잔차의 독립성 가정을 만족합니다.", True
    else:
        return f"Durbin-Watson 통계량({dw:.2f})이 기준(1.5~2.5)을 벗어나 자기상관 가능성이 있습니다.", False

def calc_vif(X):
    """다중공선성 (VIF) 계산"""
    vif_data = pd.DataFrame()
    vif_data["feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    return vif_data

def calc_cohens_d(x1, x2):
    """T-test용 효과크기(Cohen's d) 계산"""
    nx1, nx2 = len(x1), len(x2)
    s1, s2 = np.std(x1, ddof=1), np.std(x2, ddof=1)
    s_pooled = np.sqrt(((nx1 - 1) * s1**2 + (nx2 - 1) * s2**2) / (nx1 + nx2 - 2))
    return (np.mean(x1) - np.mean(x2)) / s_pooled

def calc_corr_ci(r, n, alpha=0.05):
    """상관계수의 95% 신뢰구간 계산"""
    if n <= 3: return np.nan, np.nan
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha/2)
    lo_z, hi_z = z - z_crit * se, z + z_crit * se
    return np.tanh(lo_z), np.tanh(hi_z)

# --- 해석 엔진 (강조 제거됨) ---
def interpret_effect_size(val, method):
    abs_val = abs(val)
    if method == "cohen_d":
        if abs_val < 0.2: return "작은(Small)"
        elif abs_val < 0.5: return "중간(Medium)"
        else: return "큰(Large)"
    elif method == "eta_sq": 
        if abs_val < 0.01: return "미미한"
        elif abs_val < 0.06: return "작은(Small)"
        elif abs_val < 0.14: return "중간(Medium)"
        else: return "큰(Large)"
    elif method == "pearson_r":
        if abs_val < 0.3: return "약한"
        elif abs_val < 0.7: return "뚜렷한"
        else: return "강한"
    return ""

def get_auto_interpretation(method, p_val, stats_dict=None):
    if stats_dict is None: stats_dict = {}
    is_sig = p_val < 0.05
    sig_text = "통계적으로 유의한 차이(또는 관계)가 확인되었습니다(p < .05)." if is_sig else "통계적으로 유의한 차이(또는 관계)가 확인되지 않았습니다(p >= .05)."
    
    explanation = ""
    # [수정] 기술통계, 빈도분석, 상관분석(표 형태)은 p-value 통합 해석 제외
    if method not in ["기술통계", "빈도분석", "상관분석"]:
        explanation = f"📌 [1. 결론 요약] {sig_text}\n\n"
    
    # 가정 검정 결과 요약
    assump_fails = stats_dict.get('assump_fails', [])
    if assump_fails:
        explanation += f"⚠️ [주의] 분석 가정 중 {', '.join(assump_fails)} 조건이 충족되지 않았습니다. 결과 해석에 주의가 필요합니다.\n\n"

    # 상세 해석
    if method == "기술통계":
        non_normal_vars = stats_dict.get('non_normal_vars', [])
        explanation = "📌 [데이터 분포 해석]\n"
        if not non_normal_vars:
            explanation += "분석된 변수들은 왜도(Abs < 2)와 첨도(Abs < 7) 기준 내에 있어, 정규분포와 유사한 형태를 보입니다."
        else:
            explanation += f"[{', '.join(non_normal_vars)}] 변수는 정규분포 형태에서 벗어나 있습니다 (Ref: West et al., 1995)."

    elif method == "빈도분석":
        explanation = "📌 [해석 가이드]\n'비율(%)'은 전체 대비 해당 범주의 크기를, '누적 비율'은 순차적으로 합산된 비중을 의미합니다. 데이터가 특정 범주에 편중되어 있는지 확인하십시오."

    elif method == "T-검정":
        d_val = stats_dict.get('d', 0)
        ci_lo, ci_hi = stats_dict.get('ci_lo', 0), stats_dict.get('ci_hi', 0)
        d_desc = interpret_effect_size(d_val, "cohen_d")
        explanation += f"📌 [2. 효과크기 및 신뢰구간]\n"
        explanation += f"- Cohen's d = {d_val:.2f}: 두 집단 간에는 '{d_desc}' 수준의 실질적 차이가 존재합니다.\n"
        explanation += f"- 95% 신뢰구간 [{ci_lo:.2f}, {ci_hi:.2f}]: 반복 연구 시, 실제 평균 차이는 이 범위 내에 존재할 확률이 95%입니다."

    elif method == "분산분석":
        eta = stats_dict.get('eta', 0)
        eta_desc = interpret_effect_size(eta, "eta_sq")
        explanation += f"📌 [2. 효과크기 해석]\n"
        explanation += f"- Eta-squared ($\eta^2$) = {eta:.3f}: 독립 변수(집단 구분)가 종속 변수의 변동을 약 {eta*100:.1f}% 설명하고 있으며, 이는 '{eta_desc}' 수준의 설명력입니다."

    elif method == "상관분석":
        explanation = "📌 [표 해석 가이드]\n"
        explanation += "- M: 평균, SD: 표준편차\n"
        explanation += "- 대각선 아래의 수치는 두 변수 간의 Pearson 상관계수(r)입니다.\n"
        explanation += "- 별표(*): * p<.05, ** p<.01, *** p<.001 수준에서 통계적으로 유의함을 의미합니다."

    elif method == "회귀분석":
        r2 = stats_dict.get('r2', 0)
        explanation += f"📌 [2. 모형 적합도 해석]\n"
        explanation += f"- 결정계수($R^2$) = {r2:.3f}: 구축된 회귀 모형은 종속 변수 전체 변동의 약 {r2*100:.1f}%를 설명하고 있습니다.\n"
        explanation += "- 각 독립 변수의 B(비표준화 계수) 신뢰구간이 0을 포함하지 않을 때, 해당 변수는 유의한 영향력이 있다고 판단합니다."

    return explanation

def create_word_report(df, interpretation, plot_buf=None, assumption_text=""):
    doc = Document(); doc.add_heading('STATERA Analysis Report', 0)
    
    if assumption_text:
        doc.add_heading('Assumption Checks', level=1)
        doc.add_paragraph(assumption_text.replace("<br>", "\n"))

    doc.add_heading('Statistical Results', level=1)
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
        
    if plot_buf: doc.add_heading('Visualization', level=1); doc.add_picture(plot_buf, width=Inches(5.5))
    doc.add_heading('AI Interpretation', level=1); doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0); return bio

def get_plot_buffer():
    buf = io.BytesIO(); plt.savefig(buf, format='png', bbox_inches='tight', dpi=300); buf.seek(0); plt.close(); return buf

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
    assumption_report = "" 
    assump_fails = [] 

    # -------------------------------------------------------------------------
    # 1) 기술통계
    # -------------------------------------------------------------------------
    if method == "기술통계":
        sel_v = st.multiselect("분석할 연속형 변수를 선택하세요", num_cols)
        if st.button("분석 실행") and sel_v:
            desc = df[sel_v].describe().T
            desc['skew'] = df[sel_v].skew()
            desc['kurt'] = df[sel_v].kurt()
            
            final_df = desc[['count', 'mean', 'std', 'min', '50%', 'max', 'skew', 'kurt']].reset_index()
            final_df.columns = ['변수명', 'N', '평균(M)', '표준편차(SD)', '최솟값', '중위수(Median)', '최댓값', '왜도', '첨도']
            
            non_normal_vars = []
            for idx, row in final_df.iterrows():
                if abs(row['왜도']) >= 2 or abs(row['첨도']) >= 7:
                    non_normal_vars.append(row['변수명'])
            
            interpretation = get_auto_interpretation("기술통계", 1.0, {'non_normal_vars': non_normal_vars})
            plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v], palette="Set2"); plot_img = get_plot_buffer()

    # -------------------------------------------------------------------------
    # 2) 빈도분석
    # -------------------------------------------------------------------------
    elif method == "빈도분석":
        sel_v = st.multiselect("분석할 범주형 변수를 선택하세요", all_cols)
        if st.button("분석 실행") and sel_v:
            res_list = []
            for col in sel_v:
                c = df[col].value_counts().reset_index()
                c.columns = ['범주', '빈도(N)']
                total = c['빈도(N)'].sum()
                c['비율(%)'] = (c['빈도(N)'] / total * 100).round(1)
                c['누적 비율(%)'] = c['비율(%)'].cumsum()
                c.insert(0, '변수명', col)
                res_list.append(c)
            final_df = pd.concat(res_list)
            interpretation = get_auto_interpretation("빈도분석", 1.0)
            plt.figure(figsize=(10, 5)); sns.countplot(x=sel_v[0], data=df, palette="pastel"); plot_img = get_plot_buffer()

    # -------------------------------------------------------------------------
    # 3) T-검정
    # -------------------------------------------------------------------------
    elif method == "T-검정":
        t_mode = st.radio("세부 유형 선택", list(TTEST_SUB_GUIDES.keys()), horizontal=True)
        st.markdown(f'<div class="sub-method-info">💡 {TTEST_SUB_GUIDES[t_mode]}</div>', unsafe_allow_html=True)
        
        if t_mode == "독립표본":
            g, y = st.selectbox("집단 변수 (범주형)", all_cols), st.selectbox("결과 변수 (연속형)", num_cols)
            if st.button("분석 실행"):
                gps = df[g].unique()
                if len(gps) != 2:
                    st.error("독립표본 T-검정은 집단이 정확히 2개여야 합니다.")
                else:
                    g1 = df[df[g]==gps[0]][y].dropna()
                    g2 = df[df[g]==gps[1]][y].dropna()
                    
                    msg_n1, pass_n1 = check_normality_shapiro(g1, gps[0])
                    msg_n2, pass_n2 = check_normality_shapiro(g2, gps[1])
                    if not (pass_n1 and pass_n2): assump_fails.append("정규성")

                    msg_var, equal_var = check_homogeneity_levene([g1, g2])
                    if not equal_var: assump_fails.append("등분산성")
                    
                    assumption_report = f"- 정규성: {msg_n1}<br>- 정규성: {msg_n2}<br>- 등분산성: {msg_var}"
                    
                    t_stat, p = stats.ttest_ind(g1, g2, equal_var=equal_var)
                    
                    mean_diff = np.mean(g1) - np.mean(g2)
                    n1, n2 = len(g1), len(g2)
                    se_diff = np.sqrt(np.var(g1, ddof=1)/n1 + np.var(g2, ddof=1)/n2)
                    
                    df_t = n1 + n2 - 2
                    ci_crit = stats.t.ppf(0.975, df_t)
                    ci_lower = mean_diff - ci_crit * se_diff
                    ci_upper = mean_diff + ci_crit * se_diff
                    d_val = calc_cohens_d(g1, g2)

                    final_df = pd.DataFrame({
                        "변수명": [y],
                        "집단비교": [f"{gps[0]} vs {gps[1]}"],
                        "평균 차이": [f"{mean_diff:.2f}"],
                        "표준오차(SE)": [f"{se_diff:.2f}"],
                        "95% CI (Lower)": [f"{ci_lower:.2f}"],
                        "95% CI (Upper)": [f"{ci_upper:.2f}"],
                        "t값": [f"{t_stat:.2f}"],
                        "df": [f"{df_t}"],
                        "p값": [f"{format_p(p)}{get_stars(p)}"],
                        "Cohen's d": [f"{d_val:.2f}"]
                    })
                    
                    interpretation = get_auto_interpretation("T-검정", p, {'d': d_val, 'ci_lo': ci_lower, 'ci_hi': ci_upper, 'assump_fails': assump_fails})
                    if not equal_var: interpretation += "\n(참고: 등분산 위배로 Welch's T-test 적용됨)"
                    plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df, palette="mako"); plot_img = get_plot_buffer()
        
        elif t_mode == "대응표본":
            v1, v2 = st.selectbox("사전 변수", num_cols), st.selectbox("사후 변수", num_cols)
            if st.button("분석 실행"):
                pair_data = df[[v1, v2]].dropna()
                diff = pair_data[v1] - pair_data[v2]
                
                msg_n, pass_n = check_normality_shapiro(diff, "Difference")
                if not pass_n: assump_fails.append("정규성(차이값)")
                assumption_report = f"- 정규성(차이값): {msg_n}"

                t_stat, p = stats.ttest_rel(pair_data[v1], pair_data[v2])
                
                mean_diff = np.mean(diff)
                se_diff = stats.sem(diff)
                df_t = len(diff) - 1
                ci = stats.t.interval(0.95, df_t, loc=mean_diff, scale=se_diff)
                d_val = mean_diff / np.std(diff, ddof=1) 

                final_df = pd.DataFrame({
                    "비교": [f"{v1} - {v2}"],
                    "평균 차이": [f"{mean_diff:.2f}"],
                    "표준오차(SE)": [f"{se_diff:.2f}"],
                    "95% CI (Lower)": [f"{ci[0]:.2f}"],
                    "95% CI (Upper)": [f"{ci[1]:.2f}"],
                    "t값": [f"{t_stat:.2f}"],
                    "p값": [f"{format_p(p)}{get_stars(p)}"],
                    "Cohen's d": [f"{d_val:.2f}"]
                })
                
                interpretation = get_auto_interpretation("T-검정", p, {'d': d_val, 'ci_lo': ci[0], 'ci_hi': ci[1], 'assump_fails': assump_fails})
                plt.figure(figsize=(6, 5)); sns.pointplot(data=pair_data, palette="flare"); plot_img = get_plot_buffer()

        elif t_mode == "단일표본":
            v, mu = st.selectbox("분석 변수", num_cols), st.number_input("검정 기준값", value=0.0)
            if st.button("분석 실행"):
                clean_data = df[v].dropna()
                msg_n, pass_n = check_normality_shapiro(clean_data, v)
                if not pass_n: assump_fails.append("정규성")
                assumption_report = f"- 정규성: {msg_n}"
                
                t_stat, p = stats.ttest_1samp(clean_data, mu)
                
                mean_val = np.mean(clean_data)
                mean_diff = mean_val - mu
                se = stats.sem(clean_data)
                ci = stats.t.interval(0.95, len(clean_data)-1, loc=mean_val, scale=se)

                final_df = pd.DataFrame({
                    "변수": [v],
                    "표본 평균": [f"{mean_val:.2f}"],
                    "차이(Mean-μ)": [f"{mean_diff:.2f}"],
                    "95% CI (Lower)": [f"{ci[0]:.2f}"],
                    "95% CI (Upper)": [f"{ci[1]:.2f}"],
                    "t값": [f"{t_stat:.2f}"],
                    "p값": [f"{format_p(p)}{get_stars(p)}"]
                })
                interpretation = get_auto_interpretation("T-검정", p, {'assump_fails': assump_fails})
                plt.figure(figsize=(6, 5)); sns.histplot(clean_data, kde=True); plt.axvline(mu, color='red', ls='--'); plot_img = get_plot_buffer()

    # -------------------------------------------------------------------------
    # 4) 분산분석
    # -------------------------------------------------------------------------
    elif method == "분산분석":
        g, y = st.selectbox("집단 변수 (3집단 이상)", all_cols), st.selectbox("결과 변수 (연속형)", num_cols)
        if st.button("분석 실행"):
            temp_df = df[[g, y]].dropna().rename(columns={g:'Group_Var', y:'Target_Var'})
            groups = [temp_df[temp_df['Group_Var']==val]['Target_Var'] for val in temp_df['Group_Var'].unique()]

            msg_var, equal_var = check_homogeneity_levene(groups)
            if not equal_var: assump_fails.append("등분산성")
            assumption_report = f"- 등분산성: {msg_var}<br>(참고: 정규성은 각 집단별 N>=30일 경우 CLT에 의해 충족 간주)"
            
            model = ols('Target_Var ~ C(Group_Var)', data=temp_df).fit()
            anova_table = anova_lm(model, typ=2)
            
            ss_between = anova_table.loc['C(Group_Var)', 'sum_sq']
            ss_resid = anova_table.loc['Residual', 'sum_sq']
            eta_sq = ss_between / (ss_between + ss_resid)
            
            f_val = anova_table.loc['C(Group_Var)', 'F']
            p_val = anova_table.loc['C(Group_Var)', 'PR(>F)']
            df_bet = int(anova_table.loc['C(Group_Var)', 'df'])
            df_resid = int(anova_table.loc['Residual', 'df'])

            final_df = pd.DataFrame({
                "요인": ["집단 간", "집단 내(오차)"],
                "제곱합(SS)": [f"{ss_between:.2f}", f"{ss_resid:.2f}"],
                "자유도(df)": [df_bet, df_resid],
                "평균제곱(MS)": [f"{ss_between/df_bet:.2f}", f"{ss_resid/df_resid:.2f}"],
                "F값": [f"{f_val:.2f}", ""],
                "p값": [f"{format_p(p_val)}{get_stars(p_val)}", ""],
                "Eta-squared": [f"{eta_sq:.3f}", ""]
            })
            
            interpretation = get_auto_interpretation("분산분석", p_val, {'eta': eta_sq, 'assump_fails': assump_fails})
            if not equal_var: interpretation += "\n(권고: 등분산 위배 시 Welch's ANOVA를 고려하십시오.)"
            plt.figure(figsize=(8, 5)); sns.boxplot(x=g, y=y, data=df, palette="viridis"); plot_img = get_plot_buffer()

    # -------------------------------------------------------------------------
    # 5) 상관분석 (업그레이드: APA 스타일 표 생성)
    # -------------------------------------------------------------------------
    elif method == "상관분석":
        sel_vars = st.multiselect("분석할 변수들을 모두 선택하세요 (2개 이상)", num_cols)
        
        if st.button("분석 실행") and len(sel_vars) >= 2:
            target_df = df[sel_vars].dropna()
            n = len(target_df)
            
            desc_stats = target_df.describe().T[['mean', 'std']]
            cols = ['M', 'SD'] + [str(i+1) for i in range(len(sel_vars))]
            corr_table = pd.DataFrame(index=sel_vars, columns=cols)
            
            check_normality_msgs = []
            
            for i, var_row in enumerate(sel_vars):
                corr_table.loc[var_row, 'M'] = f"{desc_stats.loc[var_row, 'mean']:.2f}"
                corr_table.loc[var_row, 'SD'] = f"{desc_stats.loc[var_row, 'std']:.2f}"
                
                msg_n, pass_n = check_normality_shapiro(target_df[var_row], var_row)
                if not pass_n: assump_fails.append(f"정규성({var_row})")
                check_normality_msgs.append(f"- {var_row}: {msg_n}")

                for j, var_col in enumerate(sel_vars):
                    if i == j:
                        corr_table.iloc[i, j+2] = "1"
                    elif i > j:
                        r, p = stats.pearsonr(target_df[var_row], target_df[var_col])
                        star = get_stars(p)
                        corr_table.iloc[i, j+2] = f"{r:.2f}{star}"
                    else:
                        corr_table.iloc[i, j+2] = ""
            
            new_index = [f"{i+1}. {v}" for i, v in enumerate(sel_vars)]
            corr_table.index = new_index
            
            final_df = corr_table
            assumption_report = "<br>".join(check_normality_msgs)
            
            interpretation = get_auto_interpretation("상관분석", 1.0, {'assump_fails': assump_fails})
            
            max_r = 0
            max_pair = ""
            for i in range(len(sel_vars)):
                for j in range(i):
                    val_str = str(corr_table.iloc[i, j+2]).replace('*', '')
                    try:
                        val = float(val_str)
                        if abs(val) > abs(max_r):
                            max_r = val
                            max_pair = f"'{sel_vars[i]}' - '{sel_vars[j]}'"
                    except: pass
            
            if max_pair:
                interpretation += f"\n💡 [핵심 발견] 분석된 변수 중 {max_pair} 간의 관계가 가장 강하게 나타났습니다 (r={max_r:.2f})."

            plt.figure(figsize=(8, 6)); sns.heatmap(target_df.corr(), annot=True, cmap="coolwarm", vmin=-1, vmax=1); plot_img = get_plot_buffer()

    # -------------------------------------------------------------------------
    # 6) 회귀분석
    # -------------------------------------------------------------------------
    elif method == "회귀분석":
        reg_t = st.radio("유형", ["선형 회귀", "로지스틱 회귀"], horizontal=True)
        x_vars = st.multiselect("독립 변수 선택", [c for c in num_cols])
        y_var = st.selectbox("종속 변수 선택", num_cols)
        
        if st.button("분석 실행") and x_vars:
            X = sm.add_constant(df[x_vars].dropna())
            Y = df[y_var].loc[X.index] 

            if "선형" in reg_t:
                model = sm.OLS(Y, X).fit()
                
                # 가정 검정
                vif_df = calc_vif(X)
                high_vif = vif_df[vif_df['VIF'] > 10]['feature'].tolist()
                if "const" in high_vif: high_vif.remove("const")
                
                msg_dw, pass_dw = check_independence_dw(model.resid)
                _, p_het, _, _ = het_breuschpagan(model.resid, model.model.exog)
                pass_het = p_het >= 0.05
                msg_het = f"Breusch-Pagan p={format_p(p_het)} (>=.05 만족)" if pass_het else "등분산성 위배 (p<.05)"

                if high_vif: assump_fails.append(f"다중공선성({', '.join(high_vif)})")
                if not pass_dw: assump_fails.append("잔차 독립성")
                if not pass_het: assump_fails.append("잔차 등분산성")
                
                assumption_report = f"- 다중공선성: {'문제 없음' if not high_vif else f'의심 변수: {high_vif}'}<br>- 독립성: {msg_dw}<br>- 등분산성: {msg_het}"

                conf_int = model.conf_int(alpha=0.05)
                conf_int.columns = ['Lower CI', 'Upper CI']
                
                final_df = pd.DataFrame({
                    "B (비표준화 계수)": model.params,
                    "표준오차(SE)": model.bse,
                    "t값": model.tvalues,
                    "p값": model.pvalues,
                    "95% CI (Lower)": conf_int['Lower CI'],
                    "95% CI (Upper)": conf_int['Upper CI']
                }).reset_index().rename(columns={'index':'변수명'})
                
                p_val_model = model.f_pvalue
                stats_info = {'r2': model.rsquared, 'assump_fails': assump_fails}
                
            else: 
                model = sm.Logit(Y, X).fit(disp=0)
                assumption_report = "- 로지스틱 회귀는 정규성/등분산성 가정이 요구되지 않습니다."
                
                conf_int = model.conf_int()
                odds_ratio = np.exp(model.params)
                or_ci_lower = np.exp(conf_int[0])
                or_ci_upper = np.exp(conf_int[1])
                
                final_df = pd.DataFrame({
                    "B (계수)": model.params,
                    "표준오차(SE)": model.bse,
                    "Wald Chi-Sq": np.square(model.tvalues),
                    "p값": model.pvalues,
                    "Odds Ratio (OR)": odds_ratio,
                    "95% CI (Lower)": or_ci_lower,
                    "95% CI (Upper)": or_ci_upper
                }).reset_index().rename(columns={'index':'변수명'})
                
                p_val_model = model.llr_pvalue
                stats_info = {'r2': model.prsquared, 'assump_fails': []}

            final_df['p값'] = final_df['p값'].apply(lambda x: f"{format_p(x)}{get_stars(x)}")
            interpretation = get_auto_interpretation("회귀분석", p_val_model, stats_dict=stats_info)
            plt.figure(figsize=(8, 4)); sns.heatmap(df[x_vars + [y_var]].corr(), annot=True, cmap="YlGnBu"); plot_img = get_plot_buffer()

    # 결과 출력
    if final_df is not None:
        st.markdown('<div class="section-title"><span class="step-badge">02</span> 분석 결과 및 리포트</div>', unsafe_allow_html=True)
        
        # 가정 검정 결과를 박스(assumption-box class) 안에 출력
        if assumption_report:
            with st.expander("🔍 통계적 가정 검정 결과 (Assumption Checks)", expanded=True):
                st.markdown(f"""
                <div class="assumption-box">
                    {assumption_report}
                </div>
                """, unsafe_allow_html=True)
                
                if assump_fails:
                    st.error(f"⚠️ 위배된 가정: {', '.join(assump_fails)} (해석 시 주의가 필요합니다.)")
                else:
                    st.success("✅ 주요 통계적 가정을 모두 충족합니다.")

        c1, c2 = st.columns([1.5, 1])
        with c1: 
            st.table(final_df)
            st.info(interpretation)
        with c2: 
            if plot_img: st.image(plot_img)
        st.download_button("📄 워드 리포트 다운로드", data=create_word_report(final_df, interpretation, plot_img, assumption_report), file_name=f"STATERA_Report.docx")

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
