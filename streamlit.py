import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# ETF 설명 데이터
assets = {
    'SPLG': 'SPLG는 S&P 500 지수를 추적하는 ETF입니다.',
    'QQQM': 'QQQM은 NASDAQ-100 지수를 추적하는 ETF입니다.',
    'EFA': 'EFA는 북미 외의 선진국 대형주를 추적하는 ETF입니다.',
    'SHY': 'SHY는 단기 미국 국채를 추적하는 ETF입니다.',
    'IEF': 'IEF는 중기 미국 국채를 추적하는 ETF입니다.',
    'TLT': 'TLT는 장기 미국 국채를 추적하는 ETF입니다.',
    'TIP': 'TIP는 미국 물가 연동 채권(TIPS)을 추적하는 ETF입니다.',
    'LQD': 'LQD는 투자적격 등급의 회사채를 추적하는 ETF입니다.',
    'HYG': 'HYG는 고수익(정크) 회사채를 추적하는 ETF입니다.',
    'RWX': 'RWX는 국제 부동산 투자 신탁(REITs)을 추적하는 ETF입니다.',
    'EMB': 'EMB는 신흥 시장 채권을 추적하는 ETF입니다.'
}

# Streamlit 제목
st.title('ETF 수익률 분석')
st.sidebar.title('설정')

# 데이터 로드
@st.cache_data
def load_data(etf_list):
    data = {}
    for etf in etf_list:
        ticker = yf.Ticker(etf)
        hist = ticker.history(period='2y', interval='1mo')  # 최근 2년 월별 데이터
        data[etf] = hist['Close']
    df = pd.DataFrame(data)
    df.index.name = 'Date'
    return df

etf_list = list(assets.keys())[:3]  # 분석 대상 ETF 제한 (SPLG, QQQM, EFA)
df = load_data(etf_list)

# 투자 전략 설정
strategy = st.sidebar.selectbox('투자 전략 선택', ['1년 수익률', '6개월 수익률'])

# 수익률 계산
if strategy == '1년 수익률':
    returns = df.pct_change(12).iloc[-1]
    st.write("### 최근 1년 수익률")
elif strategy == '6개월 수익률':
    returns = df.pct_change(6).iloc[-1]
    st.write("### 최근 6개월 수익률")

# 수익률 테이블 표시
returns_df = returns.reset_index()
returns_df.columns = ['ETF', '수익률']
st.table(returns_df)

# 투자 결정
if strategy == '1년 수익률':
    recommended_etf = returns.idxmax()
    st.success(f"최근 1년 수익률 기준, 추천 ETF는 **{recommended_etf}** 입니다!")
else:
    top_3_bonds = returns.nlargest(3).index.tolist()
    st.success(f"최근 6개월 수익률 기준, 추천 ETF는 **{', '.join(top_3_bonds)}** 입니다!")

# 그래프 그리기
fig = px.line(df, title=f'ETF 가격 변화 ({strategy})')
st.plotly_chart(fig)

# ETF 설명 표시
st.write("### ETF 설명")
for etf, description in assets.items():
    st.write(f"**{etf}**: {description}")

# 투자 금액 입력 및 계산
st.write("### 투자 계산")
investment = st.number_input('투자 금액 입력 ($):', min_value=0, value=1000, step=100)
if investment > 0:
    unit_prices = df.iloc[-1].to_dict()  # 최신 종가 기준 단가
    shares = {etf: investment // unit_prices[etf] for etf in unit_prices}
    remaining_cash = investment - sum(shares[etf] * unit_prices[etf] for etf in unit_prices)

    st.write("### 투자 결과")
    for etf, num_shares in shares.items():
        st.write(f"{etf}: {num_shares} 주 (가격: ${unit_prices[etf]:.2f})")
    st.write(f"남은 현금: ${remaining_cash:.2f}")
