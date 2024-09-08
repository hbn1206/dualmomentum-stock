import yfinance as yf
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
import pandas as pd
import dash  # Import dash here


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

# 종가(Close) 데이터 추출
close_data = data['Adj Close']

# 수익률 계산 (수익률 = (현재 가격 / 시작 가격) - 1)
returns_1y = close_data / close_data.iloc[0] - 1

# 최근 6개월 데이터 추출
returns_6m = close_data[-126:] / close_data[-126:].iloc[0] - 1  # 6개월 동안의 수익률

# 일봉, 주봉, 월봉 데이터 생성
daily_returns = close_data / close_data.iloc[0] - 1
weekly_returns = close_data.resample('W').last() / close_data.resample('W').last().iloc[0] - 1
monthly_returns = close_data.resample('ME').last() / close_data.resample('ME').last().iloc[0] - 1  # Changed 'M' to 'ME'

# 그래프 생성 함수
def create_return_plot(returns):
    fig = go.Figure()

    # 자산을 원하는 순서로 추가 (SPLG, QQQM, EFA) - 범례 순서 설정
    priority_assets = ['SPLG', 'QQQM', 'EFA']
    available_priority_assets = [asset for asset in priority_assets if asset in returns.columns]
    other_assets = [asset for asset in returns.columns if asset not in available_priority_assets]
    
    # 모든 자산을 포함한 리스트 (범례 순서에 맞추어야 함)
    ordered_assets = available_priority_assets + other_assets

    # SPLG, QQQM, EFA를 가장 위에 추가
    for asset in ordered_assets:
        fig.add_trace(go.Scatter(
            x=returns.index,
            y=returns[asset],
            mode='lines',
            name=asset,
        ))

    # 레이아웃 설정
    fig.update_layout(
        
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        yaxis_tickformat='.2%',
        hovermode='x unified',
        legend_title_text='자산',
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                buttons=[
                    dict(
                        args=[
                            {"x": [daily_returns.index] * len(ordered_assets),
                             "y": [daily_returns[asset] for asset in ordered_assets],
                             "visible": [True] * len(ordered_assets)},  # 자산 순서 유지
                        ],
                        label="일봉",
                        method="update"
                    ),
                    dict(
                        args=[
                            {"x": [weekly_returns.index] * len(ordered_assets),
                             "y": [weekly_returns[asset] for asset in ordered_assets],
                             "visible": [True] * len(ordered_assets)},  # 자산 순서 유지
                        ],
                        label="주봉",
                        method="update"
                    ),
                    dict(
                        args=[
                            {"x": [monthly_returns.index] * len(ordered_assets),
                             "y": [monthly_returns[asset] for asset in ordered_assets],
                             "visible": [True] * len(ordered_assets)},  # 자산 순서 유지
                        ],
                        label="월봉",
                        method="update"
                    )
                ],
                direction="left",
                x=0.5,
                xanchor="center",
                y=1.15,
                yanchor="top"
            ),
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        args=[{"visible": [True] * len(ordered_assets)}],
                        label="모두 보이기",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": ["legendonly"] * len(ordered_assets)}],
                        label="모두 숨기기",
                        method="update"
                    )
                ],
                direction="left",
                x=1,
                xanchor="right",
                y=1.15,
                yanchor="top"
            )
        ]
    )

    return fig



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



# 한 종목 선택시 그래프 생성 함수
def create_return_each(returns, title, selected_asset=None):
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
        fig.add_trace(go.Scatter(
            x=returns.index,
            y=returns['SPLG'],
            mode='lines',
            name='SPLG',
        ))
        
        # MACD, RSI 계산 및 추가
        macd_osc, rsi = calculate_macd_rsi(close_data['SPLG'])
        fig.add_trace(go.Scatter(
            x=macd_osc.index,
            y=macd_osc,
            mode='lines',
            name='SPLG MACD OSC',
            yaxis='y2'
        ))
        fig.add_trace(go.Scatter(
            x=rsi.index,
            y=rsi,
            mode='lines',
            name='SPLG RSI',
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

# 투자 전략에 따른 투자 판단 함수
def investment_decision(investment_amount=None):
    splg_return_1y = returns_1y['SPLG'].iloc[-1]
    if splg_return_1y > 0:
        best_asset = returns_1y[['SPLG', 'QQQM', 'EFA']].iloc[-1].idxmax()
        best_price = close_data[best_asset].iloc[-1]
        number_of_shares = int(investment_amount // best_price) if investment_amount else 0
        total_investment = number_of_shares * best_price
        if investment_amount:
            return (f"SPLG의 최근 1년 수익이 {splg_return_1y:.2%}로 플러스입니다.\n"
                    f"{best_asset}에 총 {int(investment_amount):,}달러를 투자하면\n"
                    f"주가 {best_price:.2f}달러에 {number_of_shares}주를 구매할 수 있으며, \n"
                    f"총 {total_investment:.2f}달러를 투자하게 됩니다.")
        else:
            return (f"SPLG의 최근 1년 수익이 {splg_return_1y:.2%}로 플러스입니다.\n"
                    f"{best_asset}에 투자하세요.")
    else:
        bond_returns = returns_6m[['SHY', 'IEF', 'TLT', 'TIP', 'LQD', 'HYG', 'RWX', 'EMB']].iloc[-1]
        best_bonds = bond_returns.nlargest(3)
        investment_message = f"SPLG의 최근 1년 수익이 {splg_return_1y:.2%}로 마이너스입니다.\n"
        allocation_message = ""
        total_investment = 0
        
        if investment_amount is not None:
            for bond, return_ in best_bonds.items():
                bond_price = close_data[bond].iloc[-1]
                number_of_shares = int((investment_amount / 3) // bond_price) if bond_price else 0
                total_bond_investment = number_of_shares * bond_price
                allocation_message += (f"{bond}에 약 {int(investment_amount / 3):,}달러를 투자하면\n"
                                      f"주가 {bond_price:.2f}달러에 {number_of_shares}주를 구매할 수 있으며, \n"
                                      f"총 {total_bond_investment:.2f}달러를 투자하게 됩니다.\n")
                total_investment += total_bond_investment

            if total_investment < investment_amount:
                allocation_message += (f"나머지 약 {int(investment_amount - total_investment):,}달러는 현금으로 보유합니다.\n")
        
        return investment_message + allocation_message


# Dash 애플리케이션 생성
app = Dash(__name__)

app.layout = html.Div([
    html.H1('변형듀얼모멘텀 투자',id='title', style={'margin': '30px', 'textAlign': 'center'}),
    html.H2(id='investment-decision', style={'margin': '30px', 'textAlign': 'center'}),
    html.Div([ dcc.Input(id='investment-amount', type='number', placeholder="총 투자 금액 (달러)", style={'margin': '20px', "padding":"15px", 'fontSize': '15px'}),
    html.Button('계산하기', id='calculate-button', n_clicks=0, style={'margin': '10px'}),
    html.Button('초기화', id='reset-button', n_clicks=0, style={'margin': '10px'}),],style={
            
        'display': 'flex',
        'flexWrap': 'wrap',
        'width': '100%',
        'overflow': 'auto',
        "justifyContent": "center",
        'alignItems': 'center'
    },),
    
   
    html.Div([
        html.H2("최근 1년 ETF 별 수익률 비교" ,id='return-plot-1y-title', style={'margin': '30px', 'textAlign': 'center'}),
        dcc.Graph(id='return-plot-1y', style={'height': '80vh'}),
        html.H2("최근 6개월 ETF 별 수익률 비교" ,id='return-plot-6m-title', style={'margin': '30px', 'textAlign': 'center'}),
        dcc.Graph(id='return-plot-6m', style={'height': '80vh'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'height': 'auto'}),
    html.H2("매수/매도 타이밍 찾기" ,id='return-each-title', style={'margin': '30px', 'textAlign': 'center'}),
    dcc.Dropdown(
        id='asset-selector',
        options=[{'label': key, 'value': key} for key in assets.keys()],
        multi=False,
        placeholder="자세히 볼 종목을 선택하세요.(with. RSI / MACD)",
       style={'margin': '30px 0 10px 10px',
              'width': '400px'}
    ),
    dcc.Graph(id='return-each', style={'height': '90vh'}),
    html.H2("전략 및 ETF에 대한 간략한 설명" ,id='explain-each-title', style={'margin': '50px', 'textAlign': 'center'}),

    html.Div(
        id='asset-description',
        style={
            'marginTop': '20px',
            'display': 'flex',
            'flexWrap': 'wrap',
            'width': '100%',
            'overflow': 'auto',
            "justifyContent": "center"
        },
        children=[
            html.Div(
                children=[
                    html.P('1. SPLG의 최근 1년 수익 > 0'),
                    html.P('    👉🏼 SPLG와 EFA,qqqm중 최근 1년 수익률이 높은 자산 올인.', style={'marginLeft':'15px'}),
                    html.P("2. SPLG의 최근 1년 수익 < 0 "),html.P('    👉🏼 8개 채권( SHY IEF TLT TIP LQD HYG RWX EMB ) 중 최근 6개월 최고 수익 3개 찾기', style={'marginLeft':'15px'}),html.P('    ** 만약 3개 중 최근 6개월 수익이 0보다 작은 종목은 해당 비중만큼 현금 보유!', style={'marginLeft':'15px'}),html.P('3. 한 달에 한 번 확인 및 리밸런싱'), 
                ],
                style={
                    'width': '700px',
                    'margin': '10px',
                    'border': '1px solid #ccc',
                    'borderRadius': '5px',
                    'padding': '10px'
                }
            )
        ]
   ),    html.Div(
        id='asset-description',
        style={
            'marginTop': '20px',
            'display': 'flex',
            'flexWrap': 'wrap',
            'width': '100%',
            'overflow': 'auto',
            "justifyContent": "center"
        },
        children=[
            html.Div(
                children=[
                    html.H4(asset, style={'margin': '10px'}),
                    html.P(description, style={'margin': '0'})
                ],
                style={
                    'width': '420px',
                    'margin': '10px',
                    'border': '1px solid #ccc',
                    'borderRadius': '5px',
                    'padding': '10px'
                }
            ) for asset, description in assets.items()
        ]
    ),
    html.P(' **투자의 모든 책임은 본인에게 있습니다. 해당 자료는 정확성 및 신뢰도를 보장할 수 없습니다. 참고용으로만 활용하시기 바랍니다.', style={'fontSize':'13px', 'color': 'gray'})
    
])


@app.callback(
    Output('return-each', 'figure'),
    Input('asset-selector', 'value')
)
def update_graph(selected_asset):
    if selected_asset:
        return create_return_each(returns_1y, f'{selected_asset} 1년 수익률과 MACD/RSI', selected_asset=selected_asset)
    else:
        return create_return_each(returns_1y, '종목을 선택해주세요!')


# 콜백: 투자 전략 업데이트
@app.callback(
    Output('investment-decision', 'children'),
    Input('calculate-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('investment-amount', 'value')
)
def update_investment_decision(calculate_clicks, reset_clicks, investment_amount):
    ctx = dash.callback_context

    if not ctx.triggered:
        return investment_decision(None), ""

    triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered == 'reset-button':
        # SPLG의 수익률에 따라 메시지를 업데이트
        return investment_decision(None), ""

    if triggered == 'calculate-button':
        # 투자 결정 함수 호출
        decision_message = investment_decision(investment_amount)
        return decision_message, ""

# 콜백: 1년 수익률 그래프 업데이트
@app.callback(
    Output('return-plot-1y', 'figure'),
    Input('return-plot-1y', 'id')  # Dummy input to trigger callback
)
def update_graph_1y(id_value):
    return create_return_plot(returns_1y)

# 콜백: 6개월 수익률 그래프 업데이트
@app.callback(
    Output('return-plot-6m', 'figure'),
    Input('return-plot-6m', 'id')  # Dummy input to trigger callback
)
def update_graph_6m(id_value):
    return create_return_plot(returns_6m)

# 서버 실행
if __name__ == '__main__':
    app.run_server(debug=True)