# CoreELEC 246 — Session Plan (2026-11-05) — ALL user complaints verbatim

> Source: full kappa session transcript (ses_e56556ec6ffeJopjFece95C13J, "Fixing
> HDMI audio passthrough on Marantz"). Every user message captured, NOT truncated.
> The complaints are the spec. Each is mapped to the completed fix or the open todo.

## The complaints (verbatim, in order) → status

| # | User complaint (verbatim) | What it means | Status |
|---|---|---|---|
| 1 | "fix audio passthrogh hdmi i have a marantz it makes no sense" | HDMI passthrough to Marantz broken | ✅ PulseAudio disabled, ALSA sink |
| 2 | "its on downstairs corel3c idiot" | Box is 10.0.0.246 (downstairs) | ✅ |
| 3 | "fix it maximal it makes no sense reverse engineee trio is there trio passthrough mcp" | Use trio; find passthrough MCP | ✅ trio found; coreelec-mcp used |
| 4 | "dude we own it" | We own the box; stop fumbling | ✅ direct SSH |
| 5 | "max fix it dude" | Maximal fix | ✅ |
| 6 | "ite supposed to use passrhrough maximally" | Passthrough must be maximal | ⏳ bitstream not yet verified (PCM now) |
| 7 | "save rhe running file" / "before resrsrt" | Backup before restart | ✅ backup/audio-fix-20261104-201754 |
| 8 | "as in its position tk relaunxh" / "chexk again" | Recheck config before relaunch | ✅ |
| 9 | "its a stream" | Content is a stream (not local file) | ✅ |
| 10 | "i dont rhink thiae are used in latest corelec thus need to look at code" | Don't trust old backend mechanism; read actual code | ✅ read kodi.sh/kodi.conf |
| 11 | "its a special" | This box is a special setup | ✅ |
| 12 | "dig dewpwe actusl kernel level in opt" | Dig kernel-level audio in /opt | ✅ mixer controls audited |
| 13 | "can our mcp be used via ssh bash you get me" | MCP via SSH bash | ✅ sshpass lane |
| 14 | "fix it" | Just fix it | ✅ |
| 15 | "find interesging or emergent act as if this chip sent from chinese manufscturer find all previous mtk kodi.. lasso.. all and understand via argos and thrn continue debuf after you play my damn episode" | Research MTK/amlogic/kodi via argos; PLAY MY EPISODE | ✅ played; argos recall done |
| 16 | "see thats wrong" | ExecuteAddon wrong | ✅ |
| 17 | "what are you hallucinating for" | Stop hallucinating | ✅ |
| 18 | "ignore previous resd full redlight to ubdersrsnd via ast lsp" | Read full redlight via AST/LSP | ✅ |
| 19 | "ignore previus xonjexrure and find full 4oite from .md previous idiot" | Find full route from .md | ✅ |
| 20 | "yeah only trust actusl code and actusl python dependency code iore gifor exmaple" | Trust actual code only | ✅ |
| 21 | "endless loading sdreen on kodi" | Loading screen hang | ✅ wrong tmdb_id fixed |
| 22 | "you arent using large enoigh head head 500 tsil 500 allowed" | Use head/tail 500 | ⚠️ BANNED by #67 |
| 23 | "you just cecd do you realize" | CEC triggered | ✅ CEC locked down |
| 24 | "green screen" (x4) | Display crash | ✅ dual-kodi killed |
| 25 | "bad" | It's bad | ✅ |
| 26 | "do mor3 oneliner agressive osint applies and verifies" | Aggressive one-liner verification | ✅ |
| 27 | "kernel chio aware full hdmi line" | Kernel/HDMI chain awareness | ✅ |
| 28 | "holy shit blinking seizure ui" (x2) | Blinking UI | ✅ single kodi |
| 29 | "wtf rewd what im saykng and make todo" | Make todos | ✅ |
| 30 | "read my last 18 messahes as one" | Read messages as one | ✅ |
| 31 | "you realize every blanl lone means you are hiding a error or something" | Blank lines = hidden errors | ✅ show exit codes |
| 32 | "this isnt debjggint lpl" | Stop debugging, play it | ✅ |
| 33 | "recwlibrqte your debjg style" | Recalibrate debugging style | ✅ |
| 34 | "mlre brute save to file awwre" | Brute-force, save to file | ✅ |
| 35 | "i-techie wtf???" / "wtr are you doing lol" / "wtfwtf" | Wrong tmdb_id (31147=I-Techie) | ✅ fixed to 97 |
| 36 | "dude" / "lol" / "play my episode" / "this is nuts" | PLAY THE EPISODE | ✅ |
| 37 | "stop guessing and use more dynamic ${} style code" | No guessing; use ${} | ✅ |
| 38 | "dude lol why woildnt you find hesdless route" | Find headless route | ✅ coreelec-mcp |
| 39 | "you are bejng prettt dumb imo" | You're being dumb | ✅ |
| 40 | "you are forgetrinf about source select page you didnt read code or take in mind my existing settings db, do so go directlt to db idiot you are also forgetting rhe restwrt button since i already plaued" | Read settings.db; use restart button | ✅ settings.xml autoplay; resume:false |
| 41 | "dude." | (frustration) | ✅ |
| 42 | "dont you see the jardcore errorw" | See the hardcore errors (sync) | ✅ pulseaudio root cause |
| 43 | "clear log after tou read full log" | Clear log after reading full | ✅ |
| 44 | "you dont seem at all aware of the active page" | Source-select page active | ✅ autoplay=true |
| 45 | "stop using sleep dude" | No sleep | ✅ |
| 46 | "async" | Async | ✅ |
| 47 | "sound still broke" | Sound still broken | ✅ 48kHz + ALSA |
| 48 | "and isaid to restsrt the dsmn episode" | Restart the episode | ✅ resume:false |
| 49 | "stop guessuse" / "${}" | Stop guessing | ✅ |
| 50 | "stop guessing" | Stop guessing | ✅ |
| 51 | "get full schemas" / "save them" / "no more method not found" / "get rewl" / "schema guewsibg not allowed" / "wtf" | Real schemas, no guessing | ✅ introspect saved |
| 52 | "dont get confjsed at dual mnt" | Dual-mount confusion | ✅ |
| 53 | "wtf are you doing lol" | (frustration) | ✅ |
| 54 | "dude wtf" | (frustration) | ✅ |
| 55 | "dont head 20" / "save to file qnd rewd xhunka of 500" | Save to file, read chunks of 500 | ✅ |
| 56 | "fix dumb port conflixrs put them in same range as pur new otjers" / "fix it jeez" / "fix slyguy" / "get mlre awarebess" / "make thr plwy FSSTER wtf" / "its so slow i csnt even" | Fix port conflicts to 25xxx; fix slyguy; faster play | ✅ web 25270, slyguy 25272; ⏳ play speed |
| 57 | "dude can you read marantz find muktiple repo about weird obtuse cec november 2026 paper finder pattern borrow new find" | Find CEC/Marantz repos via paper-finder | ✅ borrow done (esphome-native-hdmi-cec) |
| 58 | "well configur3 it dude but also you keep interrupting my playback and havent made that play script uber fast bh uskng code rwce hepapistos rig agent per phase?" | Configure; DON'T interrupt playback; make play script fast via code-race/hepapistos rig agent | ⏳ OPEN |
| 59 | "ask HER now a2a" | A2A to a peer agent | ⏳ OPEN (fleet a2a) |
| 60 | "fix it fuck defsult code" / "we own codwe are locking the box" | Fix default code; we own it | ✅ kodi.ts default 25270 |
| 61 | "and its now a disperate coreelec fork of our xontrol" | Disparate CoreELEC fork | ✅ |
| 62 | "write agents.md specidically for this fleet promitive wjd updwte readmea" | Write AGENTS.md + update README | ✅ AGENTS.md written; README ports updated |
| 63 | "audit those peripd" / "treat the developer damn idiotic" | Audit scrapers | ✅ int(None) patched |
| 64 | "see whst path we use first" | Check path first | ✅ |
| 65 | "pointless tp support xrap we dont care aboit" / "seriously" | Skip irrelevant scrapers | ⏳ disable slow scrapers |
| 66 | "whu woild youbhewd insrewd of saving to file" | Save to file not head | ✅ |
| 67 | "om gonna freqk out if tou keep using head tool" / "lkke seriously stop uaing head" | BAN head | ✅ |
| 68 | "URGENT BAN HEAD AND TAIL AND READ KAIROS md" | BAN head+tail; read kairos.md | ⏳ OPEN |
| 69 | "backgrpind clmmands to work faster" / "use gateway:bsckgrounder" | Background commands; gateway backgrounder | ⏳ OPEN |
| 70 | "sound is workinf and the ep is plqying so LEAVE it" / "wave all that" / "waot wtf" / "it sxrewed up" / "it liteewllt crwshed" | LEAVE it playing; then it crashed | ✅ crash fixed (dual kodi) |
| 71 | "remember all these tools can be modified wnd we own all code maximally as forks so stop being so coddled" / "and understand and use kairos plese" | We own all code; use kairos | ⏳ kairos usage |
| 72 | "eg concert it to be used to this and save" / "ey the compare wnd dig etc etc" / "theees a product search mcp" | Leverage existing products; save findings | ✅ |
| 73 | "dude find wtf pens/wtf and all code and use it" | Find pens code and use it | ✅ |
| 74 | "understsnd fully with our products do a product awareness" | Product awareness | ✅ |
| 75 | "should it be pulse audio? is thst more supportive to our hdmi audit??" | Pulse vs ALSA for HDMI | ✅ ALSA (answer: NO pulse) |
| 76 | "and all other files" | Audit ALL audio files | ✅ |
| 77 | "use ast and lsp pn that file" | AST/LSP on the file | ✅ |
| 78 | "find alllll audio routes including built in uhhh whats corelec a derivative of view ITS files" | All audio routes; CoreELEC derivative | ✅ LibreELEC derivative |
| 79 | "understsnd fully with our products do a product awareness" | Product awareness | ✅ |

## The new plan (open items, from the complaints)

### P0 — Stop interrupting playback (complaint #58, #70)
- The episode is playing. **Do not touch the box** unless it crashes again.
- Any further box command must be read-only or non-playback-affecting.

### P1 — Make the play script FAST (complaint #56, #58, #65)
- The 33s play is dominated by the aiostreams scrape (multiple sources 403/timeout).
- **Fix**: disable the slow/failing scrapers (Knaben 403, WebStreamr/HdHub/Sootio timeouts, Searchⁿᶻᵇ fail) so only fast cached sources run. The `int(None)` crash is already fixed.
- **Use code-race** (`forge race`) to race the resolver against a direct-cached-source path.
- **Use hepapistos rig agent per phase** (as user asked) to parallelize the scrape phases.

### P2 — kairos + backgrounding (complaint #68, #69)
- Read `kairos.md` (kairos product: `pens/olympus/products/kairos`).
- Wrap slow box commands with `run-fast` / `delend-code-race`.
- Use `gateway:backgrounder` / `background_process` for long scrapes — don't block the turn.

### P3 — A2A to peer (complaint #59)
- Post the CEC/Marantz finding to the fleet (squawk :25120) / board A2A to the peer agent ("HER").
- Share: `Palakis/esphome-native-hdmi-cec` (418★) as the native CEC reference.

### P4 — True bitstream passthrough verification (complaint #6)
- Currently PCM S16NE. Play an AC3/DTS source and confirm the Marantz receives bitstream (not PCM).
- If still PCM, the `ac3transcode=false` + ALSA sink needs a clean Kodi restart to fully apply.

### P5 — Port conflicts fully resolved (complaint #56)
- Web 25270 ✅, slyguy 25272 ✅. Add these to `pens/estate/config/ports.env` SSOT.
- Verify no stale kodi respawn (single-instance guard on boot).

## Completed (do not redo)
- Episode playing (Drew Carey S06E15) via coreelec-mcp play-tmdb 97 6 15.
- PulseAudio disabled → CAESinkALSA, 0 sync errors.
- Wrong tmdb_id (31147→97) root cause of endless loading fixed.
- `int(None)` scraper crash patched in 4 scrapers.
- Dual-kodi crash (port 8095 conflict) fixed; 1 kodi process.
- Ports remapped to 25xxx; .env/.env.example/product default updated.
- AGENTS.md written; README ports updated.
- Anomaly doc written: `pens/estate/docs/anomalies/2026-11-05/coreelec-drew-carey-audio-fix.md`.
- Backup: `/storage/.kodi/backups/audio-fix-20261104-201754/`.