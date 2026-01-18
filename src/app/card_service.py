from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import logging
from jinja2 import TemplateNotFound

from src.app.config import Config
from src.app.renderers.jinja_html_renderer import JinjaHtmlRenderer
from src.app.renderers.jinja_json_renderer import JinjaJsonRenderer
from src.app.renderers.jinja_template_loader import JinjaTemplateLoader
from src.app.renderers.jinja_text_renderer import JinjaTextRenderer
from src.app.renderers.types import Renderer
from src.domain.types import QueryResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CardArtifact:
    template: str
    payload_key: str
    format: str  # "png" | "html" | "txt" | "json"
    path: Path
    mime: str | None = None

    def exists(self) -> bool:
        return self.path.exists()

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.path.read_text(encoding=encoding)


class CardService:
    """
    需求对齐版：

    1) PNG 必须由 HTML 渲染而来；缺 html 模板 => png 必须报错。
    2) 产物统一落盘：png/html/txt/json 都是磁盘缓存产物。
    3) 模板不一定同时具备所有格式：
       - 只有当用户请求某个格式时，才要求对应模板存在；
       - 未请求的格式，即使模板缺失，也绝不报错、绝不尝试加载。
    4) 未知 format 直接报错。
    """

    def __init__(self, cfg: Config):
        templates_root = cfg.ProjectRoot / "data" / "templates"
        loader = JinjaTemplateLoader(str(templates_root))

        self.text_renderer: Renderer = JinjaTextRenderer(loader)
        self.json_renderer: Renderer = JinjaJsonRenderer(loader)
        self.html_renderer: Renderer = JinjaHtmlRenderer(loader)

        self.cache_root: Path = cfg.ResourcePath / "cache" / "cards"
        self.cache_root.mkdir(parents=True, exist_ok=True)

        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def get(
        self,
        *,
        template: str,
        payload_key: str,
        payload: object,
        params: dict | None = None,
        format: str = "png",
    ) -> CardArtifact:
        """
        返回指定 format 的单个产物（如果磁盘已有则直接返回，否则渲染并落盘）。
        """
        fmt = format.lower().strip().lstrip(".")
        allowed = ("png", "html", "txt", "json")
        if fmt not in allowed:
            raise ValueError(f"Unsupported format: {format}._toggle must be one of {allowed}")

        params = params or {}

        out_dir = self.cache_root / template / payload_key
        out_path = out_dir / f"artifact.{fmt}"

        # 快速命中
        if out_path.exists():
            try:
                if out_path.stat().st_size > 0:
                    return CardArtifact(template, payload_key, fmt, out_path)
            except FileNotFoundError:
                pass

        # 同 key 并发只做一次
        lock_key = f"{template}:{payload_key}:{fmt}"
        lock = await self._get_lock(lock_key)

        async with lock:
            # double-check
            if out_path.exists():
                try:
                    if out_path.stat().st_size > 0:
                        return CardArtifact(template, payload_key, fmt, out_path)
                except FileNotFoundError:
                    pass

            out_dir.mkdir(parents=True, exist_ok=True)
            qr = self._ensure_query_result(payload)

            if fmt == "html":
                ro = self.html_renderer.render(template, qr)  # 缺模板 => TemplateNotFound（请求才要求存在）
                await self._atomic_write_text(out_path, ro.payload, encoding="utf-8")
                return CardArtifact(template, payload_key, fmt, out_path, mime=ro.mime)

            elif fmt == "txt":
                ro = self.text_renderer.render(template, qr)  # 缺模板 => TemplateNotFound
                await self._atomic_write_text(out_path, ro.payload, encoding="utf-8")
                return CardArtifact(template, payload_key, fmt, out_path, mime=ro.mime)

            elif fmt == "json":
                ro = self.json_renderer.render(template, qr)  # 缺模板 => TemplateNotFound
                await self._atomic_write_text(out_path, ro.payload, encoding="utf-8")
                return CardArtifact(template, payload_key, fmt, out_path, mime=ro.mime)

            elif fmt == "png":
                # 只在请求 png 时才加载 html / json(可选配置)
                html_ro = self.html_renderer.render(template, qr)  # 缺 html 模板 => 必须报错（需求 1）
                render_cfg = self._load_png_render_cfg_optional(template, qr)  # 缺 json 模板 => 静默 {}

                merged_cfg = dict(render_cfg)
                merged_cfg.update(params)

                await self._render_html_to_png(
                    html=html_ro.payload,
                    out_path=out_path,
                    cfg=merged_cfg,
                )
                return CardArtifact(template, payload_key, fmt, out_path, mime="image/png")

            # 理论上走不到，因为上面已经校验过 allowed
            raise ValueError(f"Unsupported format: {format}")

    async def get_many(
        self,
        *,
        template: str,
        payload_key: str,
        payload: object,
        params: dict | None = None,
        formats: list[str] | None = None,
    ) -> dict[str, CardArtifact]:
        """
        一次请求多个格式，逐个生成并落盘。
        - 请求到的格式缺模板会报错（符合“请求才要求存在”）
        - png 仍然强依赖 html
        - 未知格式会直接报错
        """
        formats = formats or ["png", "html"]
        out: dict[str, CardArtifact] = {}
        for f in formats:
            out[f] = await self.get(
                template=template,
                payload_key=payload_key,
                payload=payload,
                params=params,
                format=f,
            )
        return out

    # ----------------- internals -----------------

    async def _get_lock(self, key: str) -> asyncio.Lock:
        async with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock

    def _ensure_query_result(self, payload: object) -> QueryResult:
        if isinstance(payload, QueryResult):
            return payload
        if isinstance(payload, dict):
            return QueryResult(data=payload)
        return QueryResult(data={"payload": payload})

    def _load_png_render_cfg_optional(self, template: str, qr: QueryResult) -> dict[str, Any]:
        """
        png 渲染配置来源：尝试用 json 模板渲染出配置 dict。
        - json 模板缺失：静默返回 {}
        - json 不是 dict 或解析失败：静默返回 {}
        只有在请求 png 时才会调用（满足需求 3）。
        """
        try:
            ro = self.json_renderer.render(template, qr)
        except TemplateNotFound:
            return {}

        text = (ro.payload or "").strip()
        if not text:
            return {}

        try:
            cfg = json.loads(text)
            return cfg if isinstance(cfg, dict) else {}
        except Exception as e:
            logger.debug("png render cfg parse failed: template=%s err=%s", template, e)
            return {}

    async def _atomic_write_text(self, path: Path, content: str, *, encoding: str = "utf-8") -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding=encoding)
        os.replace(tmp, path)

    async def _atomic_write_bytes(self, path: Path, content: bytes) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(content)
        os.replace(tmp, path)

    async def _render_html_to_png(self, *, html: str, out_path: Path, cfg: dict[str, Any]) -> None:
        """
        Playwright 渲染 HTML 为 PNG

        cfg 常用字段（都可选）：
        - viewport: {"width": 900, "height": 520, "deviceScaleFactor": 2}
        - full_page: true/false
        - wait_until: "load" | "domcontentloaded" | "networkidle"
        - extra_wait_ms: 0..n
        - transparent: true/false
        """
        viewport = cfg.get("viewport") or {"width": 900, "height": 520}
        full_page = bool(cfg.get("full_page", False))
        wait_until = cfg.get("wait_until", "networkidle")
        extra_wait_ms = int(cfg.get("extra_wait_ms", 0))
        transparent = bool(cfg.get("transparent", False))

        try:
            from playwright.async_api import async_playwright
        except Exception as e:
            raise RuntimeError(
                "Playwright 不可用，无法渲染 png。请安装 playwright 并执行 playwright install。"
            ) from e

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            try:
                page = await browser.new_page(viewport=viewport)
                await page.set_content(html, wait_until=wait_until)

                if extra_wait_ms > 0:
                    await page.wait_for_timeout(extra_wait_ms)

                png_bytes = await page.screenshot(
                    full_page=full_page,
                    type="png",
                    omit_background=transparent,
                )
                await self._atomic_write_bytes(out_path, png_bytes)
            finally:
                await browser.close()
