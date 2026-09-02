# Tawfiq Store

Repository for iOS applications, designed around the repository format used by Feather and compatible repository clients.

## Current structure

- `repo.json` — repository index
- `apps/` — IPA files, organized by application
- `icons/` — application/store icons
- `screenshots/` — application screenshots
- `backend/` — future API/admin server

## Important

Do not upload `.p12`, private keys, passwords, or Apple Developer credentials to this repository.

The first milestone is:

Upload IPA -> extract metadata -> update repo.json -> publish direct IPA/icon URLs -> test in Feather/ESign.

## Repository URL

After GitHub Pages or another HTTPS host is configured, the public repository URL will point to:

`https://<host>/repo.json`
