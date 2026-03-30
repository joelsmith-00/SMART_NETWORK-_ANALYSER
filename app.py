import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objects as go
from monitor import get_network_io, get_top_processes, get_wifi_signal
from ip_tracker import get_active_connections
from analytics import record_usage, get_usage_summary, predict_next_usage, check_alerts
from location_tracker import save_location, get_locations
from report import generate_report

app = dash.Dash(__name__)
app.title = "Smart Network Monitor"

prev_io = get_network_io()

CSS = """
body { margin:0; font-family:'Segoe UI',sans-serif; background:#0a0a1a; color:#fff; }
.header { position:relative; width:100%%; height:140px; overflow:hidden;
  background: linear-gradient(135deg,#0a0a2e,#1a1a3e);
  display:flex; align-items:center; justify-content:center; }
.header::before { content:''; position:absolute; top:0; left:0; width:200%%; height:200%%;
  background-image: linear-gradient(rgba(0,212,255,0.1) 1px, transparent 1px),
                     linear-gradient(90deg, rgba(0,212,255,0.1) 1px, transparent 1px);
  background-size:40px 40px;
  animation: gridScan 3s linear infinite; }
@keyframes gridScan { 0%%{background-position:0 0} 100%%{background-position:40px 40px} }
.header h1 { position:relative; z-index:1; font-size:2em; text-shadow:0 0 20px #00d4ff; }
.card { background:linear-gradient(145deg,#16213e,#1a1a2e); border-radius:16px;
  padding:20px; margin:10px; box-shadow:0 8px 32px rgba(0,0,0,0.3);
  animation: cardFloat 4s ease-in-out infinite; min-width:200px; }
@keyframes cardFloat { 0%%,100%%{transform:translateY(0)} 50%%{transform:translateY(-8px)} }
.card:nth-child(2) { animation-delay:0.5s; }
.card:nth-child(3) { animation-delay:1s; }
.card:nth-child(4) { animation-delay:1.5s; }
.card h3 { margin:0 0 8px; color:#00d4ff; font-size:0.9em; }
.card .value { font-size:1.8em; font-weight:bold; }
.cards-row { display:flex; flex-wrap:wrap; justify-content:center; padding:10px 20px; }
.section { padding:20px 30px; }
.alert-box { background:#ff1744; color:#fff; padding:15px; border-radius:10px;
  margin:5px 0; font-weight:bold; font-size:1.1em; animation: pulse 1s ease-in-out infinite; }
@keyframes pulse { 0%%,100%%{opacity:1} 50%%{opacity:0.7} }
input[type=text] { background:#16213e; border:1px solid #00d4ff; color:#fff;
  padding:10px 16px; border-radius:8px; font-size:1em; outline:none; }
button { background:linear-gradient(135deg,#00d4ff,#0088ff); color:#fff; border:none;
  padding:10px 24px; border-radius:8px; font-size:1em; cursor:pointer; font-weight:bold; }
button:hover { opacity:0.85; }
table { width:100%%; border-collapse:collapse; margin-top:10px; }
th,td { padding:10px; text-align:left; border-bottom:1px solid #16213e; }
th { color:#00d4ff; }
"""

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        <meta charset='utf-8'>
        <title>Smart Network Monitor</title>
        <style>""" + CSS + """</style>
        {%metas%}
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

app.layout = html.Div([
    dcc.Interval(id="interval", interval=2000, n_intervals=0),
    html.Div([html.H1("Smart Network Monitoring System")], className="header"),
    html.Div(id="cards-row", className="cards-row"),
    html.Div(id="alerts-section", className="section"),
    html.Div([
        html.H2("CPU Usage by App"),
        dcc.Graph(id="cpu-graph", config={"displayModeBar": False}),
        html.H2("Running Apps"),
        html.Div(id="apps-table"),
        html.H2("Active Connections"),
        html.Div(id="ip-table"),
    ], className="section"),
    html.Div([
        html.H2("Usage Analytics"),
        html.Div(id="usage-summary"),
        html.Div(id="prediction-text", style={"marginTop":"10px","color":"#00ff88","fontSize":"1.1em"}),
    ], className="section"),
    html.Div([
        html.H2("Location-Based Analysis"),
        html.Div([
            dcc.Input(id="loc-input", type="text", placeholder="Enter location (e.g. Lab, Classroom)"),
            html.Button("Capture Signal", id="loc-btn", n_clicks=0),
        ], style={"display":"flex","gap":"10px","marginBottom":"15px"}),
        html.Div(id="loc-list"),
    ], className="section"),
    html.Div([
        html.H2("Report"),
        html.Button("Download Report (.odt)", id="report-btn", n_clicks=0),
        dcc.Download(id="report-download"),
    ], className="section"),
])


@app.callback(
    Output("cards-row","children"),
    Output("alerts-section","children"),
    Output("cpu-graph","figure"),
    Output("apps-table","children"),
    Output("ip-table","children"),
    Output("usage-summary","children"),
    Output("prediction-text","children"),
    Input("interval","n_intervals"),
)
def update(n):
    global prev_io
    io = get_network_io()
    speed_sent = (io["bytes_sent"] - prev_io["bytes_sent"]) / 2
    speed_recv = (io["bytes_recv"] - prev_io["bytes_recv"]) / 2
    record_usage(int(speed_sent), int(speed_recv))
    prev_io = io

    wifi = get_wifi_signal()
    procs = get_top_processes(8)
    ips = get_active_connections(8)
    summary = get_usage_summary()
    prediction = predict_next_usage()
    conn_count = sum(p["connections"] for p in procs)

    alerts = check_alerts(int(speed_sent + speed_recv), 0, wifi["signal"], conn_count, ips)

    cards = [
        _card("Sent", f"{speed_sent/1024:.1f} KB/s"),
        _card("Received", f"{speed_recv/1024:.1f} KB/s"),
        _card("WiFi", f"{wifi['signal'] or '?'}%% ({wifi['quality']})"),
        _card("Connections", str(conn_count)),
        _card("Daily", f"{summary['daily']} MB"),
    ]

    alert_divs = [html.Div(a, className="alert-box") for a in alerts]

    fig = go.Figure()
    names = [p["name"][:20] for p in procs]
    cpus = [p["cpu"] for p in procs]
    fig.add_trace(go.Bar(x=names, y=cpus, marker_color="#00d4ff"))
    fig.update_layout(
        paper_bgcolor="#0a0a1a", plot_bgcolor="#0a0a1a",
        font_color="#fff", margin=dict(l=40,r=20,t=20,b=60),
        xaxis=dict(tickangle=-45), yaxis=dict(title="CPU %%")
    )

    apps_tbl = html.Table([
        html.Thead(html.Tr([html.Th(h) for h in ["App","CPU %%","Memory %%","Connections"]])),
        html.Tbody([html.Tr([
            html.Td(p["name"][:25]), html.Td(p["cpu"]),
            html.Td(p["memory"]), html.Td(p["connections"])
        ]) for p in procs])
    ])

    ip_tbl = html.Table([
        html.Thead(html.Tr([html.Th(h) for h in ["IP","Port","Status","Country"]])),
        html.Tbody([html.Tr([
            html.Td(c["ip"]), html.Td(c["port"]),
            html.Td(c["status"]), html.Td(c["country"])
        ]) for c in ips])
    ])

    usage_div = html.Div([
        html.Span(f"Daily: {summary['daily']} MB  |  "),
        html.Span(f"Weekly: {summary['weekly']} MB  |  "),
        html.Span(f"Monthly: {summary['monthly']} MB"),
    ])

    return cards, alert_divs, fig, apps_tbl, ip_tbl, usage_div, prediction


def _card(title, value):
    return html.Div([html.H3(title), html.Div(value, className="value")], className="card")


@app.callback(
    Output("loc-list","children"),
    Input("loc-btn","n_clicks"),
    State("loc-input","value"),
    prevent_initial_call=False,
)
def handle_location(n, loc_name):
    if n and loc_name:
        wifi = get_wifi_signal()
        save_location(loc_name, wifi["signal"])
    locs = get_locations()
    if not locs:
        return html.P("No locations captured yet.", style={"color":"#888"})
    rows = []
    for l in locs:
        sig = l["signal"] or 0
        color = "#00ff88" if sig > 70 else "#ffaa00" if sig > 40 else "#ff4444"
        quality = "Good" if sig > 70 else "Medium" if sig > 40 else "Poor"
        rows.append(html.Tr([
            html.Td(l["name"]), html.Td(f"{sig}%%", style={"color":color}), html.Td(quality)
        ]))
    return html.Table([
        html.Thead(html.Tr([html.Th("Location"), html.Th("Signal"), html.Th("Quality")])),
        html.Tbody(rows)
    ])


@app.callback(
    Output("report-download","data"),
    Input("report-btn","n_clicks"),
    prevent_initial_call=True,
)
def download_report(n):
    summary = get_usage_summary()
    locs = get_locations()
    prediction = predict_next_usage()
    path = generate_report(summary, locs, prediction)
    return dcc.send_file(path)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
