import os

import uvicorn


def get_port() -> int:
    raw_port = os.getenv("PORT", "8000").strip()
    try:
        return int(raw_port)
    except ValueError as exc:
        raise RuntimeError(f"Invalid PORT value: {raw_port!r}") from exc


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=get_port(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
