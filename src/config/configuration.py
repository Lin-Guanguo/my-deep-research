"""Runtime configuration models and loading helpers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


@dataclass
class RuntimeConfig:
    """Parameters that govern the orchestration loop."""

    locale: str = "zh-CN"
    max_iterations: int = 6
    human_review: bool = True


@dataclass
class ModelConfig:
    """LLM model choices and sampling parameters (served via OpenRouter)."""

    planner: str = "gpt-4o-mini"
    researcher: str = "gpt-4o-mini"
    reporter: str = "gpt-4o-mini"
    temperature: float = 0.0


@dataclass
class SearchConfig:
    """Tavily search quota settings."""

    max_queries: int = 3
    timeout_seconds: float = 8.0


@dataclass
class ApiConfig:
    """API credentials for OpenRouter and Tavily."""

    openrouter_key: str | None = None
    tavily_key: str | None = None


@dataclass
class ObservabilityConfig:
    """LangSmith or other tracing configuration."""

    langsmith_project: str | None = None
    langsmith_api_key: str | None = None


@dataclass
class AppConfig:
    """Full application configuration bundle."""

    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)


def load_config(
    settings_path: str | Path = "config/settings.yaml",
    secret_path: str | Path = "secret",
) -> AppConfig:
    """Load configuration from settings YAML and the optional secret file.

    `settings.yaml` carries defaults, while the plain-text `secret` file
    (KEY=VALUE per line) overrides sensitive values without touching VCS.
    """

    settings_data = _load_settings_yaml(Path(settings_path))
    secrets_data = _load_secret_file(Path(secret_path))

    runtime_cfg = RuntimeConfig(**_get_section(settings_data, "runtime"))
    model_cfg = ModelConfig(**_get_section(settings_data, "models"))
    search_cfg = SearchConfig(**_get_section(settings_data, "search"))
    api_cfg = ApiConfig(**_get_section(settings_data, "api"))

    observability_raw = _get_section(settings_data, "observability")

    api_cfg, observability_cfg = _merge_with_secrets(api_cfg, observability_raw, secrets_data)

    return AppConfig(
        runtime=runtime_cfg,
        models=model_cfg,
        search=search_cfg,
        api=api_cfg,
        observability=observability_cfg,
    )


def _load_settings_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning("Config file not found; using defaults", extra={"path": str(path)})
        return {}

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
        if not isinstance(data, dict):
            raise ValueError("settings.yaml must contain a mapping at top level")
        return data


def _load_secret_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}

    secrets: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                logger.warning("Skipping malformed secret line", extra={"line": line})
                continue
            key, value = line.split("=", 1)
            secrets[key.strip()] = value.strip()
    return secrets


def _merge_with_secrets(
    api_cfg: ApiConfig,
    observability_raw: Dict[str, Any],
    secrets: Dict[str, str],
) -> tuple[ApiConfig, ObservabilityConfig]:
    merged_api = ApiConfig(**asdict(api_cfg))
    merged_observability = ObservabilityConfig(**observability_raw)

    for raw_key, raw_value in secrets.items():
        normalized = raw_key.strip().lower()
        value = raw_value.strip()

        if normalized.startswith("langsmith"):
            if normalized.endswith("project"):
                merged_observability.langsmith_project = value
            else:
                merged_observability.langsmith_api_key = value
            continue

        if "openrouter" in normalized or "open_router" in normalized:
            merged_api.openrouter_key = value
            continue
        if "tavily" in normalized:
            merged_api.tavily_key = value
            continue

    return merged_api, merged_observability


def _get_section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    section = data.get(key, {})
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError(f"{key} section must be a mapping")
    return section
