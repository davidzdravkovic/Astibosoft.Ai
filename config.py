from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent / "Configuration"
DATABASE_CONFIG_PATH = CONFIG_DIR / "database.json"


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    database: str
    username: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


def _parse_connection_string(raw: str) -> DatabaseSettings:
    parts: dict[str, str] = {}
    for segment in raw.split(";"):
        segment = segment.strip()
        if not segment or "=" not in segment:
            continue
        key, value = segment.split("=", 1)
        parts[key.strip()] = value.strip()

    missing = [key for key in ("Host", "Database", "Username", "Password") if key not in parts]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"DefaultConnection is missing: {joined}")

    return DatabaseSettings(
        host=parts["Host"],
        port=int(parts.get("Port", "5432")),
        database=parts["Database"],
        username=parts["Username"],
        password=parts["Password"],
    )


def _load_from_env() -> DatabaseSettings | None:
    host = os.getenv("DB_HOST")
    if not host:
        return None

    required = {
        "DB_NAME": "database",
        "DB_USER": "username",
        "DB_PASSWORD": "password",
    }
    values: dict[str, str] = {"host": host}
    for env_key, label in required.items():
        value = os.getenv(env_key)
        if not value:
            raise ValueError(f"{env_key} is required when DB_HOST is set ({label})")
        values[label] = value

    return DatabaseSettings(
        host=values["host"],
        port=int(os.getenv("DB_PORT", "5432")),
        database=values["database"],
        username=values["username"],
        password=values["password"],
    )


def load_database_settings(path: Path = DATABASE_CONFIG_PATH) -> DatabaseSettings:
    from_env = _load_from_env()
    if from_env is not None:
        return from_env

    if not path.is_file():
        raise FileNotFoundError(
            f"Database config not found at {path}. "
            f"Copy Configuration/database.example.json to Configuration/database.json "
            f"and use the same values as Astibosoft.Api DefaultConnection, "
            f"or set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD."
        )

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    try:
        raw = data["ConnectionStrings"]["DefaultConnection"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "database.json must contain ConnectionStrings.DefaultConnection "
            "(same shape as Astibosoft.Api appsettings)."
        ) from exc

    return _parse_connection_string(raw)


settings = load_database_settings()
