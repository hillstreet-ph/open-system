#!/usr/bin/env python3
"""Hermes dashboard admin for production (open-system.space), run from GitHub Actions.

Credentials never pass through a person: the dashboard login is read from the Railway
service variables with RAILWAY_TOKEN, and no secret value is ever printed. Output lists
names, providers, URLs and booleans only.

  hermes-admin.py diagnose     model routing, fallbacks, web provider, MCP servers,
                               per-profile key presence
  hermes-admin.py inventory    plugins, toolsets, skills and MCP servers with their state
  hermes-admin.py fix          restore the intended routing and settings, then restart the gateway:
                               - default: main = open-connect (named provider `openai`,
                                 model open-connect/auto); model auto-rotation off (it kept
                                 rewriting the main model to openrouter models served from
                                 open-connect with the wrong key -> HTTP 401)
                               - web.search_backend `brave` (no longer registered) -> keenable
                               - profiles whose main model is not open-connect get the routing
                                 block of a healthy open-connect profile
                               - profiles missing the open-connect keys get them copied from a
                                 healthy profile (values never printed)

Env: RAILWAY_TOKEN, RAILWAY_SERVICE_ID, RAILWAY_ENVIRONMENT_ID, DASHBOARD_URL (optional).
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

RAILWAY_API = "https://backboard.railway.com/graphql/v2"
BASE = os.environ.get("DASHBOARD_URL", "https://open-system.space").rstrip("/")
UA = "open-system-ops/1.0"
OPEN_CONNECT_KEY = "HERMES_CUSTOM_OPENAI_API_KEY"
SECRETISH = re.compile(r"(key|token|secret|password|passwd|auth|cookie|bearer)", re.I)


def die(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


# --- Railway -------------------------------------------------------------------------
def railway(query: str, variables: dict) -> dict:
    token = os.environ["RAILWAY_TOKEN"]
    body = json.dumps({"query": query, "variables": variables}).encode()
    for header in ({"Project-Access-Token": token}, {"Authorization": f"Bearer {token}"}):
        req = urllib.request.Request(RAILWAY_API, body, {"Content-Type": "application/json", "User-Agent": UA, **header})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
        except urllib.error.HTTPError:
            continue
        if not data.get("errors"):
            return data["data"]
    die("Railway API query failed (token or ids)")
    return {}


def service_vars() -> dict:
    s, e = os.environ["RAILWAY_SERVICE_ID"], os.environ["RAILWAY_ENVIRONMENT_ID"]
    project = railway("query($s:String!){service(id:$s){projectId}}", {"s": s})["service"]["projectId"]
    return railway("query($p:String!,$s:String!,$e:String!){variables(projectId:$p,serviceId:$s,environmentId:$e)}",
                   {"p": project, "s": s, "e": e})["variables"]


# --- Dashboard -----------------------------------------------------------------------
class Dashboard:
    def __init__(self, user: str, password: str) -> None:
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        status, _ = self.call("POST", "/auth/password-login",
                              {"username": user, "password": password, "next": "/", "provider": "basic"})
        if status >= 400:
            die(f"dashboard login failed (HTTP {status}); response body suppressed")

    def call(self, method: str, path: str, payload: dict | None = None) -> tuple[int, object]:
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(BASE + path, data, method=method,
                                     headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA})
        try:
            with self.opener.open(req, timeout=60) as r:
                raw = r.read()
                status = r.status
        except urllib.error.HTTPError as err:  # never echo bodies: some endpoints reflect input
            return err.code, None
        try:
            return status, json.loads(raw or b"null")
        except ValueError:
            return status, None

    def get(self, path: str) -> object:
        status, body = self.call("GET", path)
        if status >= 400:
            die(f"GET {path.split('?')[0]} -> HTTP {status}")
        return body


def login() -> Dashboard:
    env = service_vars()
    user_keys = [k for k in env if k.startswith("HERMES_DASHBOARD") and re.search(r"USER", k)]
    pass_keys = [k for k in env if k.startswith("HERMES_DASHBOARD") and re.search(r"PASS", k) and "HASH" not in k]
    print(f"dashboard credential variables: user={user_keys} password={pass_keys}")
    if not user_keys or not pass_keys:
        die("dashboard basic-auth variables not found on the Railway service")
    return Dashboard(env[user_keys[0]], env[pass_keys[0]])


def env_keys(body: object) -> dict[str, bool]:
    """Normalise /api/env responses to {name: is_set} without keeping any values."""
    out: dict[str, bool] = {}
    items = body.get("env", body.get("vars", body)) if isinstance(body, dict) else body
    if isinstance(items, dict):
        for k, v in items.items():
            out[k] = bool(v.get("is_set", v.get("set", v.get("value")))) if isinstance(v, dict) else bool(v)
    elif isinstance(items, list):
        for v in items:
            if isinstance(v, dict) and (v.get("key") or v.get("name")):
                out[v.get("key") or v.get("name")] = bool(v.get("is_set", v.get("set", v.get("value", True))))
    return out


def profiles(d: Dashboard) -> list[str]:
    body = d.get("/api/profiles")
    items = body.get("profiles", body) if isinstance(body, dict) else body
    names = []
    for p in items or []:
        names.append(p if isinstance(p, str) else (p.get("name") or p.get("id")))
    return [n for n in names if n]


def config(d: Dashboard, profile: str | None = None) -> dict:
    q = "?" + urllib.parse.urlencode({"profile": profile}) if profile else ""
    body = d.get(f"/api/config/raw{q}")
    text = (body.get("yaml") or body.get("yaml_text")) if isinstance(body, dict) else None
    if text is None:
        die(f"config/raw returned no yaml (keys: {sorted(body) if isinstance(body, dict) else type(body).__name__})")
    return yaml.safe_load(text) or {}


def routing(cfg: dict) -> str:
    """One-line model routing summary: provider/model/base_url and the fallback chain."""
    m = cfg.get("model") if isinstance(cfg.get("model"), dict) else {"default": cfg.get("model")}
    fb = cfg.get("fallback_providers") or cfg.get("fallback_models") or cfg.get("fallback_model") or []
    if isinstance(fb, dict):
        fb = [fb]
    chain = ", ".join(f"{f.get('provider')}:{f.get('model')}@{f.get('base_url', '')}" if isinstance(f, dict) else str(f)
                      for f in fb)
    web = (cfg.get("web") or {}).get("backend") or (cfg.get("web") or {}).get("search_backend") or (cfg.get("web") or {}).get("provider")
    return (f"main={m.get('provider')}:{m.get('default') or m.get('model')}@{m.get('base_url', '')} "
            f"fallbacks=[{chain}] web={web}")


def scrub(obj: object) -> object:
    """Drop anything that looks secret before printing."""
    if isinstance(obj, dict):
        return {k: ("<set>" if SECRETISH.search(str(k)) and v else scrub(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(x) for x in obj]
    if isinstance(obj, str) and len(obj) > 40 and not obj.startswith("http"):
        return "<long-string>"
    return obj


def diagnose(d: Dashboard) -> None:
    cfg = config(d)
    print("== top-level config sections:", sorted(cfg))
    for key in ("model", "provider", "providers", "custom_providers", "fallback_model", "fallback_models",
                "fallback_providers", "web", "tools", "browser", "auxiliary", "delegation"):
        if key in cfg:
            print(f"== {key}:\n" + yaml.safe_dump(scrub(cfg[key]), sort_keys=False, width=200)[:4000])
    mcp = cfg.get("mcp_servers") or cfg.get("mcp", {}).get("servers") or {}
    if isinstance(mcp, dict):
        print("== mcp servers:")
        for name, spec in mcp.items():
            spec = spec or {}
            print(f"  {name}: url={spec.get('url', '-')} transport={spec.get('transport', '-')} "
                  f"command={spec.get('command', '-')} enabled={spec.get('enabled', True)}")
    print("== profiles and key presence (names only):")
    for name in profiles(d):
        q = urllib.parse.urlencode({"profile": name})
        keys = env_keys(d.get(f"/api/env?{q}"))
        provider_keys = sorted(k for k, v in keys.items() if v and re.search(r"(API_KEY|TOKEN)$", k))
        print(f"  {name}: {OPEN_CONNECT_KEY}={'yes' if keys.get(OPEN_CONNECT_KEY) else 'NO'} "
              f"keys_set={len([v for v in keys.values() if v])} provider_keys={provider_keys}")
        print(f"    {routing(config(d, name))}")
        providers = config(d, name).get("custom_providers") or config(d, name).get("providers") or []
        if providers:
            print(f"    providers: {yaml.safe_dump(scrub(providers), default_flow_style=True, width=400).strip()[:1200]}")


OPEN_CONNECT_URL = "https://open-connect.site/v1"
OPEN_CONNECT_KEYS = (OPEN_CONNECT_KEY, "OPEN_CONNECT_API_KEY", "MCP_OPEN_CONNECT_API_KEY")
WEB_SEARCH_DEFAULT = "keenable"  # keyless tier; `brave` was renamed `brave-free` and needs a key


def put_config(d: Dashboard, cfg: dict, profile: str | None) -> None:
    text = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True, width=200)
    status, _ = d.call("PUT", "/api/config/raw", {"yaml_text": text, "profile": profile})
    if status >= 400:
        die(f"PUT config ({profile or 'default'}) -> HTTP {status}")


def on_open_connect(cfg: dict) -> bool:
    m = cfg.get("model") if isinstance(cfg.get("model"), dict) else {}
    return m.get("base_url", "").rstrip("/") == OPEN_CONNECT_URL and m.get("provider") in ("custom", "openai") \
        and "open-connect" in str(m.get("default") or m.get("model") or "")


def fix_default(d: Dashboard) -> None:
    cfg = config(d)
    changes = []
    m = cfg.get("model") if isinstance(cfg.get("model"), dict) else {}
    if not on_open_connect(cfg) or m.get("auto_rotation") or m.get("continuous_rotation"):
        m.update({"provider": "openai", "default": "open-connect/auto", "base_url": OPEN_CONNECT_URL,
                  "auto_rotation": False, "continuous_rotation": False})
        cfg["model"] = m
        changes.append("model -> openai:open-connect/auto, rotation off")
    rot = cfg.get("model_rotation")
    if isinstance(rot, dict) and rot.get("enabled"):
        rot["enabled"] = False
        changes.append("model_rotation.enabled -> false")
    web = cfg.get("web") if isinstance(cfg.get("web"), dict) else {}
    if web.get("search_backend") in (None, "", "brave"):
        web["search_backend"] = WEB_SEARCH_DEFAULT
        cfg["web"] = web
        changes.append(f"web.search_backend -> {WEB_SEARCH_DEFAULT}")
    if changes:
        put_config(d, cfg, None)
    print(f"default: {'; '.join(changes) or 'already correct'}")
    print(f"  now {routing(config(d))}")


def fix_profiles(d: Dashboard) -> None:
    names = [n for n in profiles(d) if n != "default"]
    cfgs = {n: config(d, n) for n in names}
    keys = {n: env_keys(d.get("/api/env?" + urllib.parse.urlencode({"profile": n}))) for n in names}
    donors = [n for n in names if on_open_connect(cfgs[n]) and all(keys[n].get(k) for k in OPEN_CONNECT_KEYS)]
    if not donors:
        die("no healthy open-connect profile to copy routing/keys from")
    donor = donors[0]
    print(f"donor profile: {donor}")
    for n in names:
        done = []
        if not on_open_connect(cfgs[n]):
            cfg = cfgs[n]
            cfg["model"] = dict(cfgs[donor]["model"])
            cfg["fallback_providers"] = list(cfgs[donor].get("fallback_providers") or [])
            put_config(d, cfg, n)
            done.append("routing -> open-connect")
        for k in OPEN_CONNECT_KEYS:
            if keys[n].get(k):
                continue
            time.sleep(6.5)  # /api/env/reveal allows 5 calls per 30 s
            status, body = d.call("POST", "/api/env/reveal", {"key": k, "profile": donor})
            value = body.get("value") if isinstance(body, dict) else None
            if status >= 400 or not value:
                print(f"::warning::{n}: could not read {k} from {donor} (HTTP {status})")
                continue
            status, _ = d.call("PUT", "/api/env", {"key": k, "value": value, "profile": n})
            value = None
            done.append(f"{k} set" if status < 400 else f"{k} FAILED (HTTP {status})")
        if done:
            print(f"  {n}: {', '.join(done)}")
    print("profiles checked:", len(names))


def restart_gateway(d: Dashboard) -> None:
    status, _ = d.call("POST", "/api/gateway/restart", {})
    print(f"gateway restart requested (HTTP {status})")


STATE_KEYS = ("enabled", "available", "configured", "is_configured", "installed", "connected",
              "status", "state", "error", "reason", "missing_env", "requires_env")


def rows(body: object, *keys: str) -> list:
    """First list found in the response (top level or under a known key)."""
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for k in keys:
            if isinstance(body.get(k), list):
                return body[k]
            if isinstance(body.get(k), dict):
                return [dict(v, name=n) if isinstance(v, dict) else {"name": n, "value": v} for n, v in body[k].items()]
    return []


def brief(row: object) -> str:
    if not isinstance(row, dict):
        return str(row)[:80]
    name = row.get("name") or row.get("id") or row.get("key") or "?"
    bits = []
    for k in STATE_KEYS:
        if k in row and row[k] not in (None, "", [], {}):
            v = row[k]
            v = ",".join(map(str, v)) if isinstance(v, list) else str(v)
            bits.append(f"{k}={v[:80]}")
    return f"{name} " + " ".join(bits)


def inventory(d: Dashboard) -> None:
    cfg = config(d)
    plugins = (cfg.get("plugins") or {}).get("enabled") if isinstance(cfg.get("plugins"), dict) else cfg.get("plugins")
    print(f"== plugins enabled: {plugins}")
    for title, path, keys in (("toolsets", "/api/tools/toolsets", ("toolsets", "items")),
                              ("mcp servers", "/api/mcp/servers", ("servers", "items")),
                              ("skills", "/api/skills", ("skills", "items"))):
        items = rows(d.get(path), *keys)
        print(f"== {title}: {len(items)}")
        if title == "skills":
            off = [r for r in items if isinstance(r, dict) and r.get("enabled") is False]
            print(f"  disabled: {len(off)} -> {[r.get('name') for r in off][:60]}")
            continue
        for r in items:
            print("  " + brief(r))


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "diagnose"
    d = login()
    if action == "diagnose":
        diagnose(d)
    elif action == "inventory":
        inventory(d)
    elif action == "fix":
        fix_default(d)
        fix_profiles(d)
        restart_gateway(d)
    else:
        die(f"unknown action {action}")


if __name__ == "__main__":
    main()
