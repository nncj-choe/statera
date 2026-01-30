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
# 1. 페이지 설정 및 디자인 
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA - Nursing Research Platform", layout="wide", page_icon="📊")

# CSS: 사이드바 색상, 카드 디자인, 폰트 등을 강제로 덮어씌움
st.markdown("""
<style>
    / 폰트 설정 /
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

    / 사이드바 디자인 /
    section[data-testid="stSidebar"] {
        background-color: #2c3e50 !important; / 짙은 남색 배경 /
    }
    section[data-testid="stSidebar"] * {
        color: #ecf0f1 !important; / 흰색 텍스트 강제 적용 /
    }
    / 사이드바 내의 구분선 색상 변경 /
    section[data-testid="stSidebar"] hr {
        border-color: #7f8c8d !important;
    }

    / [메인 버튼 -> 카드형 디자인 변환] /
    div.stButton > button:first-child {
        background-color: #ffffff;
        color: #2c3e50;
        height: 180px; / 카드 높이 고정 /
        width: 100%;
        border-radius: 12px;
        border: 1px solid #dfe6e9;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        text-align: left;
        padding: 20px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start; / 위쪽 정렬 /
        align-items: flex-start;
        white-space: pre-wrap; / 줄바꿈 허용 /
    }
    
    / 버튼 호버 효과 /
    div.stButton > button:first-child:hover {
        border-color: #18bc9c; /* 녹색 테두리 */
        transform: translateY(-5px); /* 위로 살짝 떠오름 */
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        color: #18bc9c;
    }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1rem;
        font-weight: bold;
    }
    
    /* 헤더 스타일 */
    h1, h2, h3 { color: #2c3e50; font-weight: 700; }
    
    /* 카드 내부 텍스트 스타일링 (버튼 텍스트용) */
    .card-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; display: block; }
    .card-desc { font-size: 13px; color: #636e72; font-weight: normal; display: block; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 상태 관리 (페이지 이동 로직)
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
# 3. 사이드바 (STATERA 네비게이션)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📊 STATERA")
    st.markdown("**Nursing Research Educational Platform**")
    st.caption("🎓 Learning Mode v1.2")
    
    st.markdown("---")
    st.markdown("### Curriculum")
    # 실제 링크 기능은 없지만 UI 구색을 맞춤
    st.markdown("🔹 분석 라이브러리")
    st.markdown("🔹 기초 통계 탐색")
    st.markdown("🔹 가정 검정 마스터")
    st.markdown("🔹 학문적 글쓰기")
    st.markdown("🔹 통계 용어 대사전")
    
    st.markdown("---")
    st.markdown("### Developer Info")
    st.markdown("""
    <div style='font-size: 12px; line-height: 1.5; color: #bdc3c7;'>
    nncj91@snu.ac.kr<br>
    ANDA LAB | SNU CON<br>
    BY JEONGIN CHOE<br>
    Seoul National Univ.
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. 메인 화면 로직
# -----------------------------------------------------------------------------

# [HOME 페이지] 분석 방법 선택 (카드형 UI)
if st.session_state.page == 'home':
    st.title("학습할 통계 기법을 선택하세요")
    st.markdown("연구 목적에 맞는 카드를 선택하면 분석 요건, 가정 검정, 학술적 해석 가이드를 제공합니다.")
    st.markdown("---")

    # 카드 레이아웃 (3열)
    col1, col2, col3 = st.columns(3)
    
    # 버튼 텍스트에 HTML 스타일 적용이 안 되므로, 텍스트 배치로 시각적 효과를 줌
    with col1:
        if st.button("📋 빈도분석 (Frequency)\n\n범주형 변수의 빈도와 비율을\n확인합니다.\n(FREQ TEST)"):
            go_analysis("freq")
        if st.button("🔗 변수 간 관계 (Correlation)\n\n두 연속형 변수 사이의\n선형적 관련성을 분석합니다.\n(CORR TEST)"):
            go_analysis("corr")
        if st.button("📊 범주형 비교 (Chi-square)\n\n두 범주형 변수 간의\n연관성을 분석합니다.\n(CHI TEST)"):
            go_analysis("chi")

    with col2:
        if st.button("📈 데이터 특성 (Descriptive)\n\n연속형 변수의 평균, 표준편차,\n정규성을 탐색합니다.\n(DESC TEST)"):
            go_analysis("desc")
        if st.button("👥 집단 차이 비교 (t-test)\n\n두 집단 간의 평균 차이를\n분석합니다.\n(TTEST TEST)"):
            go_analysis("ttest")

    with col3:
        if st.button("🏢 세 집단 이상 (ANOVA)\n\n3개 이상 집단 간 평균 차이와\n사후검정을 수행합니다.\n(ANOVA TEST)"):
            go_analysis("anova")
        if st.button("📉 영향 요인 (Regression)\n\n독립변수가 종속변수에 미치는\n영향력을 분석합니다.\n(REG TEST)"):
            go_analysis("reg")

    st.markdown("---")
    st.subheader("📂 데이터 업로드 시뮬레이션")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요 (한글 포함 시 EUC-KR 또는 UTF-8)", type="csv")

# [ANALYSIS 페이지] 실제 분석 실행
elif st.session_state.page == 'analysis':
    st.button("← 메인으로 돌아가기", on_click=go_home)
    
    # 1. 데이터 로드 및 처리
    df = None
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='euc-kr') # 한글 우선 시도
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8')
    else:
        st.info("👋 테스트를 위해 CSV 파일을 업로드해주세요. (현재는 샘플 모드가 아닙니다)")

    # 2. 분석 제목 및 변수 선택 UI
    titles = {
        "freq": "빈도분석 (Frequency Analysis)",
        "desc": "기술통계 (Descriptive Statistics)",
        "ttest": "t-test (Mean Difference)",
        "anova": "One-way ANOVA",
        "corr": "Correlation Analysis",
        "reg": "Linear Regression",
        "chi": "Chi-square Test"
    }
    st.header(titles[st.session_state.method])

    if df is not None:
        st.markdown("### 1. 변수 선택 (Variables)")
        vars = df.columns.tolist()
        params = {}
        
        # UI: 변수 선택창 (2단 분리)
        c1, c2 = st.columns([1, 2])
        
        with c1:
            method = st.session_state.method
            
            if method == "freq":
                st.info("💡 범주형 변수(성별, 직급 등)를 선택하세요.")
                params['var'] = st.selectbox("변수 선택", vars)
                
            elif method == "desc":
                st.info("💡 연속형 변수(점수, 나이 등)를 선택하세요.")
                params['vars'] = st.multiselect("변수 선택 (다중 가능)", vars)
                
            elif method == "ttest":
                ttest_type = st.radio("분석 유형", ["독립표본 (Independent)", "대응표본 (Paired)", "일표본 (One-sample)"])
                params['type'] = ttest_type
                if "독립" in ttest_type:
                    params['group'] = st.selectbox("그룹 변수 (명목형)", vars)
                    params['target'] = st.selectbox("종속 변수 (연속형)", vars)
                elif "대응" in ttest_type:
                    params['pre'] = st.selectbox("사전 변수 (Pre)", vars)
                    params['post'] = st.selectbox("사후 변수 (Post)", vars)
                else:
                    params['target'] = st.selectbox("검정 변수", vars)
                    params['mu'] = st.number_input("검정값 (기준값)", value=0.0)

            elif method == "anova":
                st.info("💡 3개 이상의 그룹이 있는 변수를 선택하세요.")
                params['group'] = st.selectbox("그룹 변수", vars)
                params['target'] = st.selectbox("종속 변수 (연속형)", vars)
                
            elif method == "corr":
                st.info("💡 2개 이상의 연속형 변수를 선택하세요.")
                params['vars'] = st.multiselect("변수 선택", vars)
                
            elif method == "reg":
                params['dep'] = st.selectbox("종속 변수 (Dependent)", vars)
                indep_vars = [v for v in vars if v != params['dep']]
                params['indep'] = st.multiselect("독립 변수 (Independent)", indep_vars)
                
            elif method == "chi":
                st.info("💡 두 개의 범주형 변수를 선택하세요.")
                params['row'] = st.selectbox("행 변수", vars)
                params['col'] = st.selectbox("열 변수", vars)

        # 분석 실행 버튼
        run = st.button("분석 실행 (Run Analysis)", type="primary")

        # 3. 분석 결과 출력
        if run:
            st.divider()
            t1, t2, t3, t4 = st.tabs(["📊 데이터 확인", "🔍 가정 검정 (Assumptions)", "🧮 통계 결과 (Results)", "📝 논문식 해석 (Interpretation)"])
            
            with t1:
                st.dataframe(df.head())
            
            # --- 통계 로직 시작 ---
            try:
                # 1. 빈도분석
                if method == "freq":
                    tbl = df[params['var']].value_counts().sort_index()
                    prop = df[params['var']].value_counts(normalize=True).sort_index() * 100
                    res_df = pd.DataFrame({'Frequency': tbl, 'Percent(%)': prop.round(1)})
                    
                    with t2: st.write("빈도분석은 별도의 가정 검정이 필요하지 않습니다.")
                    with t3: st.dataframe(res_df)
                    with t4: 
                        max_cat = tbl.idxmax()
                        max_pct = prop.max()
                        st.write(f"분석 결과 '{params['var']}' 변수에서 '{max_cat}' 항목이 {max_pct:.1f}%로 가장 높은 빈도를 보였습니다.")

                # 2. 기술통계
                elif method == "desc":
                    if not params['vars']: st.error("변수를 선택해주세요.")
                    else:
                        d = df[params['vars']]
                        stats_df = d.describe().T
                        stats_df['Skewness'] = d.skew()
                        stats_df['Kurtosis'] = d.kurtosis()
                        
                        with t2: 
                            st.write("#### 정규성 탐색 (Normality Check)")
                            st.write("왜도(Skewness) < |3|, 첨도(Kurtosis) < |10| (또는 7) 일 때 정규성을 가정합니다.")
                        with t3: st.dataframe(stats_df)
                        with t4: st.write("제시된 평균(M)과 표준편차(SD)를 논문에 기술하십시오.")

                # 3. T-test
                elif method == "ttest":
                    if "독립" in params['type']:
                        grps = df[params['group']].unique()
                        if len(grps) != 2: st.error("그룹 변수는 정확히 2개의 집단이어야 합니다.")
                        else:
                            g1 = df[df[params['group']]==grps[0]][params['target']].dropna()
                            g2 = df[df[params['group']]==grps[1]][params['target']].dropna()
                            
                            levene = stats.levene(g1, g2)
                            t_res = stats.ttest_ind(g1, g2, equal_var=(levene.pvalue > 0.05))
                            
                            with t2:
                                st.write(f"**등분산성(Levene)**: F={levene.statistic:.3f}, p={levene.pvalue:.3f}")
                                if levene.pvalue > 0.05: st.success("등분산 가정이 충족되었습니다.")
                                else: st.warning("등분산 가정이 위배되어 Welch's t-test를 수행했습니다.")
                            with t3:
                                st.write(f"**Group Statistics**: {grps[0]}(M={g1.mean():.2f}), {grps[1]}(M={g2.mean():.2f})")
                                st.metric("t-value", f"{t_res.statistic:.3f}")
                                st.metric("p-value", f"{t_res.pvalue:.3f}")
                            with t4:
                                sig = "유의한 차이가 있습니다" if t_res.pvalue < 0.05 else "유의한 차이가 없습니다"
                                st.write(f"분석 결과 t={t_res.statistic:.3f}, p={t_res.pvalue:.3f}로 두 집단 간에는 통계적으로 {sig}.")
                    
                    elif "대응" in params['type']:
                        diff = df[params['post']] - df[params['pre']]
                        shapiro = stats.shapiro(diff.dropna())
                        t_res = stats.ttest_rel(df[params['pre']], df[params['post']], nan_policy='omit')
                        
                        with t2: st.write(f"차이값 정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        with t3: st.write(f"t={t_res.statistic:.3f}, p={t_res.pvalue:.3f}")
                        with t4: st.write(f"검정 결과 p={t_res.pvalue:.3f}입니다.")

                    else: # One-sample
                        d = df[params['target']].dropna()
                        t_res = stats.ttest_1samp(d, params['mu'])
                        with t2: st.write(f"정규성(Shapiro): p={stats.shapiro(d).pvalue:.3f}")
                        with t3: st.write(f"t={t_res.statistic:.3f}, p={t_res.pvalue:.3f}")
                        with t4: st.write(f"검정 결과 p={t_res.pvalue:.3f}입니다.")

                # 4. ANOVA
                elif method == "anova":
                    model = ols(f"{params['target']} ~ C({params['group']})", data=df).fit()
                    
                    # 가정 검정
                    resid = model.resid
                    shapiro = stats.shapiro(resid)
                    # Levene (그룹별 분리)
                    grps = [df[df[params['group']]==g][params['target']].dropna() for g in df[params['group']].unique()]
                    levene = stats.levene(*grps)
                    
                    with t2:
                        st.write(f"1. 잔차 정규성(Shapiro): p={shapiro.pvalue:.3f}")
                        st.write(f"2. 등분산성(Levene): p={levene.pvalue:.3f}")
                    
                    with t3:
                        anova_tbl = sm.stats.anova_lm(model, typ=2)
                        st.dataframe(anova_tbl)
                        if anova_tbl['PR(>F)'][0] < 0.05:
                            st.write("👉 **사후검정 (Tukey HSD)**")
                            tukey = pairwise_tukeyhsd(df[params['target']].dropna(), df[params['group']].dropna())
                            st.text(tukey.summary())
                    
                    with t4:
                        p_val = sm.stats.anova_lm(model, typ=2)['PR(>F)'][0]
                        res_text = "유의한 차이가 있습니다." if p_val < 0.05 else "차이가 없습니다."
                        st.write(f"F검정 결과 p={p_val:.3f}로 집단 간 {res_text}")

                # 5. Correlation
                elif method == "corr":
                    if len(params['vars']) < 2: st.error("2개 이상의 변수를 선택하세요.")
                    else:
                        corr_mat = df[params['vars']].corr()
                        with t2: st.write("피어슨 상관분석은 변수들의 정규성을 가정합니다.")
                        with t3: 
                            st.write("#### 상관계수 행렬 (Pearson r)")
                            st.dataframe(corr_mat.style.background_gradient(cmap='coolwarm'))
                        with t4: st.write("상관계수(r)가 .4 이상이면 관련성이 높다고 해석합니다.")

                # 6. Regression
                elif method == "reg":
                    if not params['indep']: st.error("독립변수를 선택하세요.")
                    else:
                        form = f"{params['dep']} ~ {' + '.join(params['indep'])}"
                        model = ols(form, data=df).fit()
                        
                        with t2:
                            st.write(f"**독립성(Durbin-Watson)**: {durbin_watson(model.resid):.2f} (2에 가까울수록 좋음)")
                            if len(params['indep']) > 1:
                                from statsmodels.stats.outliers_influence import variance_inflation_factor
                                X = sm.add_constant(df[params['indep']].dropna())
                                vif = pd.DataFrame([variance_inflation_factor(X.values, i) for i in range(X.shape[1])], index=X.columns, columns=["VIF"])
                                st.write("**다중공선성(VIF)**: 10 미만이어야 함")
                                st.dataframe(vif[1:]) # 상수항 제외
                        with t3:
                            st.text(model.summary())
                        with t4:
                            st.write(f"회귀모형 설명력(Adj R2)은 {model.rsquared_adj:.3f}입니다. P>|t|가 0.05 미만인 변수가 유의한 영향을 미칩니다.")

                # 7. Chi-square
                elif method == "chi":
                    ct = pd.crosstab(df[params['row']], df[params['col']])
                    chi2, p, dof, ex = stats.chi2_contingency(ct)
                    
                    with t2: st.write("기대빈도 5 미만 셀이 20%를 넘지 않는지 확인해야 합니다.")
                    with t3:
                        st.write("#### 교차표 (Observed)")
                        st.dataframe(ct)
                        st.metric("Chi-square", f"{chi2:.3f}")
                        st.metric("p-value", f"{p:.3f}")
                    with t4:
                        res = "유의한 연관성이 있습니다." if p < 0.05 else "독립적입니다 (연관성 없음)."
                        st.write(f"검정 결과 p={p:.3f}로 두 변수는 {res}")

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
                st.info("데이터에 결측치(NA)가 있거나 변수 타입(문자/숫자)이 맞지 않을 수 있습니다.")
