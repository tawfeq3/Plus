import json
import os
import plistlib
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "tawfeq3/Plus")
BRANCH = "main"

APPS_DIR = Path("apps")
ICONS_DIR = Path("icons")
APPJSON = Path("app.json")

ICON_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]


def find_icon_url(ipa_path):
    for ext in ICON_EXTENSIONS:
        icon_path = ICONS_DIR / f"{ipa_path.stem}{ext}"

        if icon_path.exists():
            return (
                f"https://raw.githubusercontent.com/"
                f"{REPO}/{BRANCH}/icons/{icon_path.name}"
            )

    return ""


def read_ipa_info(ipa_path):
    with zipfile.ZipFile(ipa_path) as z:
        plist_name = next(
            name
            for name in z.namelist()
            if name.startswith("Payload/")
            and name.endswith(".app/Info.plist")
        )

        with z.open(plist_name) as f:
            plist = plistlib.load(f)

    return {
        "bundleIdentifier": plist.get("CFBundleIdentifier", ""),
        "name": (
            plist.get("CFBundleDisplayName")
            or plist.get("CFBundleName")
            or ipa_path.stem
        ),
        "version": plist.get("CFBundleShortVersionString", "1.0"),
        "buildVersion": plist.get("CFBundleVersion", ""),
        "minOSVersion": plist.get("MinimumOSVersion", ""),
    }


def main():
    data = json.loads(APPJSON.read_text(encoding="utf-8"))
    apps = data.setdefault("apps", [])

    by_bundle = {
        app.get("bundleIdentifier"): app
        for app in apps
        if app.get("bundleIdentifier")
    }

    tz = timezone(timedelta(hours=3))
    today = datetime.now(tz).strftime("%Y-%m-%dT00:00:00+03:00")

    for ipa_path in sorted(APPS_DIR.glob("*.ipa")):

        try:
            info = read_ipa_info(ipa_path)
        except Exception as e:
            print(f"Skipping {ipa_path}: {e}")
            continue

        bundle_id = info["bundleIdentifier"]

        if not bundle_id:
            print(f"Skipping {ipa_path}: bundle identifier missing")
            continue

        size = ipa_path.stat().st_size

        download_url = (
            f"https://github.com/{REPO}/raw/refs/heads/"
            f"{BRANCH}/apps/{ipa_path.name}"
        )

        icon_url = find_icon_url(ipa_path)

        version_entry = {
            "version": info["version"],
            "date": today,
            "localizedDescription": "New release!",
            "downloadURL": download_url,
            "size": size,
            "buildVersion": info["buildVersion"],
            "minOSVersion": info["minOSVersion"],
        }

        # تحديث تطبيق موجود
        if bundle_id in by_bundle:

            app = by_bundle[bundle_id]

            versions = app.setdefault("versions", [])
