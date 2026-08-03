#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_ROOT = "https://api.cloudflare.com/client/v4"


class EdgeConfigurationError(RuntimeError):
    pass


def _normal_domain(value: str, *, template: bool = False) -> str:
    raw = value.strip().lower()
    if raw.startswith("https://"):
        raw = raw[8:]
    elif raw.startswith("http://"):
        raw = raw[7:]
    raw = raw.rstrip("/")
    if template:
        raw = raw.rstrip("*").rstrip("/")
    return raw


def _safe_json_response(payload: Any) -> Any:
    if not isinstance(payload, dict) or payload.get("success") is not True:
        errors = payload.get("errors", []) if isinstance(payload, dict) else []
        codes = [str(row.get("code", "unknown")) for row in errors if isinstance(row, dict)]
        raise EdgeConfigurationError("Cloudflare API 失败，错误代码=" + ",".join(codes[:5]))
    return payload.get("result")


class CloudflareClient:
    def __init__(self, token: str, *, opener: Any = None) -> None:
        self.token = token.strip()
        if not self.token or len(self.token) > 4096:
            raise EdgeConfigurationError("Cloudflare API Token 缺失或长度异常")
        self.opener = opener or urllib.request.urlopen

    def request(self, method: str, path: str, *, query: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> Any:
        url = API_ROOT + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener(request, timeout=20) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.load(exc)
                _safe_json_response(payload)
            except Exception:
                pass
            raise EdgeConfigurationError(f"Cloudflare API HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise EdgeConfigurationError("Cloudflare API 不可达或响应无效") from exc
        return _safe_json_response(payload)

    def list_all(self, path: str, *, query: dict[str, str] | None = None) -> list[dict[str, Any]]:
        values: list[dict[str, Any]] = []
        base = dict(query or {})
        for page in range(1, 51):
            result = self.request("GET", path, query={**base, "page": str(page), "per_page": "100"})
            if not isinstance(result, list):
                raise EdgeConfigurationError("Cloudflare list API 未返回数组")
            values.extend(row for row in result if isinstance(row, dict))
            if len(result) < 100:
                return values
        raise EdgeConfigurationError("Cloudflare list API 分页超过安全上限")


def find_unique_app(apps: list[dict[str, Any]], domain: str, *, template: bool = False) -> dict[str, Any]:
    expected = _normal_domain(domain, template=template)
    matches = []
    for app in apps:
        observed = _normal_domain(str(app.get("domain", "")), template=template)
        if observed == expected:
            matches.append(app)
    if len(matches) != 1:
        raise EdgeConfigurationError(f"Access application 必须唯一匹配 {domain}，实际={len(matches)}")
    return matches[0]


def _contains_everyone(value: Any) -> bool:
    if isinstance(value, dict):
        if "everyone" in value:
            return True
        return any(_contains_everyone(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_everyone(item) for item in value)
    return False


def safe_policy_body(policy: dict[str, Any], *, target_name: str) -> dict[str, Any]:
    decision = str(policy.get("decision", "")).lower()
    if decision == "bypass":
        raise EdgeConfigurationError("禁止复制 Access bypass policy")
    if decision not in {"allow", "deny", "non_identity"}:
        raise EdgeConfigurationError(f"不支持的 Access policy decision: {decision or 'missing'}")
    if decision in {"allow", "non_identity"} and _contains_everyone(policy.get("include", [])):
        raise EdgeConfigurationError("禁止复制公开 Everyone Access policy")
    include = policy.get("include")
    if decision in {"allow", "non_identity"} and (not isinstance(include, list) or not include):
        raise EdgeConfigurationError("Allow policy 必须包含明确身份规则")
    allowed = (
        "decision", "include", "exclude", "require", "precedence", "session_duration",
        "approval_required", "approval_groups", "purpose_justification_required",
        "purpose_justification_prompt", "isolation_required", "mfa_config",
    )
    body = {key: policy[key] for key in allowed if key in policy}
    body["name"] = f"{target_name} · {str(policy.get('name', 'owner policy'))}"[:350]
    return body


def safe_application_body(template: dict[str, Any], *, target_domain: str, target_name: str) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": target_name,
        "type": "self_hosted",
        "domain": _normal_domain(target_domain),
        "session_duration": str(template.get("session_duration") or "24h"),
        "app_launcher_visible": False,
    }
    for key in (
        "allowed_idps", "auto_redirect_to_identity", "enable_binding_cookie",
        "http_only_cookie_attribute", "same_site_cookie_attribute", "skip_interstitial",
        "options_preflight_bypass",
    ):
        if key in template:
            body[key] = template[key]
    return body


def _token(path: Path) -> str:
    if not path.is_file():
        raise EdgeConfigurationError(f"Token 文件不存在: {path}")
    return path.read_text(encoding="utf-8").strip()


def _write_env_values(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    remaining = dict(updates)
    output: list[str] = []
    for raw in lines:
        if "=" in raw and not raw.lstrip().startswith("#"):
            key = raw.split("=", 1)[0].strip()
            if key in remaining:
                output.append(f"{key}={remaining.pop(key)}")
                continue
        output.append(raw)
    if remaining:
        if output and output[-1].strip():
            output.append("")
        output.append("# Memory Atlas Cloudflare Access binding; generated without storing API Token.")
        output.extend(f"{key}={value}" for key, value in remaining.items())
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR)
    temporary.replace(path)


def _exact_zone(client: CloudflareClient, zone_name: str) -> tuple[str, str]:
    zones = client.list_all("/zones", query={"name": zone_name, "status": "active"})
    matches = [row for row in zones if str(row.get("name", "")).lower() == zone_name.lower()]
    if len(matches) != 1:
        raise EdgeConfigurationError(f"必须唯一解析 Cloudflare zone {zone_name}")
    zone = matches[0]
    account = zone.get("account") if isinstance(zone.get("account"), dict) else {}
    zone_id, account_id = str(zone.get("id", "")), str(account.get("id", ""))
    if not zone_id or not account_id:
        raise EdgeConfigurationError("Cloudflare zone 缺少 zone_id/account_id")
    return zone_id, account_id


def _exact_dns_record(client: CloudflareClient, zone_id: str, domain: str, *, required: bool) -> dict[str, Any] | None:
    rows = client.list_all(f"/zones/{zone_id}/dns_records", query={"name": domain})
    matches = [row for row in rows if str(row.get("name", "")).lower() == domain.lower()]
    if len(matches) > 1 or (required and len(matches) != 1):
        raise EdgeConfigurationError(f"DNS record {domain} 必须唯一，实际={len(matches)}")
    return matches[0] if matches else None


def configure(args: argparse.Namespace) -> dict[str, Any]:
    access = CloudflareClient(_token(args.access_token_file))
    dns = CloudflareClient(_token(args.dns_token_file))
    zone_id, account_id = _exact_zone(dns, args.zone_name)
    dns_source = _exact_dns_record(dns, zone_id, args.dns_template_domain, required=True)
    assert dns_source is not None
    if str(dns_source.get("type")) not in {"A", "AAAA", "CNAME"} or dns_source.get("proxied") is not True:
        raise EdgeConfigurationError("DNS 模板必须是已代理的 A/AAAA/CNAME")
    dns_target = _exact_dns_record(dns, zone_id, args.target_domain, required=False)
    if dns_target is not None:
        for key in ("type", "content", "proxied"):
            if dns_target.get(key) != dns_source.get(key):
                raise EdgeConfigurationError(f"目标 DNS 与模板冲突: {key}")

    apps = access.list_all(f"/accounts/{account_id}/access/apps")
    target_matches = [app for app in apps if _normal_domain(str(app.get("domain", ""))) == _normal_domain(args.target_domain)]
    created_app = False
    app: dict[str, Any]
    try:
        if target_matches:
            if len(target_matches) != 1:
                raise EdgeConfigurationError("目标 Access application 不唯一")
            app = target_matches[0]
        else:
            if not args.allow_create:
                raise EdgeConfigurationError("目标 Access application 不存在；未授权创建")
            template = find_unique_app(apps, args.access_template_domain, template=True)
            template_id = str(template.get("id", ""))
            if not template_id:
                raise EdgeConfigurationError("Access 模板缺少 app id")
            policies = access.list_all(f"/accounts/{account_id}/access/apps/{template_id}/policies")
            safe_policies = [safe_policy_body(row, target_name=args.target_name) for row in policies]
            if not safe_policies or not any(row.get("decision") in {"allow", "non_identity"} for row in safe_policies):
                raise EdgeConfigurationError("Access 模板没有安全 Allow policy")
            result = access.request("POST", f"/accounts/{account_id}/access/apps", body=safe_application_body(template, target_domain=args.target_domain, target_name=args.target_name))
            if not isinstance(result, dict) or not result.get("id"):
                raise EdgeConfigurationError("Access application 创建回执无效")
            app = result
            created_app = True
            app_id = str(app["id"])
            for policy in safe_policies:
                access.request("POST", f"/accounts/{account_id}/access/apps/{app_id}/policies", body=policy)

        app_id = str(app.get("id", ""))
        app_aud = str(app.get("aud", ""))
        if not app_id or not app_aud:
            # Re-read because create responses can omit computed AUD.
            current = find_unique_app(access.list_all(f"/accounts/{account_id}/access/apps"), args.target_domain)
            app_id, app_aud = str(current.get("id", "")), str(current.get("aud", ""))
        if not app_id or not app_aud:
            raise EdgeConfigurationError("Access application 缺少 id/aud")
        target_policies = access.list_all(f"/accounts/{account_id}/access/apps/{app_id}/policies")
        checked = [safe_policy_body(row, target_name=args.target_name) for row in target_policies]
        if not checked or not any(row.get("decision") in {"allow", "non_identity"} for row in checked):
            raise EdgeConfigurationError("目标 Access application 没有安全 Allow policy")

        organization = access.request("GET", f"/accounts/{account_id}/access/organizations")
        if not isinstance(organization, dict):
            raise EdgeConfigurationError("Zero Trust organization 回执无效")
        auth_domain = str(organization.get("auth_domain", "")).strip()
        if not auth_domain:
            raise EdgeConfigurationError("Zero Trust organization 缺少 auth_domain")

        created_dns = False
        if dns_target is None:
            if not args.allow_create:
                raise EdgeConfigurationError("目标 DNS 不存在；未授权创建")
            body = {
                "type": dns_source["type"], "name": args.target_domain,
                "content": dns_source["content"], "proxied": True, "ttl": 1,
                "comment": "Memory Atlas private owner entry; managed by frozen Taskpack",
            }
            result = dns.request("POST", f"/zones/{zone_id}/dns_records", body=body)
            if not isinstance(result, dict) or not result.get("id"):
                raise EdgeConfigurationError("DNS 创建回执无效")
            created_dns = True

        _write_env_values(args.env_file, {
            "MEMORY_ATLAS_EXTERNAL_ORIGIN": f"https://{_normal_domain(args.target_domain)}",
            "MEMORY_ATLAS_CF_ACCESS_TEAM_DOMAIN": f"https://{auth_domain.rstrip('/')}",
            "MEMORY_ATLAS_CF_ACCESS_AUD": app_aud,
            "MEMORY_ATLAS_CF_ACCESS_APP_ID": app_id,
        })
        return {
            "schema_version": "memory_atlas.cloudflare_edge_binding.v1",
            "state": "PASS",
            "target_domain": _normal_domain(args.target_domain),
            "zone_id_suffix": zone_id[-6:],
            "account_id_suffix": account_id[-6:],
            "access_app_id": app_id,
            "access_aud_sha256_prefix": __import__("hashlib").sha256(app_aud.encode()).hexdigest()[:12],
            "access_policy_count": len(checked),
            "access_policy_decisions": sorted({str(row.get("decision")) for row in checked}),
            "access_app_created": created_app,
            "dns_created": created_dns,
            "env_file": str(args.env_file),
            "env_mode": "0600",
            "token_values_persisted": False,
        }
    except Exception:
        if created_app and isinstance(locals().get("app"), dict) and app.get("id"):
            try:
                access.request("DELETE", f"/accounts/{account_id}/access/apps/{app['id']}")
            except Exception:
                pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Idempotently bind Memory Atlas to an existing owner-only Cloudflare Access/DNS pattern")
    parser.add_argument("--access-token-file", type=Path, required=True)
    parser.add_argument("--dns-token-file", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--zone-name", default="linzezhang.com")
    parser.add_argument("--target-domain", default="memoryatlas.linzezhang.com")
    parser.add_argument("--target-name", default="Memory Atlas Owner Private")
    parser.add_argument("--access-template-domain", default="status.linzezhang.com/admin")
    parser.add_argument("--dns-template-domain", default="status.linzezhang.com")
    parser.add_argument("--allow-create", action="store_true")
    args = parser.parse_args()
    try:
        result = configure(args)
    except EdgeConfigurationError as exc:
        print(json.dumps({"state": "BLOCKED", "message_zh": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
