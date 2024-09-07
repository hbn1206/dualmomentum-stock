import yfinance as yf
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output
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

# 1년치 데이터 다운로드
data = yf.download(list(assets.keys()), period='1y')
close_data = data['Adj Close']

# 수익률 계산
returns_1y = close_data / close_data.iloc[0] - 1
returns_6m = close_data[-126:] / close_data[-126:].iloc[0] - 1

# 일봉, 주봉, 월봉 데이터 생성
daily_returns = close_data / close_data.iloc[0] - 1
weekly_returns = close_data.resample('W').last() / close_data.resample('W').last().iloc[0] - 1
monthly_returns = close_data.resample('ME').last() / close_data.resample('ME').last().iloc[0] - 1

# MACD와 RSI 계산 함수
def calculate_macd_rsi(data, short_window=12, long_window=26, signal_window=9, rsi_window=14):
    # MACD 계산
    short_ema = data.ewm(span=short_window, adjust=False).mean()
    long_ema = data.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    macd_osc = macd - signal

    # RSI 계산
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return macd_osc, rsi

# 그래프 생성 함수
def create_return_plot(returns, title, selected_asset=None):
    fig = go.Figure()

    # 선택된 종목이 없으면 전체 자산 표시
    if selected_asset:
        fig.add_trace(go.Scatter(
            x=returns.index,
            y=returns[selected_asset],
            mode='lines',
            name=selected_asset,
        ))
        
        # MACD, RSI 계산 및 추가
        macd_osc, rsi = calculate_macd_rsi(close_data[selected_asset])
        fig.add_trace(go.Scatter(
            x=macd_osc.index,
            y=macd_osc,
            mode='lines',
            name=f'{selected_asset} MACD OSC',
            yaxis='y2'
        ))
        fig.add_trace(go.Scatter(
            x=rsi.index,
            y=rsi,
            mode='lines',
            name=f'{selected_asset} RSI',
            yaxis='y3'
        ))

        # 보조 Y축 추가 (MACD와 RSI용)
        fig.update_layout(
            yaxis2=dict(
                title='MACD Oscillator',
                overlaying='y',
                side='right',
                showgrid=False,
                position=0.85
            ),
            yaxis3=dict(
                title='RSI',
                overlaying='y',
                side='right',
                showgrid=False,
                position=0.95
            )
        )
    
    else:
        # 전체 자산을 표시하는 기본 차트
        for asset in returns.columns:
            fig.add_trace(go.Scatter(
                x=returns.index,
                y=returns[asset],
                mode='lines',
                name=asset,
            ))

    # 레이아웃 설정
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        yaxis_tickformat='.2%',
        hovermode='x unified',
        legend_title_text='자산',
    )

    return fig

# Dash 애플리케이션 생성
app = Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id='asset-selector',
        options=[{'label': key, 'value': key} for key in assets.keys()],
        multi=False,
        placeholder="자세히 볼 종목을 선택하세요.(with. RSI / MACD)",
       style={'margin': '30px 0 10px 10px',
              'width': '400px'}
    ),
    dcc.Graph(id='return-plot-1y', style={'height': '90vh'}),
])

@app.callback(
    Output('return-plot-1y', 'figure'),
    Input('asset-selector', 'value')
)
def update_graph(selected_asset):
    if selected_asset:
        return create_return_plot(returns_1y, f'{selected_asset} 수익률과 MACD/RSI', selected_asset=selected_asset)
    else:
        return create_return_plot(returns_1y, '최근 1년 자산 수익률 비교')

if __name__ == '__main__':
    app.run_server(debug=True)
