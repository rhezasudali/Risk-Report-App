import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Risk Score Report", page_icon="📊", layout="wide")

@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

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
        <circle cx="{w-10}" cy="{last_y}" r="5" fill="#ff4d4f"/>
        <text x="{w-150}" y="{last_y - 15 if last_y > 40 else last_y + 15}" fill="#8b909f" font-family="JetBrains Mono" font-size="11">Current: {last_p:,.0f}</text>
    </svg>
    """

st.markdown("<h2 style='text-align:center; color:#e0e0e0; font-family:sans-serif;'>⚡ Advanced Institutional Risk Report</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    raw_ticker = st.text_input("Masukkan Kode Saham:", value="BRPT")
    ticker = raw_ticker.strip().upper() + ".JK"

if raw_ticker:
    with st.spinner(f"Menganalisa {ticker}..."):
        info, hist = get_stock_data(ticker)
        
        if hist.empty:
            st.error("Data saham tidak ditemukan dari Yahoo Finance.")
        else:
            # --- PERHITUNGAN DATA ---
            price = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else price
            pct_change = ((price - prev) / prev) * 100
            
            name = info.get('longName') or info.get('shortName') or raw_ticker.upper()
            sector = info.get('sector', 'N/A').upper()
            mcap = info.get('marketCap', 0) / 1e12 
            vol = info.get('averageVolume', 0) / 1e6 
            pe = info.get('trailingPE', 0) or 0
            pb = info.get('priceToBook', 0) or 0
            cr = info.get('currentRatio', 0) or 0
            de = info.get('debtToEquity', 0) or 0
            ev_rev = info.get('enterpriseToRevenue', 0) or 0
            rev_g = (info.get('revenueGrowth', 0) or 0) * 100
            npat_g = (info.get('earningsQuarterlyGrowth', 0) or 0) * 100
            low52 = info.get('fiftyTwoWeekLow', 0)
            high52 = info.get('fiftyTwoWeekHigh', 0)
            
            # --- SKOR RISIKO ---
            v_score = 35 if 0 < pe < 15 else 20 if 0 < pe < 25 else 10
            h_score = 35 if de < 100 else 18 if de < 200 else 10
            g_score = 30 if rev_g > 10 else 15 if rev_g > 0 else 5
            total = v_score + h_score + g_score
            
            # --- LOGIKA NARASI OTOMATIS (AI RULES) ---
            # Menghasilkan list Katalis
            catalysts = []
            if pe > 0 and pe < 15: catalysts.append(f"Valuasi sangat menarik (Undervalued) dengan P/E di level {pe:.1f}x.")
            if rev_g > 5: catalysts.append(f"Momentum pertumbuhan solid dengan lonjakan *Revenue* sebesar {rev_g:.1f}% YoY.")
            if cr > 1.5: catalysts.append("Likuiditas sangat aman (*Current Ratio* > 1.5x), kas kuat untuk operasional.")
            if pct_change > 2: catalysts.append("Momentum harga sedang *bullish* dengan minat beli tinggi hari ini.")
            if not catalysts: catalysts.append("Belum terlihat katalis fundamental yang dominan saat ini.")
            cat_html = "".join([f"<li>{c}</li>" for c in catalysts])

            # Menghasilkan list Risiko
            risks = []
            if de > 100: risks.append(f"Tingkat utang membengkak (D/E: {de/100:.1f}x) membebani margin laba perusahaan.")
            if pe > 30: risks.append(f"Valuasi tergolong mahal (P/E: {pe:.1f}x), sangat rentan terhadap aksi *profit taking*.")
            if npat_g < 0: risks.append(f"Penurunan Laba Bersih (NPAT turun {npat_g:.1f}%) menandakan inefisiensi biaya.")
            if pct_change < -2: risks.append("Tekanan jual jangka pendek sedang berlangsung, harga turun menembus *support*.")
            if not risks: risks.append("Risiko fundamental tergolong relatif rendah dan terkendali.")
            risk_html = "".join([f"<li>{r}</li>" for r in risks])

            # Narasi Operasional
            trend_text = "mencatatkan kinerja yang solid" if total > 60 else "sedang menghadapi tantangan berat"
            margin_text = "didukung oleh efisiensi yang terjaga" if npat_g > 0 else "tertekan oleh lonjakan beban biaya operasi"
            op_update = f"{name} ({raw_ticker.upper()}) {trend_text} pada periode ini. Dengan skor keseluruhan {total}/100, perusahaan berupaya menavigasi volatilitas pasar. Pertumbuhan pendapatan tercatat di angka {rev_g:+.1f}%, yang mana pencapaian laba {margin_text}. Manajemen harus waspada terhadap rasio utang yang berada di level {de/100:.2f}x ekuitas."

            # Verdict
            verdict = "Strong Buy" if total > 80 else "Buy" if total > 65 else "Hold" if total > 40 else "Sell" if total > 20 else "Strong Sell"
            
            v_color = "var(--green)" if total > 65 else "var(--amber)" if total > 40 else "var(--red)"
            p_color = "text-green" if pct_change >= 0 else "text-red"

            # --- FULL HTML TEMPLATE (SAMA PERSIS DENGAN DESAIN ANDA) ---
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
                    button {{ background-color: var(--panel); color: var(--text-main); border: 1px solid var(--border); padding: 10px 16px; border-radius: 6px; cursor: pointer; font-weight: 500; }}
                    button:hover {{ background-color: #1a1d27; border-color: #333845; }}
                    #report-container {{ display: flex; flex-direction: column; gap: 40px; width: 100%; max-width: 850px; }}
                    .page {{ background-color: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                    .header-strip {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }}
                    .stock-title h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 8px; letter-spacing: -0.5px; }}
                    .stock-title .price {{ font-size: 24px; font-weight: 500; }}
                    .date-stamp {{ text-align: right; font-size: 13px; }}
                    .gauge-header {{ display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-bottom: 10px; letter-spacing: 1px; }}
                    .gauge-track {{ height: 12px; background-color: #1a1c23; border-radius: 6px; overflow: hidden; margin-bottom: 30px; }}
                    .gauge-fill {{ height: 100%; width: {total}%; background: linear-gradient(90deg, var(--green), var(--amber) 70%, var(--red)); }}
                    .kpi-strip {{ display: flex; gap: 15px; margin-bottom: 30px; }}
                    .kpi-box {{ flex: 1; background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 15px; text-align: center; }}
                    .kpi-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
                    .kpi-value {{ font-size: 18px; font-weight: 700; }}
                    .chart-container {{ width: 100%; height: 220px; background: #0b0c11; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 30px; padding: 20px; position: relative; }}
                    .chart-title {{ position: absolute; top: 15px; left: 20px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); }}
                    .section-title {{ font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 15px; color: var(--text-muted); border-left: 3px solid var(--amber); padding-left: 10px; }}
                    .grid-6 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
                    .card {{ background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 15px; }}
                    .card-header {{ font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }}
                    .card-value {{ font-size: 20px; font-weight: 700; margin-bottom: 4px; }}
                    .card-sub {{ font-size: 11px; color: #5d6375; text-transform: uppercase; }}
                    .breakdown-row {{ display: flex; align-items: center; margin-bottom: 12px; font-size: 13px; }}
                    .b-label {{ width: 180px; }} .b-track {{ flex: 1; height: 8px; background: #1a1c23; border-radius: 4px; margin: 0 15px; }}
                    .b-fill {{ height: 100%; border-radius: 4px; }} .b-value {{ width: 30px; text-align: right; font-weight: 700; }}
                    
                    /* Page 2 Styles */
                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 13px; }}
                    th, td {{ text-align: left; padding: 12px 15px; border-bottom: 1px solid var(--border); }}
                    th {{ color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; background: #151821; }}
                    .update-box {{ background: rgba(255, 197, 61, 0.05); border: 1px solid var(--border); border-left: 4px solid var(--amber); padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                    .update-box h4 {{ margin-bottom: 10px; font-size: 15px; }}
                    .update-box p {{ font-size: 14px; color: #a0a5b5; line-height: 1.6; }}
                    .dual-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
                    .col-box {{ background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 20px; }}
                    .col-box h4 {{ margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }}
                    .col-box ul {{ list-style: none; font-size: 13px; color: #a0a5b5; }}
                    .col-box ul li {{ margin-bottom: 10px; padding-left: 15px; position: relative; }}
                    .col-box ul li::before {{ content: "•"; position: absolute; left: 0; color: var(--text-main); }}
                    .bottom-line {{ background: #151821; border: 1px solid var(--border); border-radius: 8px; padding: 25px; text-align: center; }}
                    .rating-bar {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; }}
                    .rating-segment {{ padding: 8px 20px; border-radius: 4px; font-size: 12px; font-weight: 700; text-transform: uppercase; background: #1a1c23; color: #5d6375; border: 1px solid var(--border); }}
                    .rating-segment.active {{ background: rgba(255, 197, 61, 0.1); color: {v_color}; border-color: {v_color}; box-shadow: 0 0 10px rgba(255, 197, 61, 0.2); }}
                    .verdict-text {{ font-size: 14px; color: #a0a5b5; max-width: 650px; margin: 0 auto; line-height: 1.6; }}
                </style>
            </head>
            <body>
                <div class="controls"><button id="copyBtn" onclick="copyReport()">📋 Copy Report to Clipboard</button></div>
                <div id="report-container">
                    
                    <div class="page" id="page-1">
                        <div class="header-strip">
                            <div class="stock-title">
                                <h1>{raw_ticker.upper()} <span class="text-muted font-mono" style="font-size: 18px; font-weight: 400;">| {name}</span></h1>
                                <div class="price font-mono">{price:,.0f} IDR <span class="{p_color}" style="font-size: 16px; margin-left: 10px;">{'+' if pct_change>0 else ''}{pct_change:.2f}%</span></div>
                            </div>
                            <div class="date-stamp text-muted font-mono">
                                <div>REPORT DATE: {datetime.now().strftime('%b %d, %Y').upper()}</div>
                                <div>SECTOR: {sector}</div>
                            </div>
                        </div>

                        <div class="risk-gauge">
                            <div class="gauge-header font-mono">
                                <span>RISK METRIC</span>
                                <span style="color: {v_color}">{total} / 100 ({'SAFE ZONE' if total>65 else 'CAUTION' if total>40 else 'ELEVATED RISK'})</span>
                            </div>
                            <div class="gauge-track"><div class="gauge-fill"></div></div>
                        </div>

                        <div class="kpi-strip">
                            <div class="kpi-box"><div class="kpi-label">Market Cap</div><div class="kpi-value font-mono">{mcap:.1f}T</div></div>
                            <div class="kpi-box"><div class="kpi-label">52W Range</div><div class="kpi-value font-mono">{low52:,.0f} - {high52:,.0f}</div></div>
                            <div class="kpi-box"><div class="kpi-label">Vol (Avg 3M)</div><div class="kpi-value font-mono">{vol:.1f}M</div></div>
                            <div class="kpi-box"><div class="kpi-label">P/B Ratio</div><div class="kpi-value font-mono">{pb:.2f}x</div></div>
                        </div>

                        <div class="chart-container">
                            <div class="chart-title font-mono">12-Month Price Action (IDR)</div>
                            {make_svg_chart(hist)}
                        </div>

                        <h2 class="section-title">Fundamental Health Grid</h2>
                        <div class="grid-6">
                            <div class="card"><div class="card-header font-mono">P/E Ratio</div><div class="card-value font-mono {'text-amber' if pe>20 else 'text-green'}">{pe:.1f}x</div><div class="card-sub">Valuation</div></div>
                            <div class="card"><div class="card-header font-mono">EV/Revenue</div><div class="card-value font-mono">{ev_rev:.2f}x</div><div class="card-sub">Valuation</div></div>
                            <div class="card"><div class="card-header font-mono">Current Ratio</div><div class="card-value font-mono {'text-amber' if cr<1 else 'text-green'}">{cr:.2f}</div><div class="card-sub">Health</div></div>
                            <div class="card"><div class="card-header font-mono">Debt/Equity</div><div class="card-value font-mono {'text-red' if de>100 else 'text-amber'}">{de/100:.2f}x</div><div class="card-sub">Health</div></div>
                            <div class="card"><div class="card-header font-mono">Revenue YoY</div><div class="card-value font-mono {'text-green' if rev_g>0 else 'text-red'}">{rev_g:+.1f}%</div><div class="card-sub">Growth</div></div>
                            <div class="card"><div class="card-header font-mono">NPAT YoY</div><div class="card-value font-mono {'text-green' if npat_g>0 else 'text-red'}">{npat_g:+.1f}%</div><div class="card-sub">Growth</div></div>
                        </div>

                        <h2 class="section-title">Composite Score Breakdown</h2>
                        <div class="scores">
                            <div class="breakdown-row"><div class="b-label font-mono">Valuation (35)</div><div class="b-track"><div class="b-fill {'bg-green' if v_score>25 else 'bg-amber' if v_score>15 else 'bg-red'}" style="width: {(v_score/35)*100}%;"></div></div><div class="b-value font-mono">{v_score}</div></div>
                            <div class="breakdown-row"><div class="b-label font-mono">Financial Health (35)</div><div class="b-track"><div class="b-fill {'bg-green' if h_score>25 else 'bg-amber' if h_score>15 else 'bg-red'}" style="width: {(h_score/35)*100}%;"></div></div><div class="b-value font-mono">{h_score}</div></div>
                            <div class="breakdown-row"><div class="b-label font-mono">Growth (30)</div><div class="b-track"><div class="b-fill {'bg-green' if g_score>20 else 'bg-amber' if g_score>10 else 'bg-red'}" style="width: {(g_score/30)*100}%;"></div></div><div class="b-value font-mono">{g_score}</div></div>
                            <div class="breakdown-row" style="margin-top: 15px; border-top: 1px solid var(--border); padding-top: 15px;">
                                <div class="b-label font-mono text-amber" style="font-weight: 700; color: {v_color}">TOTAL SCORE</div>
                                <div style="flex: 1;"></div>
                                <div class="b-value font-mono text-amber" style="width: auto; color: {v_color}">{total} / 100</div>
                            </div>
                        </div>
                    </div>

                    <div class="page" id="page-2">
                        <h2 class="section-title">Fundamental Data Estimates</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th class="font-mono">Metric</th>
                                    <th class="font-mono">Value / Ratio</th>
                                    <th class="font-mono">Status</th>
                                </tr>
                            </thead>
                            <tbody class="font-mono">
                                <tr><td>Market Capitalization</td><td>{mcap:.2f} Trillion IDR</td><td class="text-green">Active</td></tr>
                                <tr><td>Price to Earning (P/E)</td><td>{pe:.2f}x</td><td class="{'text-amber' if pe>20 else 'text-green'}">{"Premium" if pe>20 else "Discount"}</td></tr>
                                <tr><td>Price to Book (P/B)</td><td>{pb:.2f}x</td><td class="{'text-amber' if pb>2 else 'text-green'}">{"Premium" if pb>2 else "Discount"}</td></tr>
                                <tr><td>Trailing Revenue Growth</td><td class="{'text-green' if rev_g>0 else 'text-red'}">{rev_g:+.2f}% YoY</td><td>Recorded</td></tr>
                            </tbody>
                        </table>

                        <h2 class="section-title">Latest Operational Insight</h2>
                        <div class="update-box">
                            <h4>Algorithmic Fundamental Summary</h4>
                            <p>{op_update}</p>
                        </div>

                        <div class="dual-col">
                            <div class="col-box">
                                <h4 class="text-green"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg> Catalysts & Strengths</h4>
                                <ul>{cat_html}</ul>
                            </div>
                            <div class="col-box">
                                <h4 class="text-red"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"/></svg> Risk Exposures</h4>
                                <ul>{risk_html}</ul>
                            </div>
                        </div>

                        <div class="bottom-line">
                            <h2 class="section-title" style="border: none; text-align: center; margin-bottom: 0;">Bottom Line Verdict</h2>
                            <div class="rating-bar font-mono">
                                <div class="rating-segment {'active' if verdict=='Strong Sell' else ''}">Strong Sell</div>
                                <div class="rating-segment {'active' if verdict=='Sell' else ''}">Sell</div>
                                <div class="rating-segment {'active' if verdict=='Hold' else ''}">Hold</div>
                                <div class="rating-segment {'active' if verdict=='Buy' else ''}">Buy</div>
                                <div class="rating-segment {'active' if verdict=='Strong Buy' else ''}">Strong Buy</div>
                            </div>
                            <p class="verdict-text">
                                Berdasarkan evaluasi kuantitatif, saham {name} mencetak skor <strong>{total}/100</strong>. Sistem merekomendasikan status <strong>{verdict.upper()}</strong> di level harga {price:,.0f} IDR dengan mempertimbangkan komposit rasio keuangan dan aksi harga terakhir.
                            </p>
                        </div>
                    </div>

                </div>
                <script>
                    function copyReport() {{
                        const container = document.getElementById('report-container');
                        const range = document.createRange(); range.selectNode(container); window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
                        try {{ document.execCommand('copy'); const btn = document.getElementById('copyBtn'); btn.innerText = '✅ Copied!'; setTimeout(() => btn.innerText = '📋 Copy Report to Clipboard', 2000); }} catch(e) {{}}
                        window.getSelection().removeAllRanges();
                    }}
                </script>
            </body>
            </html>
            """
            components.html(html_code, height=2200, scrolling=True)
