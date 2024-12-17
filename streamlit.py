import yfinance as yf
import plotly.graph_objects as go
import streamlit as st
import pandas as pd

# 자산 설명
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

# 데이터 다운로드
@st.cache_data
def download_data():
    data_1y = yf.download(list(assets.keys()), period='1y')['Adj Close']
    data_6m = yf.download(list(assets.keys()), period='6mo')['Adj Close']
    return data_1y, data_6m

data_1y, data_6m = download_data()

# 수익률 계산
returns_1y = data_1y / data_1y.iloc[0] - 1
returns_6m = data_6m / data_6m.iloc[0] - 1

# 그래프 생성 함수
def create_return_plot(returns):
    fig = go.Figure()
    for asset in returns.columns:
        fig.add_trace(go.Scatter(
            x=returns.index,
            y=returns[asset],
            mode='lines',
            name=asset
        ))
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        yaxis_tickformat='.2%',
        hovermode='x unified',
        legend_title_text='자산'
    )
    return fig

# Streamlit 인터페이스
st.title("ETF 수익률 대시보드")

# 1년치 그래프
st.header("최근 1년 수익률")
fig_1y = create_return_plot(returns_1y)
st.plotly_chart(fig_1y)

# 6개월치 그래프
st.header("최근 6개월 수익률")
fig_6m = create_return_plot(returns_6m)
st.plotly_chart(fig_6m)

# 자산 설명
st.header("자산 설명")
for asset, description in assets.items():
    st.markdown(f"**{asset}**: {description}")

# 투자 판단
st.header("투자 전략")
splg_return_1y = returns_1y['SPLG'].iloc[-1]
if splg_return_1y > 0:
    st.success(f"SPLG의 최근 1년 수익률은 양수({splg_return_1y:.2%})입니다. SPLG에 투자하세요!")
else:
    st.warning(f"SPLG의 최근 1년 수익률은 음수({splg_return_1y:.2%})입니다. 다른 투자 대안을 고려하세요.")
