import yfinance as yf
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output  # Ensure Output and Input are imported

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
def create_return_plot(returns, title):
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
        title=title,
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



# Dash 애플리케이션 생성
app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        dcc.Graph(id='return-plot-1y', style={'height': '80vh'}),
        dcc.Graph(id='return-plot-6m', style={'height': '80vh'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'height': 'auto'}),
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
                    html.H4(asset, style={'margin': '10px'}),
                    html.P(description, style={'margin': '0'})
                ],
                style={
                    'width': '500px',
                    'margin': '10px',
                    'border': '1px solid #ccc',
                    'borderRadius': '5px',
                    'padding': '10px'
                }
            ) for asset, description in assets.items()
        ]
    )
])

@app.callback(
    Output('return-plot-1y', 'figure'),
    Input('return-plot-1y', 'id')  # Dummy input to trigger callback
)
def update_graph_1y(_):
    return create_return_plot(returns_1y, '최근 1년 자산 수익률 비교')

@app.callback(
    Output('return-plot-6m', 'figure'),
    Input('return-plot-6m', 'id')  # Dummy input to trigger callback
)
def update_graph_6m(_):
    return create_return_plot(returns_6m, '최근 6개월 자산 수익률 비교')

if __name__ == '__main__':
    app.run_server(debug=True)
