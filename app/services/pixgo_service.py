import json
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://pixgo.org/api/v1"


class PixGoError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


def _request(method, path, api_key, payload=None, timeout=25):
    if not api_key:
        raise PixGoError("API key PIXGO nao configurada.", 400)

    url = BASE_URL + path
    headers = {
        "Accept": "application/json",
        "X-API-Key": api_key,
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw}
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"message": raw}
        message = parsed.get("message") or parsed.get("error") or f"Erro PIXGO ({err.code})"
        raise PixGoError(message, err.code, parsed)
    except urllib.error.URLError as err:
        raise PixGoError(f"Falha de conexao com a PIXGO: {err.reason}", 502)


def create_payment(api_key, payload):
    return _request("POST", "/payment/create", api_key, payload)


def get_payment_status(api_key, payment_id):
    pid = urllib.parse.quote(str(payment_id), safe="")
    return _request("GET", f"/payment/{pid}/status", api_key)


def get_payment_details(api_key, payment_id):
    pid = urllib.parse.quote(str(payment_id), safe="")
    return _request("GET", f"/payment/{pid}", api_key)
