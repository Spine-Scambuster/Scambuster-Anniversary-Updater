import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import requests
import re
import shutil
import ctypes
import os

# Config
ADDONS = [
    {
        "key": "scambuster",
        "name": "Scambuster (framework)",
        "folder": "Scambuster",
        "toc": "Scambuster.toc",
        "owner": "hypernormalisation",
        "repo": "Scambuster",
    },
    {
        "key": "spineshatter",
        "name": "Scambuster-Spineshatter",
        "folder": "Scambuster-Spineshatter",
        "toc": "Scambuster-Spineshatter.toc",
        "owner": "Spine-Scambuster",
        "repo": "Scambuster-Spineshatter",
    },
]

API_RELEASES_URL_TMPL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
CONFIG_FILE = "config.json"
ANNIVERSARY_SUBPATH = Path("_anniversary_") / "Interface" / "AddOns"
COMMON_WOW_ROOTS = [
    Path(r"C:\Program Files (x86)\World of Warcraft"),
    Path(r"C:\Program Files\World of Warcraft"),
    Path(r"D:\World of Warcraft"),
    Path(r"E:\World of Warcraft"),
]


# HELPERS
def resource_path(relative: str) -> str:
    """Get absolute path to resource, works for dev and bundled exe."""
    base_path = getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent)
    return str(Path(base_path) / relative)


def load_json(path: str | Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: str | Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_config():
    return load_json(resource_path(CONFIG_FILE), {"wow_root": ""})


def save_config(cfg) -> None:
    save_json(resource_path(CONFIG_FILE), cfg)


def get_anniversary_addons_path(wow_root: Path) -> Path:
    return wow_root / ANNIVERSARY_SUBPATH


def auto_detect_wow_root() -> Path | None:
    cfg = get_config()
    p = Path(cfg.get("wow_root", ""))
    if p.exists() and (p / "_anniversary_").exists():
        return p
    for root in COMMON_WOW_ROOTS:
        if root.exists() and (root / "_anniversary_").exists():
            return root
    return None


def log_append(widget: tk.Text, msg: str) -> None:
    widget.configure(state="normal")
    widget.insert(tk.END, f"{msg}\n")
    widget.see(tk.END)
    widget.configure(state="disabled")


def read_version_from_toc(addon_folder: Path, toc_name: str) -> str | None:
    toc_path = addon_folder / toc_name
    if not toc_path.exists():
        return None
    try:
        with open(toc_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().lower().startswith("## version:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def normalize_version(v: str | None) -> str:
    if not v:
        return ""
    return re.sub(r"[^0-9.]", "", str(v)).strip()


def clear_directory(path: Path, log_widget: tk.Text | None = None) -> None:
    if not path.exists():
        return
    try:
        shutil.rmtree(path, ignore_errors=True)
        if log_widget is not None:
            log_append(log_widget, f"🧹 Cleared {path}")
    except Exception as e:
        if log_widget is not None:
            log_append(log_widget, f"❌ Failed to clear {path}: {e}")


def remove_addon(addon_cfg: dict, wow_root: Path, log_widget: tk.Text) -> None:
    addon_path = get_anniversary_addons_path(wow_root) / addon_cfg["folder"]
    if not addon_path.exists():
        log_append(log_widget, f"ℹ️ {addon_cfg['name']} not installed")
        return
    clear_directory(addon_path, log_widget)
    log_append(log_widget, f"🗑️ {addon_cfg['name']} removed")


def get_latest_release(addon_cfg: dict) -> dict:
    url = API_RELEASES_URL_TMPL.format(owner=addon_cfg["owner"], repo=addon_cfg["repo"])
    resp = requests.get(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Scambuster-Updater",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def install_addon(addon_cfg: dict, wow_root: Path, log_widget: tk.Text) -> str | None:
    addons_path = get_anniversary_addons_path(wow_root)
    log_append(log_widget, f"📦 Installing {addon_cfg['name']}...")

    try:
        rel = get_latest_release(addon_cfg)
        asset = next(
            (a for a in rel.get("assets", []) if a["name"].lower().endswith(".zip")),
            None,
        )
        if not asset:
            raise Exception("No ZIP asset found")

        zip_bytes = BytesIO(
            requests.get(asset["browser_download_url"], timeout=60).content
        )
        target_root = addons_path / addon_cfg["folder"]

        clear_directory(target_root, log_widget)
        target_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_bytes) as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                parts = Path(member.filename).parts
                if parts and parts[0].lower().startswith(addon_cfg["folder"].lower()):
                    final_path = target_root / Path(*parts[1:])
                else:
                    final_path = target_root / Path(*parts)
                final_path.parent.mkdir(parents=True, exist_ok=True)
                final_path.write_bytes(zf.read(member))

        log_append(log_widget, f"✅ {addon_cfg['name']} installed!")
        return read_version_from_toc(target_root, addon_cfg["toc"]) or rel.get(
            "tag_name"
        )
    except Exception as e:
        log_append(log_widget, f"❌ Install failed: {e}")
        raise


def is_scambuster_installed(wow_root: Path) -> bool:
    framework_folder = next(a for a in ADDONS if a["key"] == "scambuster")["folder"]
    scambuster_path = get_anniversary_addons_path(wow_root) / framework_folder
    return scambuster_path.exists()


# ROW CLASS
class AddonRow(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        addon_cfg: dict,
        wow_var: tk.StringVar,
        log_widget: tk.Text,
        refresh_all_callback,
    ):
        super().__init__(parent, bg="#242731")
        self.addon_cfg = addon_cfg
        self.wow_var = wow_var
        self.log_widget = log_widget
        self.refresh_all_callback = refresh_all_callback
        self.releases: dict[str, str] = {}

        for i in range(6):
            self.columnconfigure(i, weight=1, uniform="table")

        self.name_label = tk.Label(
            self,
            text=addon_cfg["name"],
            font=("Segoe UI", 10, "bold"),
            bg="#242731",
            fg="#e4e6ed",
            anchor="center",
        )
        self.name_label.grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        # Installed column: version / "Not installed"
        self.installed_var = tk.StringVar(value="Loading...")
        self.installed_label = tk.Label(
            self,
            textvariable=self.installed_var,
            font=("Segoe UI", 9),
            bg="#242731",
            fg="#e4e6ed",
            anchor="center",
        )
        self.installed_label.grid(row=0, column=1, sticky="ew", padx=10, pady=8)

        self.latest_var = tk.StringVar(value="Loading...")
        self.latest_label = tk.Label(
            self,
            textvariable=self.latest_var,
            font=("Segoe UI", 9),
            bg="#242731",
            fg="#e4e6ed",
            anchor="center",
        )
        self.latest_label.grid(row=0, column=2, sticky="ew", padx=10, pady=8)

        self.status_var = tk.StringVar(value="Loading...")
        self.status_label = tk.Label(
            self,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            bg="#242731",
            fg="#e4e6ed",
            anchor="center",
        )
        self.status_label.grid(row=0, column=3, sticky="ew", padx=10, pady=8)

        self.action_btn = tk.Button(
            self,
            text="Loading...",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            height=2,
            cursor="hand2",
            bg="#ff6b6b",
            fg="white",
            activebackground="#ff7f7f",
            activeforeground="white",
        )
        self.action_btn.grid(row=0, column=4, sticky="ew", padx=8, pady=8)
        self.action_btn.configure(command=self.on_action)

        # Constant-color remove button, state changes
        self.remove_btn = tk.Button(
            self,
            text="Remove",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            bd=0,
            width=8,
            height=2,
            cursor="hand2",
            state="disabled",
            bg="#2d3436",
            fg="#e4e6ed",
            activebackground="#3b3f4a",
            activeforeground="#e4e6ed",
        )
        self.remove_btn.grid(row=0, column=5, sticky="ew", padx=10, pady=8)
        self.remove_btn.configure(command=self.on_remove)

    def refresh(self):
        wow_root = Path(self.wow_var.get().strip())
        if not wow_root.exists() or not (wow_root / "_anniversary_").exists():
            self.installed_var.set("No WoW")
            self.latest_var.set("-")
            self.status_var.set("Select WoW")
            self.status_label.configure(fg="#ff6b6b")
            self.action_btn.configure(
                state="disabled", text="No WoW", bg="gray", fg="white"
            )
            self.remove_btn.configure(state="disabled")
            return

        addon_path = get_anniversary_addons_path(wow_root) / self.addon_cfg["folder"]
        installed_ver = (
            read_version_from_toc(addon_path, self.addon_cfg["toc"])
            if addon_path.exists()
            else None
        )

        key = self.addon_cfg["key"]
        if key not in self.releases:
            try:
                rel = get_latest_release(self.addon_cfg)
                self.releases[key] = rel.get("tag_name", "")
                log_append(
                    self.log_widget,
                    f"✓ {self.addon_cfg['owner']}/{self.addon_cfg['repo']}: {self.releases[key]}",
                )
            except Exception:
                self.releases[key] = "error"

        latest_ver = self.releases[key]
        installed_norm = normalize_version(installed_ver)
        latest_norm = normalize_version(latest_ver)

        self.installed_var.set(installed_ver or "Not installed")
        self.latest_var.set(latest_ver)

        if addon_path.exists():
            if installed_norm == latest_norm and installed_norm:
                self.status_var.set("✅ Up to date")
                self.status_label.configure(fg="#00d4aa")
                self.action_btn.configure(
                    text="Installed ✓",
                    bg="#00d4aa",
                    fg="white",
                    state="disabled",
                )
                self.remove_btn.configure(state="normal")
            else:
                self.status_var.set("🔄 Update available")
                self.status_label.configure(fg="#ff9f43")
                self.action_btn.configure(
                    text="Update",
                    bg="#ff6b6b",
                    fg="white",
                    state="normal",
                )
                self.remove_btn.configure(state="normal")
        else:
            if self.addon_cfg["key"] == "spineshatter" and not is_scambuster_installed(
                wow_root
            ):
                self.status_var.set("⚠️ Requires Scambuster")
                self.status_label.configure(fg="#ff9f43")
                self.action_btn.configure(
                    text="Install Scambuster first",
                    bg="#ff9f43",
                    fg="white",
                    state="disabled",
                )
            else:
                self.status_var.set("❌ Not installed")
                self.status_label.configure(fg="#ff6b6b")
                self.action_btn.configure(
                    text="Install",
                    bg="#ff6b6b",
                    fg="white",
                    state="normal",
                )
            self.remove_btn.configure(state="disabled")

    def on_action(self):
        wow_root = Path(self.wow_var.get().strip())
        if not wow_root.exists() or not (wow_root / "_anniversary_").exists():
            messagebox.showwarning("Error", "Select valid WoW folder first")
            return

        if self.action_btn.cget("state") == "disabled":
            return

        try:
            install_addon(self.addon_cfg, wow_root, self.log_widget)
            self.refresh_all_callback()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_remove(self):
        wow_root = Path(self.wow_var.get().strip())
        if messagebox.askyesno(
            "Confirm Remove", f"Remove {self.addon_cfg['name']}?"
        ):
            remove_addon(self.addon_cfg, wow_root, self.log_widget)
            self.refresh_all_callback()


# APP
def create_app():
    global log_text

    # Separate AppID so Windows uses this icon on taskbar/tray
    try:
        myappid = "Spineshatter.Scambuster.Updater"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    root = tk.Tk()
    root.title("Scambuster Anniversary Updater")

    # Window + taskbar icon
    try:
        icon_path = resource_path("spineshatter.ico")
        root.iconbitmap(icon_path)
    except Exception:
        pass

    root.geometry("1200x820")
    root.resizable(False, False)
    root.configure(bg="#1a1d21")

    colors = {
        "bg": "#1a1d21",
        "card": "#242731",
        "text": "#e4e6ed",
        "orange": "#ff9f43",
        "accent": "#5865f2",
    }

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Dark.TButton",
        background="#2d3436",
        foreground=colors["text"],
        font=("Segoe UI", 10, "bold"),
    )
    style.map("Dark.TButton", background=[("active", colors["accent"])])

    main_frame = tk.Frame(root, bg=colors["bg"])
    main_frame.pack(fill="both", expand=True, padx=30, pady=30)

    tk.Label(
        main_frame,
        text="🎮 Scambuster Anniversary Updater",
        font=("Segoe UI", 28, "bold"),
        bg=colors["bg"],
        fg=colors["text"],
    ).pack(pady=(0, 35))

    # WoW Path
    path_frame = tk.Frame(main_frame, bg=colors["bg"])
    path_frame.pack(fill="x", pady=(0, 25))
    tk.Label(
        path_frame,
        text="📁 World of Warcraft Folder:",
        font=("Segoe UI", 13, "bold"),
        bg=colors["bg"],
        fg=colors["text"],
    ).pack(anchor="w")

    wow_frame = tk.Frame(path_frame, bg=colors["bg"])
    wow_frame.pack(fill="x", pady=(12, 0))

    wow_var = tk.StringVar(value=str(auto_detect_wow_root() or ""))
    wow_entry = tk.Entry(
        wow_frame,
        textvariable=wow_var,
        font=("Segoe UI", 12),
        bg=colors["card"],
        fg=colors["text"],
        relief="flat",
        bd=0,
        highlightthickness=2,
        highlightcolor=colors["accent"],
    )
    wow_entry.pack(side="left", fill="x", expand=True, padx=(0, 20), ipady=12)

    overall_status_var = tk.StringVar(value="Status: not checked yet")

    def refresh_all():
        wow_root = Path(wow_var.get().strip())
        all_ok = True

        for row in rows:
            row.refresh()

            addon_path = get_anniversary_addons_path(wow_root) / row.addon_cfg["folder"]
            installed_ver = (
                read_version_from_toc(addon_path, row.addon_cfg["toc"])
                if addon_path.exists()
                else None
            )
            latest_ver = row.releases.get(row.addon_cfg["key"], "")
            installed_norm = normalize_version(installed_ver)
            latest_norm = normalize_version(latest_ver)

            if not addon_path.exists():
                all_ok = False
            elif not installed_norm or installed_norm != latest_norm:
                all_ok = False

        if all_ok:
            overall_status_var.set("Status: all addons are up to date")
        else:
            overall_status_var.set(
                "Status: updates available or addons not installed"
            )

    def browse_path():
        folder = filedialog.askdirectory(
            title="Select WoW folder (contains _anniversary_)",
            initialdir=wow_var.get() or str(Path.home()),
        )
        if folder:
            wow_var.set(folder)
            save_config({"wow_root": folder})
            refresh_all()

    ttk.Button(
        wow_frame, text="Browse", style="Dark.TButton", width=12, command=browse_path
    ).pack(side="right")

    tk.Label(
        main_frame,
        text="⚠️ Scambuster-Spineshatter requires Scambuster installed first",
        font=("Segoe UI", 11),
        bg=colors["bg"],
        fg=colors["orange"],
    ).pack(anchor="w", pady=(0, 25))

    # Header
    header_frame = tk.Frame(main_frame, bg="#2d3436", height=50)
    header_frame.pack(fill="x", pady=(0, 15))
    header_frame.pack_propagate(False)

    for i, title in enumerate(
        ["Addon", "Installed", "Latest", "Status", "Action", "Remove"]
    ):
        tk.Label(
            header_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg="#2d3436",
            fg=colors["text"],
            anchor="center",
        ).grid(row=0, column=i, sticky="ew", padx=2)
        header_frame.columnconfigure(i, weight=1)

    rows_frame = tk.Frame(main_frame, bg=colors["bg"])
    rows_frame.pack(fill="both", expand=True, pady=(0, 20))
    rows_frame.columnconfigure(0, weight=1)

    # Log
    log_frame = tk.Frame(main_frame, bg=colors["card"])
    log_frame.pack(fill="x")
    tk.Label(
        log_frame,
        text="📋 Log",
        font=("Segoe UI", 14, "bold"),
        bg=colors["card"],
        fg=colors["text"],
    ).pack(anchor="w", padx=20, pady=(20, 10))
    log_text = tk.Text(
        log_frame,
        height=10,
        bg="#1e2124",
        fg=colors["text"],
        font=("Consolas", 11),
        relief="flat",
        bd=0,
        state="disabled",
    )
    log_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    rows: list[AddonRow] = []

    # Rows
    for addon_cfg in ADDONS:
        row = AddonRow(
            rows_frame, addon_cfg, wow_var, log_text, refresh_all_callback=refresh_all
        )
        row.grid(row=len(rows), column=0, sticky="ew", pady=2)
        rows.append(row)

    # Status line
    status_frame = tk.Frame(main_frame, bg=colors["bg"])
    status_frame.pack(fill="x", pady=(10, 0))

    tk.Label(
        status_frame,
        textvariable=overall_status_var,
        font=("Segoe UI", 11, "bold"),
        bg=colors["bg"],
        fg=colors["text"],
        anchor="w",
    ).pack(side="left")

    if wow_var.get():
        root.after(100, refresh_all)

    root.mainloop()


if __name__ == "__main__":
    create_app()
