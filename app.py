import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Risk Score Report", page_icon="📈", layout="wide")

# Fungsi Penarik Data
@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

# Fungsi Pembuat Grafik Garis (SVG)
def make_svg_chart(hist):
    if len(hist) < 2: return ""
    prices = hist['Close'].values
    min_p, max_p = np.min(prices), np.max(prices)
    w, h, y_offset = 800, 100, 40
    x_step = w / (len(prices) - 1)
    pts = [f"{i * x_step},{y_offset + h - ((p - min_p) / (max_p - min_p + 1e-9)) * h}" for i, p in enumerate(prices)]
    points_str = " ".join(pts)
    
    last_p = prices[-1]
    last_y = y_offset + h - ((last_p - min_p) / (max_p - min_p + 1e-9)) * h
    
    return f"""
    <svg width="100%" height="100%" viewBox="0 0 800 180" preserveAspectRatio="none" style="margin-top: 10px;">
        <line x1="0" y1="40" x2="800" y2="40" stroke="#1e212b" stroke-dasharray="4"/>
        <line x1="0" y1="90" x2="800" y2="90" stroke="#1e212b" stroke-dasharray="4"/>
        <line x1="0" y1="140" x2="800" y2="140" stroke="#1e212b" stroke-dasharray="4"/>
        <defs>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stop-color="#00d084"/><stop offset="50%" stop-color="#ffc53d"/><stop offset="100%" stop-color="#ff4d4f"/>
            </linearGradient>
        </defs>
        <polyline points="{points_str}" fill="none" stroke="url(#lineGrad)" stroke-width="3" stroke-linecap="round"/>
        <circle cx="790" cy="{last_y}" r="5" fill="#ff4d4f"/>
        <text x="650" y="{last_y - 15 if last_y > 40 else last_y + 15}" fill="#8b909f" font-family="JetBrains Mono" font-size="11">Current: {last_p:,.0f}</text>
    </svg>
    """

# Tampilan Streamlit
st.markdown("<h2 style='text-align:center;'>⚡ Auto Risk Report</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    raw_ticker = st.text_input("Masukkan Kode Saham:", value="BRPT")
    ticker = raw_ticker.strip().upper() + ".JK"

if raw_ticker:
    with st.spinner("Menarik data pasar..."):
        info, hist = get_stock_data(ticker)
        
        if hist.empty:
            st.error("Data saham tidak ditemukan.")
        else:
            # Hitung Data
            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2] if len(hist) > 1 else price
            pct_change = ((price - prev) / prev) * 100
            
            mcap = info.get('marketCap', 0) / 1e12 # in Trillions
            vol = info.get('averageVolume', 0) / 1e6 # in Millions
            pe = info.get('trailingPE', 0) or 0
            pb = info.get('priceToBook', 0) or 0
            cr = info.get('currentRatio', 0) or 0
            de = info.get('debtToEquity', 0) or 0
            rev_g = (info.get('revenueGrowth', 0) or 0) * 100
            npat_g = (info.get('earningsQuarterlyGrowth', 0) or 0) * 100
            
            # Skor
            v_score = 35 if pe > 0 and pe < 15 else 20 if pe > 0 and pe < 25 else 10
            h_score = 35 if de < 100 else 18 if de < 200 else 10
            g_score = 30 if rev_g > 10 else 15 if rev_g > 0 else 5
            total = v_score + h_score + g_score
            
            # HTML Injeksi (Desain Asli Anda)
            html_code = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
                <style>
                    :root {{ --bg: #08090d; --panel: #11131a; --border: #1e212b; --green: #00d084; --red: #ff4d4f; --amber: #ffc53d; --text-main: #ffffff; --text-muted: #8b909f; }}
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    body {{ background-color: var(--bg); color: var(--text-main); font-family: 'DM Sans', sans-serif; display: flex; flex-direction: column; align-items: center; gap: 40px; padding: 20px; }}
                    .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
                    .text-green {{ color: var(--green); }} .text-red {{ color: var(--red); }} .text-amber {{ color: var(--amber); }} .text-muted {{ color: var(--text-muted); }}
                    .bg-green {{ background-color: var(--green); }} .bg-red {{ background-color: var(--red); }} .bg-amber {{ background-color: var(--amber); }}
                    .controls {{ width: 100%; max-width: 850px; display: flex; justify-content: flex-end; }}
                    button {{ background-color: var(--panel); color: var(--text-main); border: 1px solid var(--border); padding: 10px 16px; border-radius: 6px; cursor: pointer; }}
                    #report-container {{ display: flex; flex-direction: column; gap: 40px; width: 100%; max-width: 850px; }}
                    .page {{ background-color: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                    .header-strip {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }}
                    .stock-title h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 8px; }}
                    .stock-title .price {{ font-size: 24px; font-weight: 500; }}
                    .date-stamp {{ text-align: right; font-size: 13px; }}
                    .gauge-header {{ display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-bottom: 10px; }}
                    .gauge-track {{ height: 12px; background-color: #1a1c23; border-radius: 6px; overflow: hidden; margin-bottom: 30px; }}
                    .gauge-fill {{ height: 100%; width: {total}%; background: linear-gradient(90deg, var(--green), var(--amber) 70%, var(--red)); }}
                    .kpi-strip {{ display: flex; gap: 15px; margin-bottom: 30px; }}
                    .kpi-box {{ flex: 1; background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 15px; text-align: center; }}
                    .kpi-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }}
                    .kpi-value {{ font-size: 18px; font-weight: 700; }}
                    .chart-container {{ width: 100%; height: 220px; background: #0b0c11; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 30px; padding: 20px; position: relative; }}
                    .chart-title {{ position: absolute; top: 15px; left: 20px; font-size: 12px; color: var(--text-muted); }}
                    .section-title {{ font-size: 14px; font-weight: 700; text-transform: uppercase; margin-bottom: 15px; color: var(--text-muted); border-left: 3px solid var(--amber); padding-left: 10px; }}
                    .grid-6 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
                    .card {{ background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 15px; }}
                    .card-header {{ font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }}
                    .card-value {{ font-size: 20px; font-weight: 700; margin-bottom: 4px; }}
                    .breakdown-row {{ display: flex; align-items: center; margin-bottom: 12px; font-size: 13px; }}
                    .b-label {{ width: 180px; }} .b-track {{ flex: 1; height: 8px; background: #1a1c23; border-radius: 4px; margin: 0 15px; }}
                    .b-fill {{ height: 100%; border-radius: 4px; }} .b-value {{ width: 30px; text-align: right; font-weight: 700; }}
                </style>
            </head>
            <body>
                <div id="report-container">
                    <div class="page">
                        <div class="header-strip">
                            <div class="stock-title">
                                <h1>{raw_ticker} <span class="text-muted font-mono" style="font-size: 18px;">| {info.get('shortName', '-')}</span></h1>
                                <div class="price font-mono">{price:,.0f} IDR <span class="{'text-green' if pct_change>0 else 'text-red'}" style="font-size: 16px;">{'+' if pct_change>0 else ''}{pct_change:.2f}%</span></div>
                            </div>
                            <div class="date-stamp text-muted font-mono"><div>DATE: {datetime.now().strftime('%d %b %Y')}</div></div>
                        </div>

                        <div class="gauge-header font-mono"><span>RISK METRIC</span><span class="text-amber">{total} / 100 SCORE</span></div>
                        <div class="gauge-track"><div class="gauge-fill"></div></div>

                        <div class="kpi-strip">
                            <div class="kpi-box"><div class="kpi-label">Market Cap</div><div class="kpi-value font-mono">{mcap:.1f}T</div></div>
                            <div class="kpi-box"><div class="kpi-label">P/B Ratio</div><div class="kpi-value font-mono">{pb:.2f}x</div></div>
                            <div class="kpi-box"><div class="kpi-label">Vol (3M)</div><div class="kpi-value font-mono">{vol:.1f}M</div></div>
                            <div class="kpi-box"><div class="kpi-label">P/E Ratio</div><div class="kpi-value font-mono">{pe:.1f}x</div></div>
                        </div>

                        <div class="chart-container"><div class="chart-title font-mono">12-Month Price Action</div>{make_svg_chart(hist)}</div>

                        <h2 class="section-title">Fundamental Health Grid</h2>
                        <div class="grid-6">
                            <div class="card"><div class="card-header font-mono">P/E Ratio</div><div class="card-value font-mono">{pe:.1f}x</div></div>
                            <div class="card"><div class="card-header font-mono">Current Ratio</div><div class="card-value font-mono">{cr:.2f}</div></div>
                            <div class="card"><div class="card-header font-mono">Debt/Equity</div><div class="card-value font-mono">{de/100:.2f}x</div></div>
                            <div class="card"><div class="card-header font-mono">Revenue YoY</div><div class="card-value font-mono">{rev_g:+.1f}%</div></div>
                            <div class="card"><div class="card-header font-mono">NPAT YoY</div><div class="card-value font-mono">{npat_g:+.1f}%</div></div>
                            <div class="card"><div class="card-header font-mono">P/B Ratio</div><div class="card-value font-mono">{pb:.2f}x</div></div>
                        </div>

                        <h2 class="section-title">Composite Score Breakdown</h2>
                        <div class="breakdown-row"><div class="b-label font-mono">Valuation (35)</div><div class="b-track"><div class="b-fill bg-amber" style="width: {(v_score/35)*100}%;"></div></div><div class="b-value font-mono">{v_score}</div></div>
                        <div class="breakdown-row"><div class="b-label font-mono">Health (35)</div><div class="b-track"><div class="b-fill bg-amber" style="width: {(h_score/35)*100}%;"></div></div><div class="b-value font-mono">{h_score}</div></div>
                        <div class="breakdown-row"><div class="b-label font-mono">Growth (30)</div><div class="b-track"><div class="b-fill bg-green" style="width: {(g_score/30)*100}%;"></div></div><div class="b-value font-mono">{g_score}</div></div>
                    </div>
                </div>
            </body>
            </html>
            """
            components.html(html_code, height=1300, scrolling=True)