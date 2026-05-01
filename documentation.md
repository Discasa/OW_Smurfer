# OW Smurfer Documentation

This document describes the current OW Smurfer repository and runtime behavior.

## 1. Purpose

OW Smurfer is a small Windows tray utility for quickly logging into saved Overwatch accounts. It stores account entries locally, lets the user choose a login hotkey, and can start with Windows.

## 2. Repository Layout

```text
OW_Smurfer
  OW_Smurfer.pyw     Main PySide6 application entrypoint
  Overwatch.lnk      Shortcut used to start Overwatch in windowed mode
  img                UI screenshots, logo, and icon assets
  img/scripts        Image-related helper scripts
  requirements.txt   Python dependencies
  README.md          User-facing overview
  documentation.md   Technical and maintenance notes
  CHANGELOG.md       Version history
```

## 3. Runtime Data

The app stores its local configuration under:

```text
%LOCALAPPDATA%\OW_Smurfer\config.json
```

Saved account credentials are obfuscated in the local config file. This avoids casual plain-text reading, but it is not strong encryption and should not be treated as a secure password vault.

## 4. Main Workflow

1. The user opens the tray app.
2. Accounts are added or edited in settings.
3. A global hotkey opens the quick account selector.
4. The app types the selected email and password into the active login form.
5. The configured separator mode controls whether Enter or Tab is sent between fields.

## 5. Development

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run:

```powershell
pythonw .\OW_Smurfer.pyw
```

Basic syntax validation:

```powershell
python -m py_compile .\OW_Smurfer.pyw
```

## 6. Maintenance Guidelines

- Keep account-storage warnings visible in `README.md`.
- Keep screenshots in `img` current when the UI changes.
- Keep image-related helper scripts in `img/scripts`.
- Keep `requirements.txt` minimal and aligned with imports.
- Test tray startup, hotkey behavior, and login typing on Windows after changes.
