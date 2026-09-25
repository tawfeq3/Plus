import json
import os
import plistlib
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "tawfeq3/Plus")
BRANCH = "main"
APPS_DIR = Path("apps")
APPJSON = Path("app.json")


def read_ipa_info(ipa_path):
    with zipfile.ZipFile(ipa_path) as z:
        plist_name = next(
            n for n in z.namelist()
            if n.startswith("Payload/") and n.endswith(".app/Info.plist") and n.count("/") == 2
        )
        with z.open(plist_name) as f:
            plist = plistlib.load(f)
    return {
        "bundleIdentifier": plist.get("CFBundleIdentifier", ""),
        "name": plist.get("CFBundleDisplayName") or plist.get("CFBundleName") or ipa_path.stem,
        "version": plist.get("CFBundleShortVersionString", "1.0"),
        "buildVersion": plist.get("CFBundleVersion"),
        "minOSVersion": plist.get("MinimumOSVersion"),
    }


def main():
    data = json.loads(APPJSON.read_text(encoding="utf-8"))
    apps = data.setdefault("apps", [])
    by_bundle = {a.get("bundleIdentifier"): a for a in apps}

    tz = timezone(timedelta(hours=3))
    today = datetime.now(tz).strftime("%Y-%m-%dT00:00:00+03:00")

    for ipa_path in sorted(APPS_DIR.glob("*.ipa")):
        try:
            info = read_ipa_info(ipa_path)
        except StopIteration:
            print(f"Skipping {ipa_path}: could not find Info.plist inside IPA")
            continue

        bundle_id = info["bundleIdentifier"]
        if not bundle_id:
            print(f"Skipping {ipa_path}: no bundle identifier found")
            continue

        size = ipa_path.stat().st_size
        download_url = f"https://github.com/{REPO}/raw/refs/heads/{BRANCH}/apps/{ipa_path.name}"

        version_entry = {
            "version": info["version"],
            "date": today,
            "localizedDescription": "New release!",
            "downloadURL": download_url,
            "size": size,
            "buildVersion": info["buildVersion"],
            "minOSVersion": info["minOSVersion"],
        }

        if bundle_id in by_bundle:
            app = by_bundle[bundle_id]
            versions = app.setdefault("versions", [])
            if versions and versions[0].get("version") == info["version"]:
                versions[0] = version_entry
            else:
                versions.insert(0, version_entry)
            print(f"Updated {app.get('name')} -> {info['version']}")
        else:
            new_app = {
                "name": info["name"],
                "bundleIdentifier": bundle_id,
                "marketplaceID": "",
                "developerName": "",
                "subtitle": "",
                "localizedDescription": info["name"],
                "iconURL": "",
                "tintColor": "#5865F2",
                "category": "other",
                "screenshots": [],
                "versions": [version_entry],
                "appPermissions": {"entitlements": [], "privacy": {}},
                "patreon": {},
            }
            apps.append(new_app)
            by_bundle[bundle_id] = new_app
            print(f"Added new app: {info['name']} ({bundle_id})")

    APPJSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
