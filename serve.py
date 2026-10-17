"""Production server for running the site on this PC behind a Cloudflare Tunnel (Windows-friendly).

    python serve.py            # then: cloudflared tunnel --url http://127.0.0.1:5000
or just run start_public.ps1, which starts both.
"""
import os

# Cloudflare terminates HTTPS and forwards to us over plain HTTP: trust its X-Forwarded-* headers,
# mark session cookies Secure, and load the AI models before the first scan.
os.environ.setdefault("ATTIRE_BEHIND_PROXY", "1")
os.environ.setdefault("ATTIRE_WEB_HTTPS", "1")
os.environ.setdefault("ATTIRE_WARM_UP", "1")

from waitress import serve  # noqa: E402

from web_app import app  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("ATTIRE_WEB_PORT", "5000"))
    print(f"Attire Checker serving on http://127.0.0.1:{port}")
    serve(app, host="127.0.0.1", port=port, threads=8, channel_timeout=300)
