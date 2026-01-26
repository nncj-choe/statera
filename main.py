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
# 1. 페이지 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="STATERA", page_icon="📊", layout="wide")

ACRONYM_FULL = "STATistical Engine for Research & Analysis"

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid")

st.markdown(f"""
<style>
    .main-header {{ color: #0f766e; text-align: center; font-size: 2.8rem; font-weight: 700; margin-bottom: 0px; }}
    .acronym-header {{ text-align: center; color: #1e293b; font-size: 1.1rem; font-style: italic; margin-bottom: 2rem; }}
    .stButton>button {{ width: 100%; border-radius: 8px; background-color: #0f766e; color: white; font-weight: bold; margin-top: 10px; }}
    .step-header {{ color: #0f766e; font-size: 1.5rem; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; border-bottom: 2px solid #f0fdfa; padding-bottom: 5px; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 사이드바 (정보 업데이트 및 메일 기능 강화)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("STATERA 📊")
    st.markdown(f"**{ACRONYM_FULL}**")
    st.markdown("---")
    
    # 🚧 Research Beta Version (요청 문구 반영)
    st.markdown("### 🚧 Research Beta Version")
    st.caption("""
    본 서비스는 연구 데이터 분석의 진입 장벽을 낮추기 위해 개발된 웹 기반 통계 솔루션입니다. 
    현재 분석 알고리즘의 타당도 검증 절차를 진행 중입니다.
    """)
    
    st.markdown("---")
    
    # 📬 Contact & Feedback (요청 문구 및 메일 기능 반영)
    st.markdown("### 📬 Contact & Feedback")
    st.caption("오류 제보 및 기능 제안은 언제나 환영합니다.")
    
    # 실제 메일 앱 실행 버튼
    st.link_button("📧 메일 보내기", "mailto:nncj91@snu.ac.kr")
    
    st.caption("주소 복사가 필요하신가요?")
    st.code("nncj91@snu.ac.kr", language="text")
    
    st.markdown("---")
    st.caption("© 2026 ANDA Lab. Developed by Jeongin Choe.")

# -----------------------------------------------------------------------------
# 3. 유틸리티 함수
# -----------------------------------------------------------------------------
def get_stars(p):
    if p < .001: return "***"
    elif p < .01: return "**"
    elif p < .05: return "*"
    else: return ""

def format_p(p):
    return "<.001" if p < .001 else f"{p:.3f}"

def get_plot_buffer():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    buf.seek(0)
    plt.close()
    return buf

def create_word_report(df, interpretation, plot_buf=None):
    doc = Document()
    doc.add_heading(f'STATERA Analysis Report', 0)
    doc.add_paragraph(f"Engine: {ACRONYM_FULL}")
    
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.rows[0].cells[i].text = str(col)
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row): cells[i].text = str(val)
    if plot_buf:
        doc.add_heading('Visualization', level=1); doc.add_picture(plot_buf, width=Inches(5.5))
    doc.add_heading('AI Interpretation', level=1); doc.add_paragraph(interpretation)
    bio = io.BytesIO(); doc.save(bio); bio.seek(0)
    return bio

# -----------------------------------------------------------------------------
# 4. 메인 워크플로우
# -----------------------------------------------------------------------------
st.markdown('<h1 class="main-header">STATERA</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="acronym-header">{ACRONYM_FULL}</p>', unsafe_allow_html=True)

# STEP 1. 데이터 업로드
st.markdown('<div class="step-header">STEP 1. 연구 데이터 업로드</div>', unsafe_allow_html=True)
c1, c2 = st.columns([2, 1])

with c2:
    st.info("**🔒 데이터 보안 안내**\n분석 즉시 데이터를 삭제하며, 서버에 저장되지 않습니다.")
    st.warning("**📄 데이터 형식 가이드**\n첫 번째 행(Row 1)에는 반드시 변수명이 있어야 합니다.")

with c1:
    up_file = st.file_uploader("엑셀(.xlsx) 또는 CSV 파일을 선택하세요", type=["xlsx", "csv"])

if up_file:
    df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
    st.success(f"✔️ 데이터 로드 완료! (총 {len(df)}건의 사례가 인식되었습니다.)")
    with st.expander("데이터 미리보기 (상위 5개 행)"):
        st.dataframe(df.head(), use_container_width=True)

    # STEP 2. 분석 방법 선택
    st.markdown('<div class="step-header">STEP 2. 분석 방법 선택</div>', unsafe_allow_html=True)
    method = st.selectbox(
        "수행할 분석 기법을 선택하세요",
        ["분석 선택 안 함", "기술통계", "T-test", "ANOVA", "상관분석", "회귀분석"]
    )

    if method != "분석 선택 안 함":
        guide_dict = {
            "기술통계": "데이터의 평균, 표준편차 등을 통해 일반적인 특성을 파악합니다.",
            "T-test": "두 집단(예: 실험군/대조군) 간의 평균치 차이를 검정합니다.",
            "ANOVA": "세 개 이상의 집단 간 평균 차이가 유의한지 분석합니다.",
            "상관분석": "두 연속형 변수가 서로 얼마나 관련되어 있는지 확인합니다.",
            "회귀분석": "독립변수가 종속변수에 미치는 영향의 강도를 예측합니다."
        }
        with st.expander(f"💡 {method} 분석에 대한 상세 설명"):
            st.write(guide_dict[method])
        
        num_cols = df.select_dtypes(include=[np.number]).columns
        final_df, interpretation, plot_img = None, "", None

        if method == "기술통계":
            sel_v = st.multiselect("분석할 변수를 선택하세요", num_cols)
            if st.button("분석 실행") and sel_v:
                final_df = df[sel_v].describe().T[['count', 'mean', 'std', 'min', 'max']].reset_index()
                final_df.columns = ['Variable', 'N', 'Mean', 'SD', 'Min', 'Max']
                interpretation = "선택된 변수들의 기술통계 분석 결과입니다."
                plt.figure(figsize=(10, 5)); sns.boxplot(data=df[sel_v]); plot_img = get_plot_buffer()

        elif method == "T-test":
            t_mode = st.radio("T-test 유형", ["독립표본", "대응표본", "단일표본"], horizontal=True)
            if t_mode == "독립표본":
                g, y = st.selectbox("집단변수 (2그룹)", df.columns), st.selectbox("결과변수", num_cols)
                if st.button("분석 실행"):
                    gps = df[g].unique()
                    g1, g2 = df[df[g]==gps[0]][y].dropna(), df[df[g]==gps[1]][y].dropna()
                    t, p = stats.ttest_ind(g1, g2, equal_var=stats.levene(g1, g2).pvalue > .05)
                    final_df = pd.DataFrame({"Variable": [y], "t": [f"{t:.2f}"], "p": [f"{format_p(p)}{get_stars(p)}"]})
                    interpretation = f"검정 결과 p={format_p(p)}이며, 두 그룹 간 차이는 {'유의함' if p < .05 else '유의하지 않음'}으로 나타났습니다."
                    plt.figure(figsize=(6, 5)); sns.barplot(x=g, y=y, data=df); plot_img = get_plot_buffer()
            # (다른 T-test 유형 생략 없이 로직 보강 가능)

        # STEP 3. 결과 출력
        if final_df is not None:
            st.markdown('<div class="step-header">STEP 3. 분석 결과 및 리포트</div>', unsafe_allow_html=True)
            res_c1, res_c2 = st.columns([1.2, 1])
            with res_c1:
                st.table(final_df)
                st.info(f"📝 **결과 해석:** {interpretation}")
            with res_c2:
                if plot_img: st.image(plot_img)
            
            report = create_word_report(final_df, interpretation, plot_img)
            st.download_button("📄 분석 리포트(Word) 다운로드", data=report, file_name=f"STATERA_{method}_Result.docx")

else:
    st.info("⬆️ 분석을 시작하려면 상단의 업로드 영역에 파일을 올려주세요.")

st.markdown("<div style='text-align: center; color: #888; margin-top: 50px;'>Developed by <strong>ANDA Lab Jeongin Choe</strong></div>", unsafe_allow_html=True)
