"""
Write a file into this repo from a GitHub Actions job (contents API), or to
the working tree when run locally without GITHUB_TOKEN.
"""
import base64, json, os, urllib.error, urllib.request

OWNER, REPO = "edwardphill", "stockpicker"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"

def _headers(token):
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json", "User-Agent": "StockPicker/1.0"}

def put_file(path, content_bytes, message):
    """Create or update `path` with `content_bytes`. Local write without a token."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(content_bytes)
        return
    url = f"{API}/{path}"
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=_headers(token)), timeout=15) as r:
            sha = json.loads(r.read())["sha"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
    body = {"message": message, "content": base64.b64encode(content_bytes).decode()}
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=_headers(token), method="PUT")
    urllib.request.urlopen(req, timeout=15).read()
