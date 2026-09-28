"""Open the installed game and offer newer Lopilol patch releases."""

import argparse
import json
import re
import subprocess
import sys
import tkinter as tk
import urllib.request
import webbrowser
from pathlib import Path
from tkinter import ttk


STATE = ".wonderful-everyday-ptbr"
RELEASES_API = "https://api.github.com/repos/lopilol/wonderful-everyday-ptbr/releases?per_page=20"
RELEASE_BASE = "https://github.com/lopilol/wonderful-everyday-ptbr/releases/"
VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$", re.IGNORECASE)
GRAY = "#f0f0f0"
FONT = ("Tahoma", 8)


def version_key(value):
    match = VERSION_RE.fullmatch(value or "")
    if not match:
        return None
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), 1 if rc is None else 0, int(rc or 0)


def choose_update(releases, installed_version):
    current = version_key(installed_version)
    if current is None or not isinstance(releases, list):
        return None
    candidates = []
    for release in releases:
        if not isinstance(release, dict) or release.get("draft"):
            continue
        tag = release.get("tag_name")
        key = version_key(tag)
        if key is None or key <= current:
            continue
        assets = release.get("assets", [])
        valid_assets = [asset for asset in assets if isinstance(asset, dict)
                        and isinstance(asset.get("name"), str)
                        and asset["name"].lower().endswith(".zip")
                        and asset["name"].startswith("Wonderful-Everyday-PTBR-Patch-")
                        and isinstance(asset.get("browser_download_url"), str)
                        and asset["browser_download_url"].startswith(RELEASE_BASE + "download/")]
        if not valid_assets:
            continue
        valid_assets.sort(key=lambda asset: (
            "anterior" not in str(asset.get("label", "")).lower(),
            asset.get("updated_at", "")), reverse=True)
        candidates.append((key, tag, valid_assets[0]["browser_download_url"]))
    if not candidates:
        return None
    _, tag, url = max(candidates)
    return tag, url


def fetch_update(installed_version):
    request = urllib.request.Request(RELEASES_API, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "Lopilol-Traducoes-Launcher",
    })
    with urllib.request.urlopen(request, timeout=4) as response:
        releases = json.load(response)
    return choose_update(releases, installed_version)


def game_folder():
    return Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent


def installed_version(game):
    receipt = game / STATE / "receipt.json"
    if not receipt.is_file():
        return None
    data = json.loads(receipt.read_text(encoding="utf-8"))
    return data.get("version")


def launch_game(game):
    executable = game / "BGI.exe"
    if not executable.is_file():
        raise FileNotFoundError("BGI.exe não foi encontrado nesta pasta.")
    subprocess.Popen([str(executable)], cwd=str(game), close_fds=True)


def show_update(game, current, update, preview=False):
    version, download_url = update
    root = tk.Tk()
    root.title("Lopilol Traduções — Atualização disponível")
    root.geometry("500x260")
    root.resizable(False, False)
    root.configure(bg=GRAY)
    root.option_add("*Font", FONT)
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    asset_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon = tk.PhotoImage(file=str(asset_dir / "logo-icon.png"))
    logo = tk.PhotoImage(file=str(asset_dir / "logo-header.png"))
    root.iconphoto(True, icon)

    header = tk.Frame(root, bg="white")
    header.place(x=0, y=0, width=500, height=62)
    tk.Label(header, image=logo, bg="white").place(x=5, y=7, width=44, height=44)
    tk.Label(header, text="Lopilol", bg="white", font=("Tahoma", 16, "bold"), anchor="w").place(x=52, y=8, width=97)
    tk.Label(header, text="TRADUÇÕES", bg="white", font=FONT, anchor="w").place(x=54, y=36, width=96)
    tk.Label(header, text="Atualização disponível", bg="white", font=("Tahoma", 8, "bold"), anchor="w").place(x=157, y=11, width=327)
    tk.Label(header, text="Wonderful Everyday · 15th Anniversary", bg="white", font=FONT, anchor="w").place(x=157, y=29, width=327)
    ttk.Separator(root).place(x=0, y=62, width=500)

    tk.Label(root, text="Há uma nova versão da tradução PT-BR.", bg=GRAY, anchor="w", font=("Tahoma", 9, "bold")).place(x=22, y=82, width=455)
    tk.Label(root, text=f"Instalada: {current}     Disponível: {version}", bg=GRAY, anchor="w", font=FONT).place(x=22, y=111, width=455)
    tk.Label(root, text="O download abre no navegador. Para instalar, feche o jogo e desinstale o patch atual com o instalador desta versão.", bg=GRAY, anchor="nw", justify="left", wraplength=455, font=FONT).place(x=22, y=139, width=455, height=45)
    ttk.Separator(root).place(x=0, y=213, width=500)

    def download():
        if not preview:
            webbrowser.open(download_url)
        root.destroy()

    def play():
        root.destroy()
        if not preview:
            launch_game(game)

    ttk.Button(root, text="Baixar atualização", command=download).place(x=243, y=226, width=128, height=23)
    ttk.Button(root, text="Jogar agora", command=play).place(x=385, y=226, width=101, height=23)
    root.protocol("WM_DELETE_WINDOW", play)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.preview:
        show_update(game_folder(), "v0.3.0-rc9", ("v0.3.0-rc10", RELEASE_BASE + "download/v0.3.0-rc10/exemplo.zip"), preview=True)
        return
    game = game_folder()
    try:
        current = installed_version(game)
        update = fetch_update(current) if current else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        update = None
    if update:
        show_update(game, current, update)
    else:
        try:
            launch_game(game)
        except OSError as exc:
            from tkinter import messagebox
            messagebox.showerror("Lopilol Traduções", str(exc))


if __name__ == "__main__":
    main()
