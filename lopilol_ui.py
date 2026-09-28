"""Reusable Lopilol installer window. Game patching stays in patch_backend.py."""

import argparse
import importlib.util
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


HERE = Path(__file__).resolve().parent
INK = "#241335"
VIOLET = "#371454"
CORAL = "#fc6378"
PAPER = "#fff9fb"
MUTED = "#705e77"
BORDER = "#e9dae8"


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = ("title", "edition", "version", "default_game_dir", "folder_hint")
    missing = [key for key in required if not isinstance(data.get(key), str) or not data[key].strip()]
    if missing:
        raise ValueError("Configuração incompleta: " + ", ".join(missing))
    return data


def load_backend():
    path = HERE / "patch_backend.py"
    if not path.is_file():
        raise FileNotFoundError("Adicione patch_backend.py para habilitar as ações.")
    spec = importlib.util.spec_from_file_location("lopilol_patch_backend", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("install", "verify", "uninstall"):
        if not callable(getattr(module, name, None)):
            raise ValueError("O backend precisa de install, verify e uninstall.")
    return module


def label(parent, text, *, size=10, color=INK, weight="normal", bg=PAPER, **kwargs):
    return tk.Label(parent, text=text, font=("Segoe UI", size, weight), fg=color, bg=bg, **kwargs)


def build_window(config, preview=False, backend=None):
    root = tk.Tk()
    root.title("Lopilol Traduções — Instalador")
    root.geometry("780x615")
    root.minsize(700, 590)
    root.configure(bg=INK)

    header = tk.Frame(root, bg=INK)
    header.pack(fill="x", padx=35, pady=(27, 24))
    logo_path = HERE / "lopilol-logo.png"
    if logo_path.is_file():
        icon = tk.PhotoImage(file=str(logo_path))
        root.iconphoto(True, icon)
        root.icon_image = icon
        logo = icon.subsample(5)
        logo_label = tk.Label(header, image=logo, bg=INK)
        logo_label.image = logo
        logo_label.pack(side="left", padx=(0, 18))
    identity = tk.Frame(header, bg=INK)
    identity.pack(side="left", fill="y")
    label(identity, "Lopilol Traduções", size=23, color=PAPER, weight="bold", bg=INK).pack(anchor="w", pady=(6, 0))
    label(identity, "INSTALADOR DE PATCHES PT-BR", size=9, color="#e9c6e2", weight="bold", bg=INK).pack(anchor="w", pady=(2, 0))

    card = tk.Frame(root, bg=PAPER, relief="raised", borderwidth=3)
    card.pack(fill="both", expand=True, padx=35, pady=(0, 18))
    top = tk.Frame(card, bg=PAPER)
    top.pack(fill="x", padx=27, pady=(24, 0))
    badge = tk.Frame(top, bg="#f8eaf0", relief="raised", borderwidth=2)
    badge.pack(side="right", pady=3)
    label(badge, config["version"], size=9, weight="bold", color=VIOLET, bg="#f8eaf0").pack(padx=11, pady=6)
    label(top, config["title"], size=20, weight="bold").pack(anchor="w")
    label(card, config["edition"], size=11, color=MUTED, anchor="w").pack(fill="x", padx=27, pady=(1, 17))
    tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=27)

    label(card, "Pasta do jogo", size=11, weight="bold", anchor="w").pack(fill="x", padx=27, pady=(22, 6))
    folder = tk.StringVar(value=config["default_game_dir"])
    path_row = tk.Frame(card, bg=PAPER)
    path_row.pack(fill="x", padx=27)
    entry = tk.Entry(path_row, textvariable=folder, font=("Segoe UI", 11), fg=INK, bg="#ffffff", relief="sunken", borderwidth=2, highlightbackground=BORDER, highlightcolor=CORAL, highlightthickness=1)
    entry.pack(side="left", fill="x", expand=True, ipady=9)
    browse = tk.Button(path_row, text="Procurar…", command=lambda: folder.set(filedialog.askdirectory() or folder.get()), font=("Segoe UI", 10, "bold"), fg=VIOLET, bg="#f8eaf0", relief="raised", borderwidth=3, cursor="hand2", padx=15, pady=8)
    browse.pack(side="left", padx=(9, 0))
    label(card, config["folder_hint"], size=9, color=MUTED, anchor="w", wraplength=680, justify="left").pack(fill="x", padx=27, pady=(7, 0))

    status = tk.StringVar(value="Prévia visual. Nenhum arquivo será alterado." if preview else "Pronto para instalar. O patch confere a edição e cria backup.")
    status_box = tk.Frame(card, bg="#f5edf7", relief="sunken", borderwidth=2)
    status_box.pack(fill="x", padx=27, pady=(22, 18))
    label(status_box, "STATUS", size=9, weight="bold", color=VIOLET, bg="#f5edf7").pack(anchor="w", padx=13, pady=(10, 1))
    tk.Label(status_box, textvariable=status, font=("Segoe UI", 10), fg=INK, bg="#f5edf7", anchor="w", wraplength=650, justify="left").pack(fill="x", padx=13, pady=(0, 11))

    row = tk.Frame(card, bg=PAPER)
    row.pack(fill="x", padx=27)
    if not preview and backend is None:
        backend = load_backend()

    def run(name):
        action = getattr(backend, name)
        try:
            status.set(action(Path(folder.get())))
            messagebox.showinfo("Lopilol Traduções", status.get())
        except Exception as exc:
            status.set(str(exc))
            messagebox.showerror("Lopilol Traduções", status.get())

    actions = (("Instalar patch", "install", CORAL, PAPER), ("Verificar", "verify", "#eee1ee", VIOLET), ("Desinstalar", "uninstall", "#eee1ee", VIOLET))
    for title, method, bg, fg in actions:
        tk.Button(row, text=title, command=lambda method=method: run(method), state="disabled" if preview else "normal", font=("Segoe UI", 10, "bold"), fg=fg, bg=bg, disabledforeground=fg, relief="raised", borderwidth=3, cursor="hand2", padx=17, pady=11).pack(side="left", padx=(0, 8))
    label(card, "Projeto de fãs · Jogos e artes pertencem aos titulares.", size=9, color=MUTED, anchor="w").pack(fill="x", padx=27, pady=(16, 16))
    return root


def show_installer(config, backend):
    root = build_window(config, backend=backend)
    root.mainloop()

