#!/usr/bin/env python3
"""Interactive configuration script for Email Viewer."""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"


def prompt(msg: str, default: str = "", required: bool = False) -> str:
    """Prompt user for input."""
    if default:
        prompt_msg = f"{msg} [{default}]: "
    else:
        prompt_msg = f"{msg}: "

    while True:
        value = input(prompt_msg).strip()
        if not value:
            if default:
                return default
            elif required:
                print("  This field is required.")
                continue
            else:
                return ""
        return value


def prompt_path(msg: str) -> str:
    """Prompt for a file path."""
    while True:
        path = input(f"{msg}: ").strip()
        if not path:
            return ""
        p = Path(path)
        if p.exists() and p.is_dir():
            return str(p.absolute())
        print(f"  Path does not exist or is not a directory: {path}")


def main():
    print("\n" + "=" * 60)
    print("Email Viewer Configuration")
    print("=" * 60 + "\n")

    # Load existing config if available
    existing_config = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                existing_config = json.load(f)
            print("Found existing configuration. Press Enter to keep current values.\n")
        except Exception:
            pass

    root_path = prompt(
        "Global root path for email files (can be empty)",
        existing_config.get("root_path", "")
    )

    print("\n" + "=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    print(f"Root path: {root_path or '(not set)'}")
    print("\nNote: Individual users can have their own email folder paths")
    print("      set by administrators in the admin panel.")

    confirm = input("\nSave configuration? (yes/no) [yes]: ").strip().lower()
    if confirm in ("", "y", "yes"):
        config = {
            "root_path": root_path,
            "secret_key": existing_config.get("secret_key"),
        }

        # Ensure secret_key is present
        if not config["secret_key"]:
            import secrets
            config["secret_key"] = secrets.token_hex(32)
            print("Generated new secret key")

        SETTINGS_FILE.write_text(json.dumps(config, indent=2))
        print(f"✓ Configuration saved to {SETTINGS_FILE}")
        print("\nNext steps:")
        print("  1. Run: make run")
        print("  2. Visit http://localhost:5000")
        print("  3. Create admin account on first run")
    else:
        print("Cancelled")


if __name__ == "__main__":
    main()
