# -*- coding: utf-8 -*-
"""Eternal Helper — script entrypoint.

Kodi's RunScript(script.eternal.helper, mode=...) requires a default.py at the
addon ROOT. This dispatches to the real implementation in resources/lib.
"""
import sys

sys.path.insert(0, __path__[0] if "__path__" in globals() else __file__.rsplit("/", 1)[0])
sys.path.insert(0, __file__.rsplit("/", 1)[0] + "/resources/lib")

from default import main  # noqa: E402

if __name__ == "__main__":
    main()