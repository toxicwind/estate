> **toxicwind fork.** Base:
> [lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) **v0.16.1b1**
> (MIT). Fork divergences in this snapshot:
>
> - **chrome150 as the default impersonation target** — `DEFAULT_CHROME =
>   "chrome150"` in `curl_cffi/requests/impersonate.py`, fingerprint entry in
>   `curl_cffi/fingerprints.py` (commit `306aed1`: bump to curl-impersonate
>   2.1.0, add chrome150)
> - **`curl-cffi` CLI** — `curl_cffi/cli/` (`doctor`, `parse`, `pro`,
>   `request`, `run`; entry via `python -m curl_cffi` / `__main__.py`)
> - **`imp-fetch` agent skill** — `skills/imp-fetch/SKILL.md`: a `web_fetch`
>   replacement with browser impersonation, HTTP/2 and HTTP/3 out of the box,
>   and `.http`/`.har` replay in batch
>
> The README below is the upstream one and remains accurate for the base
> library.

---
