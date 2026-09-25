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
ICON_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"]
APPJSON = Path("app.json")


def find_icon_url(ipa_path):
    """Find an icon with the same filename as the IPA."""
    for ext in ICON_EXTENSIONS:
        icon_path = ICONS_DIR / f"{ipa_path.stem}{ext}"

        if icon_path.exists():
            return (
                f"https://raw.githubusercontent.com/"
                f"{REPO}/{BRANCH}/icons/{icon_path.name}"
            )

    return ""


def read_ipa_info(ipa_path):
    """Read application information from Info.plist inside the IPA."""
    with zipfile.ZipFile(ipa_path) as z:
        plist_name = next(
            n for n in z.namelist()
            if (
                n.startswith("Payload/")
                and n.endswith(".app/Info.plist")
                and n.count("/") == 2
            )
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
        "buildVersion": plist.get("CFBundleVersion"),
        "minOSVersion": plist.get("MinimumOSVersion"),
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

        except (StopIteration, zipfile.BadZipFile, KeyError) as e:
            print(f"Skipping {ipa_path}: cannot read IPA ({e})")
            continue

        bundle_id = info["bundleIdentifier"]

        if not bundle_id:
            print(f"Skipping {ipa_path}: no bundle identifier found")
            continue

        size = ipa_path.stat().st_size

        download_url = (
            f"https://github.com/{REPO}/raw/refs/heads/"
            f"{BRANCH}/apps/{ipa_path.name}"
        )

        icon_url = find_icon_url(ipa_path)

        # Version entry
        version_entry = {
            "version": info["version"],
            "date": today,
            "localizedDescription": "New release!",
            "downloadURL": download_url,
            "size": size,
            "buildVersion": info["buildVersion"],
            "minOSVersion": info["minOSVersion"],
        }

        # ---------------------------------------------------------
        # Existing application
        # ---------------------------------------------------------

        if bundle_id in by_bundle:

            app = by_bundle[bundle_id]

            versions = app.setdefault("versions", [])

            # Update existing version or insert new version
            existing_index = next(
                (
                    i
                    for i, version in enumerate(versions)
                    if version.get("version") == info["version"]
                ),
                None,
            )

            if existing_index is not None:
                versions[existing_index] = version_entry
            else:
                versions.insert(0, version_entry)

            # Update main application information too
            app["
