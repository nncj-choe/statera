import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.outliers_influence import variance_inflation_factor

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 Custom CSS (STATERA UI 디자인)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA - Nursing Research Platform", layout="wide", page_icon="📊")

# CSS 주입: 사이드바, 카드, 폰트 등 디자인 요소
st.markdown("""
<style>
    / 전체 폰트 및 배경 /
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    
    / 카드 스타일 (버튼을 카드로 변환) /
    div.stButton > button:first-child {
        background-color: white;
        color: #2c3e50;
        height: 200px;
        width: 100%;
        border-radius: 10px;
        border: 1px solid #ddd;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: 0.3s;
        text-align: left;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: flex-start;
    }
    div.stButton > button:first-child:hover {
        border-color: #18bc9c;
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }
    
    / 사이드바 스타일 커스텀 /
    [data-testid="stSidebar"] {
        background-color: #2c3e50;
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #18bc9c !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #ecf0f1 !important;
    }
    
    / 탭 스타일 /
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f2f6;
        border-radius: 5px 5px 0 0;
        color: #57606f;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #fff;
        color: #18bc9c;
        border-top: 2px solid #18bc9c;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태 초기화 (페이지 네비게이션용)
# -----------------------------------------------------------------------------
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'method' not in st.session_state:
    st.session_state.method = None

def go_home():
    st.session_state.page = 'home'
    st.session_state.method = None

def go_analysis(method_name):
    st.session_state.page = 'analysis'
    st.session_state.method = method_name

# -----------------------------------------------------------------------------
# 3. 사이드바 (공통)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📊 STATERA")
    st.markdown("Nursing Research Educational Platform")
    st.caption("🎓 Learning Mode v1.2")
    
    st.markdown("---")
    st.markdown("### Curriculum")
    st.markdown("- 분석 라이브러리")
    st.markdown("- 기초 통계 탐색")
    st.markdown("- 가정 검정 마스터")
    st.markdown("- 학문적 글쓰기")
    st.markdown("- 통계 용어 대사전")
    
    st.markdown("---")
    st.markdown("**Developer Info**")
    st.caption("nncj91@snu.ac.kr")
    st.caption("ANDA LAB | SNU CON")
    st.caption("BY JEONGIN CHOE")

# -----------------------------------------------------------------------------
# 4. 메인 로직
# -----------------------------------------------------------------------------

# [페이지 1] 홈 화면
if st.session_state.page == 'home':
    st.header("학습할 통계 기법을 선택하세요")
    st.markdown("연구 목적에 맞는 카드를 선택하면 분석 요건, 가정 검정, 학술적 해석 가이드를 제공합니다.")
    st.markdown("---")

    # 3x2 그리드 레이아웃
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 데이터의 특성 파악\n\n대상자의 일반적 특성과 수치적 분포를 요약합니다.\n(DESC TEST)"):
            go_analysis("desc")
        if st.button("🔗 변수 간 관계 (Correlation)\n\n두 연속형 변수 사이의 선형적 관련성을 분석합니다.\n(CORR TEST)"):
            go_analysis("corr")

    with col2:
        if st.button("👥 집단 간 차이 비교 (t-test)\n\n두 집단 간의 평균 차이를 분석합니다.\n(TTEST TEST)"):
            go_analysis("ttest")
        if st.button("📈 영향 요인 분석 (Regression)\n\n독립변수가 종속변수에 미치는 영향력과 설명력을 분석합니다.\n(REG TEST)"):
            go_analysis("reg")

    with col3:
        if st.button("🏢 세 집단 이상 비교 (ANOVA)\n\n학력, 직급 등 3개 이상의 집단 간 평균 차이를 분석합니다.\n(ANOVA TEST)"):
            go_analysis("anova")
        if st.button("📊 범주형 빈도 비교 (Chi-square)\n\n두 범주형 변수 간의 연관성이나 비율의 차이를 분석합니다.\n(CHI TEST)"):
            go_analysis("chi")
            
    st.markdown("---")
    st.subheader("📁 데이터 업로드 시뮬레이션")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요 (한글 포함 시 EUC-KR 또는 UTF-8 권장)", type="csv")

# [페이지 2] 분석 화면
elif st.session_state.page == 'analysis':
    st.button("← 메인으로 돌아가기", on_click=go_home)
    
    # 데이터 로드
    df = None
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='euc-kr') # 한글 깨짐 방지 우선 시도
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8')
    
    # 분석 제목 설정
    method_titles = {
        "desc": "데이터의 특성 파악 (Descriptive Stats)",
        "ttest": "집단 간 차이 비교 (T-test)",
        "anova": "세 집단 이상 비교 (One-way ANOVA)",
        "corr": "변수 간 관계 파악 (Correlation)",
        "reg": "영향 요인 분석 (Linear Regression)",
        "chi": "범주형 빈도 비교 (Chi-square)"
    }
    
    st.title(method_titles[st.session_state.method])
    
    if df is None:
        st.warning("⚠️ 분석을 실행하려면 먼저 CSV 데이터를 업로드해주세요. (홈 화면 하단)")
    else:
        # ---------------------------------------------------------------------
        # 변수 선택 UI (Sidebar in Main Page style)
        # ---------------------------------------------------------------------
        st.markdown("### 1. 변수 설정")
        col_input, col_dummy = st.columns([1, 2]) # 입력란 크기 조절
        
        with col_input:
            vars = df.columns.tolist()
            params = {}
            
            if st.session_state.method == "desc":
                params['vars'] = st.multiselect("분석할 연속형 변수 선택", vars)
            
            elif st.session_state.method == "ttest":
                ttest_type = st.selectbox("분석 유형", ["독립표본 (Independent)", "대응표본 (Paired)", "일표본 (One-sample)"])
                params['type'] = ttest_type
                if "독립" in ttest_type:
                    params['group'] = st.selectbox("그룹 변수 (2 집단)", vars)
                    params['target'] = st.selectbox("종속 변수 (점수)", vars)
                elif "대응" in ttest_type:
                    params['pre'] = st.selectbox("사전 변수 (Pre)", vars)
                    params['post'] = st.selectbox("사후 변수 (Post)", vars)
                else:
                    params['target'] = st.selectbox("검정 변수", vars)
                    params['mu'] = st.number_input("검정값 (Test Value)", value=0.0)
            
            elif st.session_state.method == "anova":
                params['group'] = st.selectbox("그룹 변수 (3개 이상 집단)", vars)
                params['target'] = st.selectbox("종속 변수 (점수)", vars)
                
            elif st.session_state.method == "corr":
                params['vars'] = st.multiselect("상관분석할 변수 (2개 이상)", vars)
                
            elif st.session_state.method == "reg":
                params['dep'] = st.selectbox("종속 변수 (Dependent)", vars)
                params['indep'] = st.multiselect("독립 변수 (Independent)", [v for v in vars if v != params['dep']])
                
            elif st.session_state.method == "chi":
                params['row'] = st.selectbox("행 변수 (Row)", vars)
                params['col'] = st.selectbox("열 변수 (Column)", vars)
        
        if st.button("분석 실행 (Run Analysis)", type="primary"):
            st.markdown("---")
            
            # -----------------------------------------------------------------
            # 결과 탭 구성
            # -----------------------------------------------------------------
            tab1, tab2, tab3, tab4 = st.tabs(["📊 데이터 보기", "🔍 가정 검정", "📈 분석 결과", "📝 학술적 해석"])
            
            with tab1:
                st.dataframe(df.head(20))
            
            # --- 로직 실행 ---
            try:
                # 1. 기술통계
                if st.session_state.method == "desc":
                    res = df[params['vars']].describe().T
                    res['skew'] = df[params['vars']].skew()
                    res['kurtosis'] = df[params['vars']].kurtosis()
                    
                    with tab2:
                        st.write("**정규성 가정 탐색**")
                        st.info("왜도(Skewness) < |3|, 첨도(Kurtosis) < |10| (또는 |7|) 인 경우 정규분포를 가정합니다.")
                    with tab3:
                        st.dataframe(res)
                    with tab4:
                        st.write("기술통계 결과는 위 표와 같습니다. 평균(Mean)과 표준편차(Std)를 논문에 기술하십시오.")

                # 2. T-test
                elif st.session_state.method == "ttest":
                    if "독립" in params['type']:
                        groups = df[params['group']].unique()
                        g1 = df[df[params['group']] == groups[0]][params['target']].dropna()
                        g2 = df[df[params['group']] == groups[1]][params['target']].dropna()
                        
                        # 가정 검정
                        levene = stats.levene(g1, g2)
                        shapiro_g1 = stats.shapiro(g1)
                        shapiro_g2 = stats.shapiro(g2)
                        
                        # t-test
                        equal_var = levene.pvalue > 0.05
                        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)
                        
                        with tab2:
                            st.write(f"1. 정규성(Shapiro): G1(p={shapiro_g1.pvalue:.3f}), G2(p={shapiro_g2.pvalue:.3f})")
                            st.write(f"2. 등분산성(Levene): F={levene.statistic:.3f}, p={levene.pvalue:.3f}")
                            if equal_var: st.success("등분산 가정이 충족되었습니다.")
                            else: st.warning("등분산 가정이 위배되어 Welch's t-test를 수행했습니다.")
                        
                        with tab3:
                            st.metric("t-statistic", f"{t_stat:.3f}")
                            st.metric("P-value", f"{p_val:.3f}")
                        
                        with tab4:
                            sig = "유의한 차이가 있습니다" if p_val < 0.05 else "유의한 차이가 없습니다"
                            st.write(f"분석 결과 t={t_stat:.3f}, p={p_val:.3f}로 두 집단 간에는 통계적으로 {sig}.")

                    elif "대응" in params['type']:
                        diff = (df[params['post']] - df[params['pre']]).dropna()
                        shapiro = stats.shapiro(diff)
                        t_stat, p_val = stats.ttest_rel(df[params['pre']], df[params['post']], nan_policy='omit')
                        
                        with tab2:
                            st.write(f"차이값의 정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        with tab3:
                            st.write(f"t = {t_stat:.3f}, p = {p_val:.3f}")
                        with tab4:
                            st.write(f"p-value가 {p_val:.3f}이므로, " + ("유의한 차이가 확인되었습니다." if p_val < 0.05 else "차이가 유의하지 않습니다."))

                    else: # One-sample
                        data = df[params['target']].dropna()
                        shapiro = stats.shapiro(data)
                        t_stat, p_val = stats.ttest_1samp(data, params['mu'])
                        
                        with tab2: st.write(f"정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        with tab3: st.write(f"t = {t_stat:.3f}, p = {p_val:.3f}")
                        with tab4: st.write(f"검정값({params['mu']})과 통계적으로 " + ("유의한 차이가 있습니다." if p_val < 0.05 else "차이가 없습니다."))

                # 3. ANOVA
                elif st.session_state.method == "anova":
                    model = ols(f"{params['target']} ~ C({params['group']})", data=df).fit()
                    anova_table = sm.stats.anova_lm(model, typ=2)
                    
                    resid = model.resid
                    shapiro = stats.shapiro(resid)
                    # Levene (그룹별 데이터 분리 필요)
                    grps = [d[params['target']].dropna() for _, d in df.groupby(params['group'])]
                    levene = stats.levene(*grps)
                    
                    with tab2:
                        st.write(f"1. 잔차 정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        st.write(f"2. 등분산성(Levene): p={levene.pvalue:.3f}")
                    
                    with tab3:
                        st.write("### ANOVA Table")
                        st.dataframe(anova_table)
                        if anova_table['PR(>F)'][0] < 0.05:
                            st.write("### Post-hoc (Tukey HSD)")
                            tukey = pairwise_tukeyhsd(df[params['target']].dropna(), df[params['group']].dropna())
                            st.text(tukey.summary())
                    
                    with tab4:
                        p_v = anova_table['PR(>F)'][0]
                        st.write(f"F={anova_table['F'][0]:.3f}, p={p_v:.3f} 입니다.")
                        if p_v < 0.05: st.write("집단 간 유의한 차이가 발견되었으므로 사후검정 결과를 참고하십시오.")
                        else: st.write("집단 간 통계적으로 유의한 차이가 없습니다.")

                # 4. Correlation
                elif st.session_state.method == "corr":
                    cols = params['vars']
                    corr_mat = df[cols].corr()
                    
                    # P-value matrix 계산
                    pval_mat = pd.DataFrame(index=cols, columns=cols)
                    for r in cols:
                        for c in cols:
                            if r == c: pval_mat.loc[r,c] = 1.0
                            else:
                                _, p = stats.pearsonr(df[r].dropna(), df[c].dropna())
                                pval_mat.loc[r,c] = p
                    
                    with tab2: st.info("상관분석은 각 변수의 정규성을 가정합니다.")
                    with tab3:
                        st.write("### Pearson Correlation Coefficient (r)")
                        st.dataframe(corr_mat)
                        st.write("### P-values")
                        st.dataframe(pval_mat)
                    with tab4:
                        st.write("상관계수(r)의 절대값이 0.7 이상이면 강한 상관관계, 0.4~0.6이면 중등도 상관관계로 해석합니다. (단, p < .05 조건)")

                # 5. Regression
                elif st.session_state.method == "reg":
                    formula = f"{params['dep']} ~ {' + '.join(params['indep'])}"
                    model = ols(formula, data=df).fit()
                    
                    # 가정 검정
                    dw = durbin_watson(model.resid)
                    shapiro = stats.shapiro(model.resid)
                    
                    with tab2:
                        st.write(f"1. 독립성(Durbin-Watson): {dw:.3f} (2에 가까울수록 독립)")
                        st.write(f"2. 잔차 정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        if len(params['indep']) > 1:
                            # VIF 계산 (상수항 추가 필요)
                            X = sm.add_constant(df[params['indep']].dropna())
                            vif_data = pd.DataFrame()
                            vif_data["Variable"] = X.columns
                            vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
                            st.write("3. 다중공선성(VIF)")
                            st.dataframe(vif_data[1:]) # 상수항 제외하고 출력
                    
                    with tab3:
                        st.text(model.summary())
                    
                    with tab4:
                        st.write(f"회귀모형의 설명력(Adj. R-squared)은 {model.rsquared_adj:.3f} 입니다.")
                        st.write("P>|t| 값이 0.05 미만인 독립변수가 종속변수에 유의한 영향을 미칩니다.")

                # 6. Chi-square
                elif st.session_state.method == "chi":
                    ct = pd.crosstab(df[params['row']], df[params['col']])
                    chi2, p, dof, expected = stats.chi2_contingency(ct)
                    
                    with tab2:
                        st.write("기대빈도 가정: 기대빈도가 5 미만인 셀이 전체의 20%를 넘지 않아야 합니다.")
                    with tab3:
                        st.write("### 관측 빈도 (Observed)")
                        st.dataframe(ct)
                        st.write("### 결과")
                        st.write(f"Chi2 statistic: {chi2:.3f}")
                        st.write(f"P-value: {p:.3f}")
                    with tab4:
                        sig = "유의한 연관성이 있습니다" if p < 0.05 else "서로 독립적입니다 (연관성 없음)"
                        st.write(f"검정 결과 p={p:.3f}로, 두 변수 간에는 {sig}.")
            
            except Exception as e:
                st.error(f"분석 중 오류가 발생했습니다: {e}")
                st.info("변수 유형(숫자형/문자형)이 올바른지, 결측치가 너무 많지 않은지 확인해주세요.")
