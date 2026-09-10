---
name: codex-vpn-proxy-recovery
title: Codex VPN Proxy Recovery Without Tun
description: Use when Codex Desktop on Windows shows 正在重新连接, retrying sampling request, request timed out, or repeated 1/5–5/5 retries while v2rayN/sing-box is active and Tun mode is disabled. Diagnose the Windows proxy versus Codex native-process proxy path, automatically configure HTTP/HTTPS/WebSocket proxy environment variables, restart Codex with explicit inheritance, verify HTTP and WebSocket reachability, and distinguish local proxy failures from OpenAI 5xx service errors.
category: engineering
audience: codex-core
tags: [codex, windows, v2rayn, sing-box, vpn, proxy, tun, websocket, troubleshooting]
status: active
score: 10.0
---

# Codex VPN proxy recovery without Tun

Apply this skill when Codex Desktop works only after enabling Tun, or when the
UI shows `正在重新连接 1/5` through `5/5` while v2rayN/sing-box is running.
Target Windows and a local HTTP/mixed proxy, normally `127.0.0.1:10808`.

## Diagnosis model

Treat the path as two separate layers:

```text
Codex Desktop / codex.exe
        ├─ native HTTP/SSE Responses traffic  -> HTTP_PROXY / HTTPS_PROXY
        └─ WebSocket traffic                  -> WS_PROXY / WSS_PROXY
v2rayN mixed listener 127.0.0.1:10808 -> selected VLESS/sing-box node
```

Do not infer that the Windows “system proxy” setting covers `codex.exe`.
Electron/browser traffic and the native Codex app-server process can use
different proxy mechanisms. Tun hides this mismatch by intercepting packets;
the goal here is to make the process-level path explicit.

## Mandatory read-only checks

1. Verify the proxy listener before changing anything:

   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 10808
   ```

   Accept a different port only when the user or v2rayN configuration proves
   that it is the active HTTP/mixed listener.

2. Inspect, without printing secrets:

   ```powershell
   Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' |
     Select-Object ProxyEnable,ProxyServer,AutoConfigURL
   netsh winhttp show proxy
   Get-ItemProperty 'HKCU:\Environment' |
     Select-Object HTTP_PROXY,HTTPS_PROXY,WS_PROXY,WSS_PROXY,ALL_PROXY,NO_PROXY
   ```

3. Test the local HTTP proxy directly. A successful CONNECT followed by
   `401 Unauthorized` from the API endpoint proves the proxy path; it does not
   require an API key:

   ```powershell
   curl.exe -I --proxy http://127.0.0.1:10808 `
     --connect-timeout 10 https://api.openai.com/v1/models
   ```

4. Inspect Codex evidence when available:

   - `C:\Users\<user>\.codex\logs_2.sqlite`
   - `codex_core::responses_retry` with `request timed out`
   - `codex_app_server_transport::transport::remote_control::websocket` with
     `os error 10060`
   - `codex_core::spawn` environment snapshots

   Use the log database read-only and redact tokens, URLs containing auth
   material, request bodies, and user content.

5. Compare process connections:

   ```powershell
   $ids = Get-Process codex -ErrorAction SilentlyContinue |
     Select-Object -ExpandProperty Id
   Get-NetTCPConnection -ErrorAction SilentlyContinue |
     Where-Object { $_.OwningProcess -in $ids -and
       $_.State -in 'SynSent','Established' } |
     Select-Object OwningProcess,State,LocalAddress,LocalPort,RemoteAddress,RemotePort
   ```

   Direct external `SYN_SENT` entries while the only stable local connection
   is `127.0.0.1:10808` indicate incomplete process-level proxy inheritance.

## Automatic repair

Run the bundled script from an elevated or normal PowerShell session as
appropriate for the local installation:

```powershell
powershell -ExecutionPolicy Bypass -File `
  .\scripts\repair_codex_proxy.ps1 -ProxyPort 10808 -RestartCodex
```

The script must:

1. Refuse to mutate settings if the selected local port is not listening.
2. Persist these user-level variables as `http://127.0.0.1:<port>`:
   `HTTP_PROXY`, `HTTPS_PROXY`, `WS_PROXY`, and `WSS_PROXY`.
3. Preserve existing `NO_PROXY` entries and ensure `localhost`, `127.0.0.1`,
   and `::1` bypass the proxy.
4. Restart Codex through a detached PowerShell process that explicitly sets
   the same variables before launching `ChatGPT.exe`. Merely writing the
   registry is insufficient because already-running processes retain their
   old environment blocks.
5. Never enable Tun, change the selected node, or expose the proxy to LAN.

Use `-SetAllProxy` only as a second-line fallback when HTTP/HTTPS and WSS
remain direct. Do not set undocumented `CODEX_NETWORK_PROXY_*` variables
unless a managed enterprise policy explicitly supplies them.

## Verification after repair

1. Confirm the new Codex process has no direct external `SYN_SENT`; its active
   outbound sockets should be established to `127.0.0.1:<port>`.
2. Run Codex's redacted diagnostic with the proxy variables present and inspect:

   - `network.env.status = ok`
   - `network.provider_reachability.status = ok`
   - `network.websocket_reachability.status = ok`
   - WebSocket detail containing `HTTP 101 Switching Protocols`

3. Check the last few minutes of `logs_2.sqlite`. A successful repair should
   stop new `request timed out`, `retrying sampling request`, and `os error
   10060` entries. Ignore pre-restart entries.

## Routing and failure classification

When v2rayN uses rule mode, force these domains to the proxy if they are not
already covered:

```text
chatgpt.com
*.chatgpt.com
openai.com
*.openai.com
oaistatic.com
*.oaistatic.com
oaiusercontent.com
*.oaiusercontent.com
```

Use `http://` for `HTTP_PROXY` and `HTTPS_PROXY` when the v2rayN listener is
HTTP/mixed. Do not substitute `socks5://` unless the selected port is proven to
be SOCKS-only.

Classify failures before changing more settings:

- `request timed out`, `os error 10060`, direct `SYN_SENT`: local proxy
  inheritance, routing, DNS/IPv6, firewall, or WebSocket proxy path.
- `HTTP 500/503`, `biscuit_baker_service_me_circuit_open`: upstream OpenAI
  service-side failure; do not claim that a local Tun or proxy change fixed it.
- HTTP `401` from `api.openai.com/v1/models` without an API key: expected and
  useful evidence that the proxy CONNECT succeeded.
- Cloudflare `403` from a bare curl request to ChatGPT: not sufficient to judge
  Codex authentication; use Codex doctor and application logs instead.

## Safety and handoff

Do not print `auth.json`, bearer tokens, cookies, full request bodies, or full
Codex conversation logs. Report only redacted endpoints, status classes,
process-level connection state, and whether new retry errors remain.

If the listener is absent, stop and tell the user to start v2rayN or select a
valid local HTTP/mixed port. If WebSocket remains blocked after the proxy is
definitely inherited, inspect v2rayN routing and the proxy's WebSocket/CONNECT
support before considering `ALL_PROXY`.
