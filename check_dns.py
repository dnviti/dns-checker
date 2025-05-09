#!/usr/bin/env python3
"""
Forever-running DNS monitor.
Resolves DOMAIN_TO_CHECK every INTERVAL seconds.
On failure it writes one ERROR line to stdout/stderr:

YYYY-MM-DDThh:mm:ssZ <TAB> ERROR <TAB> domain <TAB> detail
"""

import logging
import os
import signal
import socket
import sys
import time
from types import FrameType

# ── Settings ───────────────────────────────────────────────────────────────────
DOMAIN   = os.getenv("DOMAIN_TO_CHECK", "example.com")
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "1"))  # seconds

# ── Logging: ISO-8601 in UTC ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s\t%(levelname)s\t%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.Formatter.converter = time.gmtime  # force UTC everywhere

# ── Signal handling ────────────────────────────────────────────────────────────
def _sig_term(signum: int, frame: FrameType | None) -> None:
    """Ignore SIGTERM; just log it so the pod keeps running."""
    logging.warning("Received SIGTERM - exiting gracefully.")
    sys.exit(0)

def _sig_int(signum: int, frame: FrameType | None) -> None:
    """Gracefully exit on Ctrl-C / SIGINT."""
    logging.warning("Received SIGINT - exiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGTERM, _sig_term)   # stay alive on node drain
signal.signal(signal.SIGINT,  _sig_int)    # only Ctrl-C stops us

# ── Helper ─────────────────────────────────────────────────────────────────────
def domain_resolves(host: str) -> tuple[bool, str | None]:
    try:
        socket.gethostbyname(host)
        return True, None
    except socket.gaierror as e:
        return False, str(e)

# ── Main loop ──────────────────────────────────────────────────────────────────
logging.info(
    "DNS monitor started for %s (interval=%ss) - exits ONLY on SIGINT (Ctrl-C)",
    DOMAIN, INTERVAL,
)
while True:
    try:
        ok, detail = domain_resolves(DOMAIN)
        if not ok:
            logging.error("%s\t%s", DOMAIN, detail)
    except Exception as exc:                 # nothing bubbles out
        logging.exception("Unexpected error - continuing: %s", exc)
    time.sleep(INTERVAL)
