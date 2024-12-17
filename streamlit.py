import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 데이터 로드 및 가공 (예시 데이터 생성)
st.title('ETF 수익률 분석')
st.sidebar.title('설정')

dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='M')
data = {
    'Date': dates,
    'SPLG': np.random.uniform(-0.05, 0.05, len(dates)).cumsum(),
    'QQQM': np.random.uniform(-0.04, 0.04, len(dates)).cumsum(),
    'EFA': np.random.uniform(-0.03, 0.03, len(dates)).cumsum()
}
df = pd.DataFrame(data)
df.set_index('Date', inplace=True)

# 투자 전략 설정
strategy = st.sidebar.selectbox('투자 전략 선택', ['1년 수익률', '6개월 수익률'])

# 선택에 따라 데이터 필터링
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
fig = px.line(df, title=f'ETF 수익률 ({strategy})')
st.plotly_chart(fig)

# 투자 금액 입력 및 계산
st.write("### 투자 계산")
investment = st.number_input('투자 금액 입력 ($):', min_value=0, value=1000, step=100)
if investment > 0:
    unit_prices = {'SPLG': 50, 'QQQM': 150, 'EFA': 70}  # 예시 단가
    shares = {etf: investment // unit_prices[etf] for etf in unit_prices}
    remaining_cash = investment - sum(shares[etf] * unit_prices[etf] for etf in unit_prices)

    st.write("### 투자 결과")
    for etf, num_shares in shares.items():
        st.write(f"{etf}: {num_shares} 주")
    st.write(f"남은 현금: ${remaining_cash:.2f}")
