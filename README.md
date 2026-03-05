# Scambuster Anniversary Updater

Scambuster Anniversary Updater is a small Windows utility that installs and keeps up to date the **[Scambuster framework](https://github.com/hypernormalisation/Scambuster)** and the **[Scambuster–Spineshatter](https://github.com/Spine-Scambuster/Scambuster-Spineshatter)** addon for the WoW Anniversary client.

It is built for the **Spineshatter EU** community and automates downloading the latest releases from GitHub and installing them into your `_anniversary_` AddOns folder.

---

## What it does

- Detects your World of Warcraft **Anniversary** installation (tries common paths and remembers your choice in `config.json`).
- Installs or updates:
  - **Scambuster (framework)** – `hypernormalisation/Scambuster`
  - **Scambuster–Spineshatter** – `Spine-Scambuster/Scambuster-Spineshatter`
- Fetches the **latest GitHub release** for each addon and installs the `.zip` asset into:
  - `<WoW root>/_anniversary_/Interface/AddOns/Scambuster`
  - `<WoW root>/_anniversary_/Interface/AddOns/Scambuster-Spineshatter`
- Shows current **installed** vs **latest** version, with clear status:
  - Up to date
  - Update available
  - Not installed / requires Scambuster
- Lets you **remove** each addon (deletes its folder under AddOns).
- Logs all actions in a built‑in log panel.

---

## Requirements

- Windows (tested on modern 64‑bit Windows).
- World of Warcraft **Anniversary** client.
- Internet access (to fetch GitHub releases).

The UI is built with Tkinter and the standalone executable is created with PyInstaller.

---

## Download

If you’re just a user:

- Download the latest **installer** or **portable exe** from the [releases page](https://github.com/Spine-Scambuster/Scambuster-Anniversary-Updater/releases).

Example:

- `ScambusterAnniversaryUpdaterSetup.exe` – installs into `C:\Program Files\Scambuster Anniversary Updater\`
- `ScambusterAnniversaryUpdater.exe` – portable version, runs from any folder

---

## Usage

1. **Run the app.**  
   On first launch it will try to auto–detect your WoW root from common paths:
   - `C:\Program Files (x86)\World of Warcraft`
   - `C:\Program Files\World of Warcraft`
   - `D:\World of Warcraft`
   - `E:\World of Warcraft`

2. If auto‑detection fails:
   - Click **Browse** and select your WoW folder.

3. The main table will show two rows:
   - **Scambuster (framework)**
   - **Scambuster–Spineshatter**

   For each row you’ll see:
   - Installed version (from the `.toc` file, if present).
   - Latest version (from GitHub releases).
   - Status and action buttons (Install, Update, Remove).

4. Click **Install** or **Update**:
   - The tool downloads the latest `.zip` from GitHub.
   - It clears the existing addon folder (if present).
   - It extracts the archive into the correct AddOns subfolder.

5. Use the **Remove** button to delete an addon completely.

6. The **log panel** at the bottom shows each step (downloads, extraction, errors, etc.).

> Note: The Scambuster–Spineshatter addon requires the Scambuster framework.  
> The tool will enforce this and disable installation of Scambuster–Spineshatter if the Scambuster framework is missing.

---

## Config / Persistence

The tool stores your selected WoW root in a simple JSON file:

- `config.json` is stored in the user’s application data folder (for example, `C:\Users\<YourUser>\AppData\Roaming\ScambusterAnniversaryUpdater\config.json` on Windows).
- Structure (example):

  ```json
  {
    "wow_root": "C:\\Program Files (x86)\\World of Warcraft"
  }
