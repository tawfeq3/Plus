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
        icon = ICONS_DIR / f"{ipa_path.stem}{ext}"
        if icon.exists():
            return (
                f"https://raw.githubusercontent.com/"
                f"{REPO}/{BRANCH}/icons/{icon.name}"
            )
    return ""


def read_ipa_info(ipa_path):
    with zipfile.ZipFile(ipa_path) as z:
        plist_name = next(
            n for n in z.namelist()
            if n.startswith("Payload/")
            and n.endswith(".app/Info.plist")
        )

        with z.open(plist_name) as f:
            plist = plistlib.load(f)

    return {
        "name": (
            plist.get("CFBundleDisplayName")
            or plist.get("CFBundleName")
            or ipa_path.stem
        ),
        "bundleIdentifier": plist.get("CFBundleIdentifier", ""),
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

    for ipa in sorted(APPS_DIR.glob("*.ipa")):

        try:
            info = read_ipa_info(ipa)
        except Exception as e:
            print(f"SKIP {ipa}: {e}")
            continue

        bundle = info["bundleIdentifier"]

        if not bundle:
            print(f"SKIP {ipa}: missing bundle identifier")
            continue

        size = ipa.stat().st_size

        download_url = (
            f"https://github.com/{REPO}/raw/refs/heads/"
            f"{BRANCH}/apps/{ipa.name}"
        )

        icon_url = find_icon_url(ipa)

        version = {
            "version": info["version"],
            "date": today,
            "localizedDescription": "New release!",
            "downloadURL": download_url,
            "size": size,
            "buildVersion": info["buildVersion"],
            "minOSVersion": info["minOSVersion"],
        }

        # Existing app
        if bundle in by_bundle:

            app = by_bundle[bundle]

            versions = app.setdefault("versions", [])

            versions[:] = [
                v for v in versions
                if v.get("version") != info["version"]
            ]

            versions.insert(0, version)

            app.update({
                "version": info["version"],
                "versionDate": today,
                "versionDescription": "New release!",
                "downloadURL": download_url,
                "size": size,
                "type": 1,
            })

            if icon_url:
                app["iconURL"] = icon_url

            print(f"UPDATED: {info['name']} {info['version']}")

        # New app
        else:

            app = {
                "name": info["name"],
                "bundleIdentifier": bundle,
                "marketplaceID": "",
                "developerName": "",
                "subtitle": "",
                "version": info["version"],
                "versionDate": today,
                "versionDescription": "New release!",
                "downloadURL": download_url,
                "localizedDescription": info["name"],
                "iconURL": icon_url,
                "tintColor": "#5865F2",
                "size": size,
                "type": 1,
                "category": "other",
                "screenshots": [],
                "versions": [version],
                "appPermissions": {
                    "entitlements": [],
                    "privacy": {}
                },
                "patreon": {}
            }

            apps.append(app)
            by_bundle[bundle] = app

            print(f"ADDED: {info['name']} {info['version']}")

    APPJSON.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print("SUCCESS: app.json updated")


if __name__ == "__main__":
    main()
