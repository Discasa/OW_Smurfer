import json
import os
from copy import deepcopy
from pathlib import Path

from .theme import Mode


LOCAL_APPDATA = os.getenv("LOCALAPPDATA")
APPDATA_PATH = Path(LOCAL_APPDATA) / "OW_Smurfer" if LOCAL_APPDATA else Path.home() / ".owsmurfer"
CONFIG_FILE = APPDATA_PATH / "config.json"
DEFAULT_CONFIG = {"accounts": [], "hotkey": "ctrl+l", "mode": Mode.ENTER}
VALID_MODES = {Mode.ENTER, Mode.TAB}

APPDATA_PATH.mkdir(parents=True, exist_ok=True)


def default_config():
    return deepcopy(DEFAULT_CONFIG)


def normalize_account(raw_account):
    if not isinstance(raw_account, dict):
        return None

    email = raw_account.get("email", "")
    password = raw_account.get("password", "")
    battle_tag = raw_account.get("battle_tag", "")

    if not all(isinstance(value, str) for value in (email, password, battle_tag)):
        return None

    return {
        "email": email,
        "password": password,
        "battle_tag": battle_tag,
    }


def load_config():
    if not CONFIG_FILE.exists():
        return default_config()

    try:
        raw_config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_config()

    if not isinstance(raw_config, dict):
        return default_config()

    validated_config = default_config()
    validated_config["accounts"] = raw_config.get("accounts", DEFAULT_CONFIG["accounts"])
    validated_config["hotkey"] = raw_config.get("hotkey", DEFAULT_CONFIG["hotkey"])
    validated_config["mode"] = raw_config.get("mode", DEFAULT_CONFIG["mode"])

    if not isinstance(validated_config["accounts"], list):
        validated_config["accounts"] = []
    validated_config["accounts"] = [
        normalized_account
        for account in validated_config["accounts"]
        for normalized_account in [normalize_account(account)]
        if normalized_account is not None
    ]

    if not isinstance(validated_config["hotkey"], str) or not validated_config["hotkey"].strip():
        validated_config["hotkey"] = DEFAULT_CONFIG["hotkey"]
    if validated_config["mode"] not in VALID_MODES:
        validated_config["mode"] = DEFAULT_CONFIG["mode"]

    return validated_config


def save_config(config_data):
    CONFIG_FILE.write_text(json.dumps(config_data, indent=4), encoding="utf-8")
