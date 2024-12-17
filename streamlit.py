import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# MACD 계산 함수
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['ShortEMA'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['LongEMA'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['ShortEMA'] - data['LongEMA']
    data['SignalLine'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data

# 야후 파이낸스에서 데이터 가져오기
@st.cache_data
def fetch_data(ticker, period="1mo", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        data.reset_index(inplace=True)
        data['Date'] = pd.to_datetime(data['Date'])
        return data
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류 발생: {e}")
        return None

# 투자 대상 추천 함수
def recommend_investment(ticker):
    data = fetch_data(ticker)
    if data is None:
        return None, None
    data = calculate_macd(data)
    last_macd = data.iloc[-1]['MACD']
    recommendation = "Buy" if last_macd > 0 else "Sell"
    return recommendation, data

# Streamlit 애플리케이션 시작
st.title("투자 대상 추천 및 MACD 분석")

# 입력 섹션
ticker = st.text_input("분석할 종목 티커를 입력하세요:", value="SPY", max_chars=10).upper()
st.write(f"분석할 티커: **{ticker}**")

# 투자 추천 섹션
st.header("오늘의 투자 추천")
recommendation, macd_data = recommend_investment(ticker)

if macd_data is not None:
    st.write(f"추천 투자 전략: **{recommendation}**")

    # MACD 최근 7일치 값 그래프 표시
    st.header("MACD 최근 7일치 값")
    last_7_days = macd_data.tail(7)

    fig, ax = plt.subplots()
    ax.plot(last_7_days['Date'], last_7_days['MACD'], label="MACD", marker='o')
    ax.plot(last_7_days['Date'], last_7_days['SignalLine'], label="Signal Line", linestyle='--')
    ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
    ax.set_title("MACD 최근 7일치")
    ax.set_xlabel("Date")
    ax.set_ylabel("MACD Value")
    ax.legend()
    plt.xticks(rotation=45)

    st.pyplot(fig)

    # 데이터 테이블 표시
    st.subheader("최근 7일 데이터")
    st.dataframe(last_7_days[['Date', 'Close', 'MACD', 'SignalLine']])
else:
    st.warning("데이터를 가져올 수 없습니다. 티커를 확인해주세요.")
