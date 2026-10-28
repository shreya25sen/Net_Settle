"""Local web UI for Net-Settle (standard library only)."""
import json
import os
import tempfile
import threading
import webbrowser
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import storage
from expense_manager import format_money, money_to_paise
from reports import export_report
from settlement import SettlementEngine

UI_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ui", "index.html"
)
LOCK = threading.Lock()
MAX_BODY = 64 * 1024


def parse_fee(text):
    """Fee is optional: empty or 0 means no fee."""
    text = (text or "").strip()
    if not text:
        return 0
    try:
        if Decimal(text) == 0:
            return 0
    except InvalidOperation:
        raise ValueError("Enter a valid fee amount.")
    return money_to_paise(text)


def build_state(app, fee_text=""):
    settlements, warning = [], None
    try:
        settlements = SettlementEngine(app.balances).minimise_transfers()
    except ValueError as error:
        warning = str(error)

    fee = parse_fee(fee_text)
    balances = []
    for name in sorted(app.members):
        paise = app.balances[name]
        balances.append({
            "name": name,
            "paise": paise,
            "text": format_money(abs(paise)),
            "status": "owes" if paise < 0
            else "receives" if paise > 0 else "settled",
        })

    return {
        "members": sorted(app.members),
        "balances": balances,
        "expenses": [
            {
                "payer": e["payer"],
                "description": e["description"],
                "category": e["category"],
                "participants": e["participants"],
                "amount": format_money(e["amount"]),
            }
            for e in app.expenses
        ],
        "settlements": [
            {"from": s["from"], "to": s["to"],
             "amount": format_money(s["amount"])}
            for s in settlements
        ],
        "transfer_count": len(settlements),
        "total_fees": format_money(
            SettlementEngine.estimate_fees(settlements, fee)
        ),
        "total_expense": format_money(app.total_expense()),
        "warning": warning,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "NetSettle/1.0"

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    # ---- helpers -------------------------------------------------
    def _send(self, code, body, content_type="application/json",
              headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, message):
        self._send(code, {"error": message})

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("Request too large.")
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON.")
        if not isinstance(data, dict):
            raise ValueError("Invalid request.")
        return data

    # ---- routes --------------------------------------------------
    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path in ("/", "/index.html"):
                with open(UI_FILE, "rb") as file:
                    self._send(200, file.read(), "text/html; charset=utf-8")
            elif url.path == "/api/state":
                fee = parse_qs(url.query).get("fee", [""])[0]
                with LOCK:
                    self._send(200, build_state(storage.load(), fee))
            elif url.path == "/api/report.csv":
                with LOCK:
                    app = storage.load()
                    settlements = SettlementEngine(
                        app.balances
                    ).minimise_transfers()
                    fd, tmp = tempfile.mkstemp(suffix=".csv")
                    os.close(fd)
                    try:
                        export_report(app, settlements, tmp)
                        with open(tmp, "rb") as file:
                            content = file.read()
                    finally:
                        os.remove(tmp)
                self._send(
                    200, content, "text/csv; charset=utf-8",
                    {"Content-Disposition":
                     'attachment; filename="settlement_report.csv"'},
                )
            else:
                self._error(404, "Not found.")
        except ValueError as error:
            self._error(400, str(error))
        except OSError as error:
            self._error(500, f"Server error: {error}")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            with LOCK:
                app = storage.load()
                if path == "/api/members":
                    app.add_member(str(data.get("name", "")))
                elif path == "/api/expenses":
                    participants = data.get("participants")
                    if not isinstance(participants, list):
                        raise ValueError("Select at least one participant.")
                    app.add_expense(
                        str(data.get("payer", "")).strip(),
                        money_to_paise(str(data.get("amount", ""))),
                        str(data.get("description", "")),
                        str(data.get("category", "")),
                        [str(p).strip() for p in participants],
                    )
                elif path == "/api/reset":
                    from expense_manager import ExpenseManager
                    app = ExpenseManager()
                else:
                    self._error(404, "Not found.")
                    return
                storage.save(app)
                self._send(200, build_state(app))
        except ValueError as error:
            self._error(400, str(error))
        except OSError as error:
            self._error(500, f"Server error: {error}")


def run(port=8000, open_browser=True):
    """Serve the UI until Ctrl+C. Returns so the CLI can carry on."""
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"\nNet-Settle UI running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nUI stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
