from __future__ import annotations

from html import escape
from typing import Any

from weasyprint import HTML


def render_report_pdf(user: Any, payload: dict[str, Any]) -> bytes:
    username = escape(str(getattr(user, "username", "Unknown")))
    lichess_id = escape(str(getattr(user, "lichess_id", "N/A")))
    games_analyzed = payload.get("games_analyzed", 0)
    winrate = payload.get("winrate", 0)

    tilt = payload.get("tilt") if isinstance(payload.get("tilt"), dict) else {}
    tilt_level = escape(str(tilt.get("level", "N/A")))
    tilt_score = tilt.get("score", 0)
    signals = tilt.get("signals") if isinstance(tilt.get("signals"), dict) else {}

    openings = payload.get("openings") if isinstance(payload.get("openings"), dict) else {}
    top_openings = openings.get("favorite") if isinstance(openings.get("favorite"), list) else []
    top_openings = top_openings[:3]

    weaknesses = payload.get("weaknesses") if isinstance(payload.get("weaknesses"), dict) else {}
    weakness_items = weaknesses.get("items") if isinstance(weaknesses.get("items"), list) else []

    time_management = (
        payload.get("time_management") if isinstance(payload.get("time_management"), dict) else {}
    )

    openings_rows = "".join(
        f"<tr><td>{escape(str(item.get('opening', 'Unknown')))}</td>"
        f"<td>{item.get('games', 0)}</td><td>{item.get('winrate', 0)}%</td></tr>"
        for item in top_openings
        if isinstance(item, dict)
    )
    if not openings_rows:
        openings_rows = "<tr><td colspan='3'>No opening data</td></tr>"

    weaknesses_rows = "".join(
        f"<tr><td>{escape(str(item.get('label', 'Unknown')))}</td>"
        f"<td>{escape(str(item.get('severity', 'N/A')))}</td>"
        f"<td>{item.get('ratio', 0)}%</td></tr>"
        for item in weakness_items
        if isinstance(item, dict)
    )
    if not weaknesses_rows:
        weaknesses_rows = "<tr><td colspan='3'>No weakness data</td></tr>"

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: Arial, sans-serif;
      color: #111827;
      background: #ffffff;
      font-size: 12px;
      line-height: 1.45;
      margin: 24px;
    }}
    h1, h2 {{
      margin: 0 0 8px 0;
      color: #0f172a;
    }}
    .meta {{
      margin-bottom: 16px;
      color: #334155;
    }}
    .section {{
      margin-top: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 6px 8px;
      text-align: left;
    }}
    th {{
      background: #f1f5f9;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .card {{
      border: 1px solid #cbd5e1;
      padding: 10px;
      border-radius: 6px;
      background: #ffffff;
    }}
    .label {{
      color: #475569;
      font-size: 11px;
    }}
    .value {{
      font-size: 16px;
      font-weight: 700;
      margin-top: 2px;
    }}
    ul {{
      margin: 8px 0 0 18px;
      padding: 0;
    }}
  </style>
</head>
<body>
  <h1>Chess Behavioral Report</h1>
  <div class="meta">
    User: <strong>{username}</strong> ({lichess_id})<br>
    Games analyzed: <strong>{games_analyzed}</strong><br>
    Winrate: <strong>{winrate}%</strong>
  </div>

  <div class="section">
    <h2>Tilt Summary</h2>
    <div class="grid">
      <div class="card">
        <div class="label">Tilt Level</div>
        <div class="value">{tilt_level}</div>
      </div>
      <div class="card">
        <div class="label">Tilt Score</div>
        <div class="value">{tilt_score}</div>
      </div>
    </div>
    <ul>
      <li>Losing streak: {signals.get("losing_streak", 0)}</li>
      <li>Rapid requeue after losses: {signals.get("rapid_requeue_after_loss", 0)}</li>
      <li>Recent loss ratio: {signals.get("recent_loss_ratio", 0)}%</li>
      <li>Accuracy drop placeholder: {signals.get("accuracy_drop_placeholder", 0)}%</li>
    </ul>
  </div>

  <div class="section">
    <h2>Top Openings</h2>
    <table>
      <thead><tr><th>Opening</th><th>Games</th><th>Winrate</th></tr></thead>
      <tbody>{openings_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Weaknesses</h2>
    <table>
      <thead><tr><th>Weakness</th><th>Severity</th><th>Ratio</th></tr></thead>
      <tbody>{weaknesses_rows}</tbody>
    </table>
  </div>

  <div class="section">
    <h2>Time Management</h2>
    <table>
      <tbody>
        <tr><th>Average move time</th><td>{time_management.get("average_move_time", 0)}s</td></tr>
        <tr><th>Fast move ratio</th><td>{time_management.get("fast_move_ratio", 0)}%</td></tr>
        <tr><th>Panic move ratio</th><td>{time_management.get("panic_move_ratio", 0)}%</td></tr>
        <tr><th>Time pressure score</th><td>{time_management.get("time_pressure_score", 0)}</td></tr>
        <tr><th>Data source</th><td>{escape(str(time_management.get("source", "N/A")))}</td></tr>
      </tbody>
    </table>
  </div>
</body>
</html>
"""

    return HTML(string=html).write_pdf()
