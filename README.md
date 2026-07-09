# Scambuster Anniversary Updater 2.0

Scambuster Anniversary Updater is a small Windows utility that installs and keeps up to date the **[Scambuster framework](https://github.com/hypernormalisation/Scambuster)** and the **Scambuster–Spineshatter** addon for the WoW Anniversary client.

It is built for the **Spineshatter EU** community and automates downloading the latest releases and installing them into your `_anniversary_` AddOns folder.

⚠️ **Important:** Scambuster Anniversary Updater **1.0 is no longer supported**.  
If you wish to continue using the Scambuster addon and receive future updates, remove the old updater and install **Scambuster Anniversary Updater 2.0**.

---

## What it does

- Detects your World of Warcraft **Anniversary** installation (tries common paths and remembers your choice in `config.json`).
- Installs or updates:
  - **Scambuster (framework)** – `hypernormalisation/Scambuster`
  - **Scambuster–Spineshatter** – `spineshatter/Scambuster-Spineshatter`
- Fetches the latest releases from their supported release sources:
  - GitHub releases
  - GitLab releases/packages
- Installs addon `.zip` packages into:
  - `<WoW root>/_anniversary_/Interface/AddOns/Scambuster`
  - `<WoW root>/_anniversary_/Interface/AddOns/Scambuster-Spineshatter`
- Shows current **installed** vs **latest** version with clear status:
  - Up to date
  - Update available
  - Not installed / requires Scambuster
- Lets you **remove** each addon (deletes its folder under AddOns).
- Logs all actions in a built-in log panel.

---

## Version 2.0 Changes

- Migrated Scambuster–Spineshatter updates from GitHub releases to the new GitLab release system.
- Added support for GitLab-hosted addon packages.
- Updated version detection and download handling for the new release workflow.
- Improved updater support for future addon updates.

---

## Requirements

- Windows (tested on modern 64-bit Windows).
- World of Warcraft **Anniversary** client.
- Internet access for downloading addon releases.

The UI is built with Tkinter and the standalone executable is created with PyInstaller.

---

## Download

If you’re just a user:

Download the latest **installer** or **portable exe** from the releases page:

https://github.com/Spine-Scambuster/Scambuster-Anniversary-Updater/releases

Recommended:

- `ScambusterAnniversaryUpdaterSetup.exe` – installer version
- `ScambusterAnniversaryUpdater.exe` – portable version

---

## Usage

1. Install and run **Scambuster Anniversary Updater 2.0**.
2. On first launch it will try to auto-detect your WoW root folder.
3. If detection fails:
   - Click **Browse** and select your WoW folder.
4. Select **Install** or **Update** for:
   - **Scambuster (framework)**
   - **Scambuster–Spineshatter**
5. The updater will download the latest release package and install it automatically.

> Note: The Scambuster–Spineshatter addon requires the Scambuster framework.  
> The updater will enforce this requirement before installing Scambuster–Spineshatter.

---

## Config / Persistence

The tool stores your selected WoW root in a simple JSON file:

- `config.json` is stored in the user’s application data folder.

Example:

```json
{
  "wow_root": "C:\\Program Files (x86)\\World of Warcraft"
}
