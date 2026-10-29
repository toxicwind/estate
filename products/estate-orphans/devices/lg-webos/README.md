# LG webOS TV — OLED65CXPUA (living room)

## Device
- LAN: 10.0.0.176 (wireless), webOS TV 5.6.1 "jhericurl-jimna" (Rockhopper), fw 04.63.25, board O20_ATSC_US
- HDMI-1 serves the CoreELEC box (10.0.0.246, kodi-fleet 246)

## Access routes (verified 2026-10-28)
1. **Dev Mode SSH (prisoner)** — Developer Mode app ON TV, port **9922**, user `prisoner`.
   - TV runs **OpenSSH 6.1**: host key is ssh-rsa ONLY. Modern ssh needs:
     `-o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa`
   - Auth = dev-mode **private key**, fetched from the TV key server:
     `GET http://10.0.0.176:9991/webos_rsa` (key server only listens while the dev app is foregrounded!)
   - The key downloads **passphrase-encrypted** (Proc-Type PEM, AES-128-CBC). Passphrase = the 6-char
     case-sensitive one on the dev app screen. Decrypt:
     `openssl rsa -in lg-tv_webos -passin pass:<PW> -out lg-tv_webos_clear`
   - ares-cli device entry: host 10.0.0.176, port 9922, user prisoner, privateKey openSsh: lg-tv_webos_clear.
     NOTE: `ares-setup-device -i <ip>` MISPARSES the ip into the description — edit
     `~/.webos/tv/novacom-devices.json` by hand (SSOT).
   - Do NOT `npm i -g --force @webosose/ares-cli` alongside `@webos-tools/cli` — the bins collide;
     @webos-tools/cli (profile tv, dataDir .webos/tv) is the working one.
2. **Root services** — TV is ROOTED (org.webosbrew.hbchannel.service + com.pirate.refresh.service +
   com.willinux.tvh.app.proxy installed; hbchannel ships dropbear/telnetd but root dropbear/telnet are
   netns-isolated: visible ports from host = 9922 only; 9111/18181/23 are inside other netns).

## Apps installed (2026-10-28)
- **space.nuvio.webos 1.2.10** — official NuvioTV-webOS.ipk from NuvioMedia/NuvioTVSmart releases
  (★816 repo, webOS 5+ baseline). Launch: `ares-launch --device lg-tv space.nuvio.webos`.
- com.toxicwind.streamers (custom Stremio-theater build; see ranch/nuvio/nuvio-webos).
  GOTCHA that cost hours: **ares rejects ServiceIDs that don't start with the app id**
  ("ServiceID must start with package id"). Merged identity: app com.toxicwind.streamers + child service
  com.toxicwind.streamers.server (rename in app/services.json + service/services.json + launch.js +
  index.html luna call). Stremio server also needs HOME set to the service dir (launch.js patch) or it
  ENOENTs /media/developer/.stremio-server and 500s.

## Upstream repos that solved this (blackbird-grade finds)
- NuvioMedia/NuvioTVSmart (official webOS+tizen packaging, EngineFS local service)
- kieranbrown/stremio-webos (★44; our Makefile is a fork of it; io.strem.tv identity)
- webosbrew/webos-homebrew-channel (root exec service luna://org.webosbrew.hbchannel.service/exec)

## Debugging cheat-sheet
- App console: `ares-inspect --device lg-tv -a <appid>` (streams; ws port is TV-side, jail-isolated)
- Install service state: ares-install -v prints luna appInstallService progress (state: ipk parsing →
  installing : service installing → installed)
- luna-send is root-only; luna-send-pub works from prisoner: `luna-send-pub -n <uri> <payload>`
