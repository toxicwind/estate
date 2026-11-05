# -*- coding: utf-8 -*-
import sys
from urllib.parse import parse_qsl, unquote
from modules.router import routing, sys_exit_check
# from modules.kodi_utils import logger


def main():
    routing(sys)
    # Kodi may pass the plugin query as a single URL-encoded blob (e.g. via
    # Files.GetDirectory) — unquote it first so parse_qsl splits on real '&'.
    q = unquote(sys.argv[2][1:]) if len(sys.argv) > 2 else ""
    params = dict(parse_qsl(q, keep_blank_values=True)) if q else {}
    mode = params.get('mode', 'navigator.main')
    if sys_exit_check(mode): sys.exit(1)


if __name__ == "__main__":
    main()
