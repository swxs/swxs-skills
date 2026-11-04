"""
TAPD API 客户端（仅使用 Python 标准库）。

环境变量（均以 SWXSSKILL_TAPD_ 开头）：
    SWXSSKILL_TAPD_ACCESS_TOKEN          个人访问令牌（推荐）
    SWXSSKILL_TAPD_API_USER              API 账号（与 PASSWORD 搭配）
    SWXSSKILL_TAPD_API_PASSWORD          API 密码
    SWXSSKILL_TAPD_API_BASE_URL          可选，默认 https://api.tapd.cn
    SWXSSKILL_TAPD_CURRENT_USER_NICK     可选，projects 子命令的默认 nick

本机系统代理指向无人监听的 localhost，所有请求经 ProxyHandler({}) 直连。

命令行：
    python tapd_client_stdlib.py projects [--nick NICK]
    python tapd_client_stdlib.py workspace --workspace-id ID
    python tapd_client_stdlib.py stories --workspace-id ID [--entity-type stories|tasks]
    python tapd_client_stdlib.py bugs --workspace-id ID
    python tapd_client_stdlib.py iterations --workspace-id ID
    python tapd_client_stdlib.py releases --workspace-id ID
    python tapd_client_stdlib.py get --endpoint "stories/count" -p workspace_id=123
    python tapd_client_stdlib.py post --endpoint "stories" -b '{"workspace_id":123,"name":"需求标题"}'
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from typing import Any, Optional


DEFAULT_TAPD_API_BASE_URL = "https://api.tapd.cn"


def _env(suffix: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(f"SWXSSKILL_TAPD_{suffix}", default)


def _get_base_url() -> str:
    base = _env("API_BASE_URL", DEFAULT_TAPD_API_BASE_URL) or DEFAULT_TAPD_API_BASE_URL
    return base.rstrip("/")


def _get_headers() -> dict:
    token = (_env("ACCESS_TOKEN") or "").strip()
    if token:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Via": "mcp",
        }
    user = (_env("API_USER") or "").strip()
    password = _env("API_PASSWORD") or ""
    if not user or not password:
        raise ValueError(
            "请设置 SWXSSKILL_TAPD_ACCESS_TOKEN，"
            "或 SWXSSKILL_TAPD_API_USER + SWXSSKILL_TAPD_API_PASSWORD"
        )
    auth = b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Via": "mcp",
    }


def _is_cloud() -> bool:
    base = _env("API_BASE_URL", DEFAULT_TAPD_API_BASE_URL) or DEFAULT_TAPD_API_BASE_URL
    return "api.tapd.cn" in base


def to_long_id(short_id: str, workspace_id: int) -> str:
    """将短 ID（≤9 位数字）转为 TAPD 长 ID。"""
    s = str(short_id).strip()
    if not s.isdigit() or len(s) > 9:
        return s
    prefix = "11" if _is_cloud() else "10"
    return f"{prefix}{workspace_id}{s.zfill(9)}"


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    data: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """发送 TAPD API 请求。URL 自动追加 s=mcp。HTTP 错误时返回带 http_status 的 JSON。"""
    base = _get_base_url()
    url = f"{base}/{endpoint.lstrip('/')}"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}s=mcp"

    if params:
        encoded = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}&{encoded}"

    headers = _get_headers()
    req_body = None
    if method.upper() == "POST" and data is not None:
        req_body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=req_body, headers=headers, method=method.upper())
    try:
        with _opener().open(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"status": 0, "info": raw}
        if isinstance(body, dict):
            body.setdefault("http_status", e.code)
            return body
        return {"status": 0, "info": body, "http_status": e.code}
    except urllib.error.URLError as e:
        return {"status": 0, "info": str(e.reason), "http_status": 0}


def get_stories(workspace_id: int, options: Optional[dict] = None) -> dict:
    """获取需求或任务列表。entity_type 在 options 中指定为 stories 或 tasks。"""
    opts = options or {}
    entity_type = opts.get("entity_type", "stories")
    endpoint = "stories" if entity_type == "stories" else "tasks"
    params = {"workspace_id": workspace_id, "page": 1, "limit": 10}
    params.update(opts)
    return request("GET", endpoint, params=params)


def get_workspace_info(workspace_id: int) -> dict:
    """根据项目 ID 获取项目信息。"""
    return request("GET", f"workspaces/get_workspace_info?workspace_id={workspace_id}")


def get_user_participant_projects(nick: str) -> dict:
    """获取用户参与的项目列表。"""
    return request("GET", "workspaces/user_participant_projects", params={"nick": nick})


def get_bugs(workspace_id: int, options: Optional[dict] = None) -> dict:
    """获取缺陷列表。"""
    params = {"workspace_id": workspace_id, "page": 1, "limit": 10}
    if options:
        params.update(options)
    return request("GET", "bugs", params=params)


def get_iterations(workspace_id: int, options: Optional[dict] = None) -> dict:
    """获取迭代列表。"""
    params = {"workspace_id": workspace_id}
    if options:
        params.update(options)
    return request("GET", "iterations", params=params)


def get_releases(workspace_id: int, options: Optional[dict] = None) -> dict:
    """获取发布计划列表。"""
    params = {"workspace_id": workspace_id}
    if options:
        params.update(options)
    return request("GET", "releases", params=params)


def _failed(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("http_status"):
        return True
    return payload.get("status") in (0, "0")


def _cli():
    parser = argparse.ArgumentParser(
        description="TAPD API 命令行客户端（仅标准库）。需设置 SWXSSKILL_TAPD_ACCESS_TOKEN，或 SWXSSKILL_TAPD_API_USER + SWXSSKILL_TAPD_API_PASSWORD。"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_projects = sub.add_parser("projects", help="获取用户参与的项目列表")
    p_projects.add_argument(
        "--nick",
        default=_env("CURRENT_USER_NICK", "") or "",
        help="用户昵称，默认 SWXSSKILL_TAPD_CURRENT_USER_NICK",
    )

    p_ws = sub.add_parser("workspace", help="获取项目信息")
    p_ws.add_argument("--workspace-id", type=int, required=True, dest="workspace_id")

    p_stories = sub.add_parser("stories", help="获取需求或任务列表")
    p_stories.add_argument("--workspace-id", type=int, required=True, dest="workspace_id")
    p_stories.add_argument("--entity-type", choices=("stories", "tasks"), default="stories", dest="entity_type")
    p_stories.add_argument("--limit", type=int, default=10)
    p_stories.add_argument("--page", type=int, default=1)
    p_stories.add_argument("--id", dest="id_", metavar="ID")
    p_stories.add_argument("--name")
    p_stories.add_argument("--status")
    p_stories.add_argument("--fields")

    p_bugs = sub.add_parser("bugs", help="获取缺陷列表")
    p_bugs.add_argument("--workspace-id", type=int, required=True, dest="workspace_id")
    p_bugs.add_argument("--limit", type=int, default=10)
    p_bugs.add_argument("--page", type=int, default=1)
    p_bugs.add_argument("--id", dest="id_", metavar="ID")
    p_bugs.add_argument("--title")

    p_iter = sub.add_parser("iterations", help="获取迭代列表")
    p_iter.add_argument("--workspace-id", type=int, required=True, dest="workspace_id")
    p_iter.add_argument("--limit", type=int, default=30)
    p_iter.add_argument("--page", type=int, default=1)
    p_iter.add_argument("--name")

    p_rel = sub.add_parser("releases", help="获取发布计划列表")
    p_rel.add_argument("--workspace-id", type=int, required=True, dest="workspace_id")
    p_rel.add_argument("--limit", type=int, default=30)
    p_rel.add_argument("--page", type=int, default=1)

    p_get = sub.add_parser("get", help="通用 GET")
    p_get.add_argument("--endpoint", required=True)
    p_get.add_argument("-p", "--param", dest="params", action="append", default=[], metavar="KEY=VAL")

    p_post = sub.add_parser("post", help="通用 POST")
    p_post.add_argument("--endpoint", required=True)
    p_post.add_argument("-b", "--body")
    p_post.add_argument("-p", "--param", dest="params", action="append", default=[], metavar="KEY=VAL")

    args = parser.parse_args()
    out = None

    if args.command == "projects":
        nick = (args.nick or "").strip()
        if not nick:
            print(
                json.dumps({"error": "请提供 --nick 或设置 SWXSSKILL_TAPD_CURRENT_USER_NICK"}, ensure_ascii=False),
                file=sys.stderr,
            )
            raise SystemExit(1)
        out = get_user_participant_projects(nick)
    elif args.command == "workspace":
        out = get_workspace_info(args.workspace_id)
    elif args.command == "stories":
        opts: dict[str, Any] = {"entity_type": args.entity_type, "limit": args.limit, "page": args.page}
        if getattr(args, "id_", None):
            opts["id"] = args.id_
        if getattr(args, "name", None):
            opts["name"] = args.name
        if getattr(args, "status", None):
            opts["status"] = args.status
        if getattr(args, "fields", None):
            opts["fields"] = args.fields
        out = get_stories(args.workspace_id, opts)
    elif args.command == "bugs":
        opts = {"limit": args.limit, "page": args.page}
        if getattr(args, "id_", None):
            opts["id"] = args.id_
        if getattr(args, "title", None):
            opts["title"] = args.title
        out = get_bugs(args.workspace_id, opts)
    elif args.command == "iterations":
        opts = {"limit": args.limit, "page": args.page}
        if getattr(args, "name", None):
            opts["name"] = args.name
        out = get_iterations(args.workspace_id, opts)
    elif args.command == "releases":
        out = get_releases(args.workspace_id, {"limit": args.limit, "page": args.page})
    elif args.command == "get":
        params = {}
        for s in args.params:
            if "=" in s:
                k, v = s.split("=", 1)
                params[k.strip()] = v.strip()
        out = request("GET", args.endpoint, params=params if params else None)
    elif args.command == "post":
        if args.body:
            try:
                data = json.loads(args.body)
            except json.JSONDecodeError as e:
                print(json.dumps({"error": f"无效 JSON: {e}"}, ensure_ascii=False), file=sys.stderr)
                raise SystemExit(1)
        else:
            data = {}
            for s in args.params:
                if "=" in s:
                    k, v = s.split("=", 1)
                    data[k.strip()] = v.strip()
        out = request("POST", args.endpoint, data=data if data else None)

    if out is not None:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if _failed(out):
            raise SystemExit(1)


if __name__ == "__main__":
    _cli()
