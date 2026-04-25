#!/usr/bin/env python3
"""
ssh_manager.py — Multi-account GitHub SSH key detection and config management.

Scans ~/.ssh/ for github_* private keys, reads paired .pub files for usernames,
and maintains a managed Host block in ~/.ssh/config for each account.

Key naming convention:  ~/.ssh/github_<alias>   (private)
                        ~/.ssh/github_<alias>.pub (public)

Generated host alias:   github-<alias>
Used in remote URLs:    git@github-<alias>:user/repo.git
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SSH_DIR = Path.home() / ".ssh"
CONFIG_FILE = SSH_DIR / "config"
BLOCK_START = "# === second-brain: git accounts (managed) ==="
BLOCK_END = "# === end: git accounts ==="


def detect_keys() -> list[dict]:
    """Return list of account dicts for each github_* private key found."""
    if not SSH_DIR.exists():
        return []

    keys = []
    for f in sorted(SSH_DIR.iterdir()):
        name = f.name
        if not name.startswith("github_") or name.endswith(".pub") or not f.is_file():
            continue
        # Skip files with non-key extensions
        if f.suffix in (".ppk", ".pem", ".crt", ".cer"):
            continue

        alias = name[len("github_"):].replace("_", "-")  # github_alec_personal → alec-personal
        pub_path = SSH_DIR / (name + ".pub")
        username = _read_pub_username(pub_path)

        keys.append({
            "alias": alias,
            "host": f"github-{alias}",
            "key_path": str(f),
            "pub_path": str(pub_path) if pub_path.exists() else None,
            "username": username,
        })

    return keys


def _read_pub_username(pub_path: Path) -> str:
    """Extract comment field (username/email) from a public key file."""
    try:
        parts = pub_path.read_text(encoding="utf-8").strip().split()
        return parts[-1] if len(parts) >= 3 else pub_path.stem.replace("github_", "")
    except Exception:
        return pub_path.stem.replace("github_", "")


def _build_host_block(key: dict) -> str:
    return (
        f"Host {key['host']}\n"
        f"  HostName github.com\n"
        f"  User git\n"
        f"  IdentityFile {key['key_path']}\n"
        f"  IdentitiesOnly yes\n"
    )


def update_ssh_config(keys: list[dict]) -> str:
    """Write managed block into ~/.ssh/config. Returns a status summary."""
    SSH_DIR.mkdir(mode=0o700, exist_ok=True)

    existing = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else ""

    # Strip previous managed block
    pattern = re.compile(
        rf"{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}\n?", re.DOTALL
    )
    base = pattern.sub("", existing).rstrip("\n")

    if not keys:
        CONFIG_FILE.write_text((base + "\n") if base else "", encoding="utf-8")
        return "No github_* keys found — ~/.ssh/config unchanged."

    blocks = "\n".join(_build_host_block(k) for k in keys)
    managed_section = f"\n{BLOCK_START}\n{blocks}\n{BLOCK_END}\n"
    new_config = base + managed_section if base else managed_section.lstrip("\n")

    CONFIG_FILE.write_text(new_config, encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except Exception:
        pass

    lines = [f"  {k['host']} → {k['key_path']} ({k['username']})" for k in keys]
    return "Updated ~/.ssh/config:\n" + "\n".join(lines)


def validate_connections(keys: list[dict]) -> dict[str, bool]:
    """Test SSH connectivity for each account. GitHub returns exit 1 with 'Hi <user>!' on success."""
    results = {}
    for k in keys:
        host = k["host"]
        try:
            proc = subprocess.run(
                [
                    "ssh", "-T",
                    "-o", "StrictHostKeyChecking=accept-new",
                    "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=10",
                    f"git@{host}",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = proc.stdout + proc.stderr
            results[host] = "Hi " in output or "successfully authenticated" in output
        except Exception:
            results[host] = False
    return results


def setup(validate: bool = True) -> None:
    keys = detect_keys()
    print(update_ssh_config(keys))

    if not keys:
        print("\nAdd SSH keys named  ~/.ssh/github_<alias>  (private key)")
        print("and               ~/.ssh/github_<alias>.pub (public key)")
        print("Example: ~/.ssh/github_alec-personal  and  ~/.ssh/github_alec-personal.pub")
        return

    if validate:
        print("\nValidating SSH connections...")
        results = validate_connections(keys)
        for host, ok in results.items():
            status = "connected" if ok else "FAILED (check key is added to GitHub account)"
            mark = "✓" if ok else "✗"
            print(f"  {mark} {host}: {status}")

    print("\nAvailable account aliases for .gitaccount:")
    for k in keys:
        print(f"  account = \"{k['alias']}\"  →  git@{k['host']}:...")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Manage GitHub multi-account SSH config")
    p.add_argument("--list", action="store_true", help="List detected keys (tab-separated)")
    p.add_argument("--no-validate", action="store_true", help="Skip SSH connectivity check")
    p.add_argument("--update-only", action="store_true", help="Update config without validating")
    args = p.parse_args()

    if args.list:
        for k in detect_keys():
            print(f"{k['alias']}\t{k['host']}\t{k['username']}")
    else:
        setup(validate=not (args.no_validate or args.update_only))
