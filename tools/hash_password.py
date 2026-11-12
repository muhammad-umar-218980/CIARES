"""
Generate a PBKDF2 hash for the admin password.

Usage
-----
    python tools/hash_password.py
    python tools/hash_password.py "my new password"

Paste the printed line into ``.streamlit/secrets.toml`` (locally) and into the
Streamlit Cloud app secrets:

    [auth]
    admin_email = "admin@ciares.local"
    admin_password_hash = "pbkdf2_sha256$..."
"""

from __future__ import annotations

import getpass
import sys

from ui.shared.passwords import hash_password


def main() -> None:
    password = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("New admin password: ")
    if len(password) < 8:
        raise SystemExit("Use at least 8 characters.")
    print(hash_password(password))


if __name__ == "__main__":
    main()
