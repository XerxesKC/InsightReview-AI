from __future__ import annotations

import json
import os
import shutil
import subprocess
import time

from redis import Redis

from app.core.config import get_settings

BOOTSTRAP_ENV_KEY = "REVIEWPULSE_REDIS_BOOTSTRAP_STATUS"


def bootstrap_redis_for_local_run() -> dict[str, object]:
    """Best-effort Redis bootstrap for `python main.py` local runs.

    行为目标：
    1. 如果 Redis 已可连接，直接返回成功状态；
    2. 如果 Redis 未启动且允许自动拉起，则尝试用 Docker Compose 启动 `redis` 服务；
    3. 无论 Docker/Redis 是否可用，都只返回状态，不抛异常，避免阻断开发联调。
    """

    settings = get_settings()
    status: dict[str, object] = {
        "redis_url": settings.redis_url,
        "docker_attempted": False,
        "docker_started": False,
        "docker_message": "未尝试通过 Docker 启动 Redis。",
        "redis_connected": False,
        "redis_message": "Redis 未连接。",
    }

    if _can_connect_redis(settings.redis_url):
        status["redis_connected"] = True
        status["redis_message"] = "Redis 连接成功，可直接使用（可能是手动启动，也可能已由其他服务托管）。"
        _persist_status(status)
        return status

    status["redis_message"] = "Redis 当前不可连接。"
    if not settings.redis_auto_start_on_main:
        status["docker_message"] = "已禁用 main.py 自动拉起 Redis。"
        _persist_status(status)
        return status

    status["docker_attempted"] = True
    compose_command = _resolve_compose_command()
    if compose_command is None:
        status["docker_message"] = "未检测到 docker compose / docker-compose，可继续使用手动启动的 Redis。"
        _persist_status(status)
        return status

    compose_file = settings.redis_compose_file
    command = compose_command + ["-f", compose_file, "up", "-d", settings.redis_docker_service_name]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        combined_output = "\n".join(
            part.strip()
            for part in (result.stdout or "", result.stderr or "")
            if part and part.strip()
        )
        if result.returncode == 0:
            status["docker_started"] = True
            status["docker_message"] = combined_output or "Docker 已执行 Redis 启动命令。"
        else:
            status["docker_message"] = combined_output or "Docker Redis 启动命令执行失败。"
    except Exception as exc:
        status["docker_message"] = f"调用 Docker 启动 Redis 失败：{exc}"
        _persist_status(status)
        return status

    deadline = time.time() + max(int(settings.redis_start_timeout_seconds), 1)
    while time.time() < deadline:
        if _can_connect_redis(settings.redis_url):
            status["redis_connected"] = True
            status["redis_message"] = "Redis 连接成功，已可用于会话上下文缓存。"
            break
        time.sleep(1)

    if not status["redis_connected"]:
        status["redis_message"] = "Redis 仍未连接成功；应用将继续运行，并回退到数据库持久化。"

    _persist_status(status)
    return status


def read_bootstrap_status() -> dict[str, object]:
    raw = os.environ.get(BOOTSTRAP_ENV_KEY, "")
    if not raw:
        return {
            "docker_attempted": False,
            "docker_started": False,
            "docker_message": "尚未记录 Redis 启动状态。",
            "redis_connected": False,
            "redis_message": "尚未记录 Redis 连接状态。",
        }
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "docker_attempted": False,
            "docker_started": False,
            "docker_message": "Redis 启动状态解析失败。",
            "redis_connected": False,
            "redis_message": "Redis 连接状态解析失败。",
        }
    return data if isinstance(data, dict) else {}


def format_bootstrap_messages(status: dict[str, object]) -> list[str]:
    return [
        f"[Redis][Docker] {'已启动/执行成功' if status.get('docker_started') else '未启动或启动失败'}：{status.get('docker_message')}",
        f"[Redis][Connect] {'连接成功' if status.get('redis_connected') else '连接失败'}：{status.get('redis_message')}",
    ]


def _persist_status(status: dict[str, object]) -> None:
    os.environ[BOOTSTRAP_ENV_KEY] = json.dumps(status, ensure_ascii=False)


def _resolve_compose_command() -> list[str] | None:
    docker_path = shutil.which("docker")
    if docker_path:
        try:
            result = subprocess.run(
                [docker_path, "compose", "version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return [docker_path, "compose"]
        except Exception:
            pass

    docker_compose_path = shutil.which("docker-compose")
    if docker_compose_path:
        return [docker_compose_path]
    return None


def _can_connect_redis(redis_url: str) -> bool:
    client: Redis | None = None
    try:
        socket_connect_timeout = 1
        socket_timeout = 1
        client = Redis.from_url(
            redis_url,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            decode_responses=True,
        )
        client.ping()
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


