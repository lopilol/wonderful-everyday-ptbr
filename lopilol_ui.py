"""Reusable Windows-style patch wizard; patch operations remain in the backend."""

import argparse
import importlib.util
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = Path(__file__).resolve().parent
GRAY = "#f0f0f0"
FONT = ("Tahoma", 8)


def load_config(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("title", "edition", "version", "default_game_dir", "folder_hint"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError("Configuração incompleta: " + key)
    return data


class InstallerWizard:
    def __init__(self, config, preview=False, backend=None):
        self.config, self.preview, self.backend = config, preview, backend
        self.root = tk.Tk()
        self.root.title("Instalação — Lopilol Traduções — " + config["title"])
        self.root.geometry("500x360")
        self.root.resizable(False, False)
        self.root.configure(bg=GRAY)
        self.root.option_add("*Font", FONT)
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        self.images = []
        self.icon = tk.PhotoImage(file=str(HERE / "logo-icon.png"))
        self.root.iconphoto(True, self.icon)
        self.logo = tk.PhotoImage(file=str(HERE / "logo-header.png"))
        self.images.extend((self.icon, self.logo))
        self.folder = tk.StringVar(value=config["default_game_dir"])
        self.action = tk.StringVar(value="install")
        self.page = "welcome"
        self.busy = False
        self.results = queue.Queue()
        self.details_visible = False
        self.screen = tk.Frame(self.root, bg=GRAY)
        self.screen.place(x=0, y=0, width=500, height=314)
        self.footer = tk.Frame(self.root, bg=GRAY)
        self.footer.place(x=0, y=314, width=500, height=46)
        ttk.Separator(self.footer, orient="horizontal").place(x=0, y=0, width=500)
        self.back = ttk.Button(self.footer, text="< Voltar", command=self.go_back)
        self.back.place(x=250, y=13, width=73, height=23)
        self.next = ttk.Button(self.footer, text="Próximo >", command=self.go_next)
        self.next.place(x=325, y=13, width=73, height=23)
        self.cancel = ttk.Button(self.footer, text="Cancelar", command=self.close)
        self.cancel.place(x=413, y=13, width=73, height=23)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.show("welcome")

    def text(self, parent, value, x, y, width, *, bold=False, size=8, bg=GRAY):
        widget = tk.Label(parent, text=value, bg=bg, fg="black", anchor="nw",
                          justify="left", wraplength=width, font=("Tahoma", size, "bold" if bold else "normal"))
        widget.place(x=x, y=y, width=width)
        return widget

    def header(self, title, subtitle):
        bar = tk.Frame(self.screen, bg="white")
        bar.place(x=0, y=0, width=500, height=62)
        tk.Label(bar, image=self.logo, bg="white").place(x=5, y=7, width=44, height=44)
        self.text(bar, "Lopilol", 52, 10, 97, size=16, bold=True, bg="white")
        self.text(bar, "TRADUÇÕES", 54, 37, 96, size=8, bg="white")
        self.text(bar, title, 157, 11, 327, bold=True, bg="white")
        self.text(bar, subtitle, 157, 29, 327, bg="white")
        ttk.Separator(self.screen).place(x=0, y=62, width=500)
        tk.Label(self.screen, text="Lopilol Traduções", fg="#888888", bg=GRAY, font=FONT).place(x=5, y=296)
        ttk.Separator(self.screen).place(x=103, y=304, width=383)

    def show(self, page):
        self.page = page
        for child in self.screen.winfo_children():
            child.destroy()
        self.back.configure(state="normal")
        self.next.configure(state="normal", text="Próximo >")
        self.cancel.configure(state="normal", text="Cancelar")
        if page == "welcome":
            self.welcome()
            self.back.place_forget()
        else:
            self.back.place(x=250, y=13, width=73, height=23)
            if page == "information":
                self.information()
            elif page == "folder":
                self.destination()
            elif page == "running":
                self.running()
            elif page == "done":
                self.finished()
        self.next.focus_set()

    def welcome(self):
        self.screen.configure(bg="white")
        self.cover = tk.PhotoImage(file=str(HERE / self.config.get("cover", "cover-panel.png")))
        tk.Label(self.screen, image=self.cover, bg="white", bd=0).place(x=0, y=0, width=164, height=314)
        self.text(self.screen, self.config["title"], 180, 17, 305, size=11, bold=True, bg="white")
        self.text(self.screen, "Bem-vindo ao instalador da tradução PT-BR de " + self.config["title"] + ".", 180, 72, 302, bg="white")
        self.text(self.screen, self.config["edition"] + "\n" + self.config["version"], 180, 120, 302, bg="white")
        self.text(self.screen, "Feche o jogo antes de continuar. O instalador confere os arquivos da edição e cria backups antes de aplicar o patch.", 180, 166, 302, bg="white")
        self.text(self.screen, "Clique em Próximo para continuar.", 180, 236, 302, bg="white")

    def information(self):
        self.screen.configure(bg=GRAY)
        self.header("Informações do patch", "Leia as instruções antes de continuar com a instalação.")
        self.text(self.screen, "Lopilol Traduções", 22, 77, 455)
        frame = tk.Frame(self.screen, bg=GRAY)
        frame.place(x=22, y=101, width=455, height=153)
        content = tk.Text(frame, wrap="word", font=FONT, bg="white", relief="sunken", bd=2)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=content.yview)
        content.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        content.pack(side="left", fill="both", expand=True)
        content.insert("1.0", (HERE / "LEIA-ME.txt").read_text(encoding="utf-8"))
        content.configure(state="disabled")
        self.text(self.screen, "Use a barra de rolagem para ler todas as instruções.", 22, 265, 455)

    def destination(self):
        self.screen.configure(bg=GRAY)
        self.header("Escolha o local da instalação", "Selecione a pasta do jogo original e a operação desejada.")
        self.text(self.screen, self.config["folder_hint"], 22, 77, 455)
        choices = tk.Frame(self.screen, bg=GRAY)
        choices.place(x=22, y=118, width=455, height=28)
        for i, (caption, value) in enumerate((("Instalar patch", "install"), ("Verificar", "verify"), ("Desinstalar", "uninstall"))):
            ttk.Radiobutton(choices, text=caption, variable=self.action, value=value,
                            command=self.update_action).place(x=i * 148, y=3)
        box = ttk.LabelFrame(self.screen, text="Pasta do jogo:")
        box.place(x=22, y=176, width=455, height=58)
        ttk.Entry(box, textvariable=self.folder).place(x=15, y=8, width=310, height=23)
        ttk.Button(box, text="Procurar...", command=self.browse).place(x=338, y=8, width=88, height=23)
        self.text(self.screen, "O jogo original é necessário. Nenhum arquivo será alterado até confirmar a operação.", 22, 250, 455)
        self.update_action()

    def update_action(self):
        self.next.configure(text={"install": "Instalar", "verify": "Verificar", "uninstall": "Desinstalar"}[self.action.get()])

    def browse(self):
        selected = filedialog.askdirectory(parent=self.root, initialdir=self.folder.get(), title="Selecione a pasta do jogo")
        if selected:
            self.folder.set(selected)

    def running(self):
        self.screen.configure(bg=GRAY)
        title = {"install": "Instalando", "verify": "Verificando", "uninstall": "Desinstalando"}[self.action.get()]
        self.header(title, "Por favor, aguarde enquanto o instalador conclui a operação.")
        self.status = tk.StringVar(value="Conferindo os arquivos e a edição do jogo...")
        tk.Label(self.screen, textvariable=self.status, bg=GRAY, fg="black", anchor="w", font=FONT).place(x=15, y=79, width=468)
        self.progress = ttk.Progressbar(self.screen, mode="indeterminate")
        self.progress.place(x=15, y=98, width=468, height=19)
        self.progress.start(14)
        self.details_toggle = ttk.Button(self.screen, text="Mostrar detalhes", command=self.toggle_details)
        self.details_toggle.place(x=15, y=125, width=110, height=23)
        self.details = tk.Text(self.screen, font=FONT, bg="white", wrap="word", relief="sunken", bd=2)
        self.details.insert("1.0", "Pasta: " + self.folder.get() + "\nOperação: " + self.action.get() + "\nAguarde a confirmação do resultado.")
        self.details.configure(state="disabled")
        self.details_visible = False
        for button in (self.back, self.next, self.cancel):
            button.configure(state="disabled")

    def toggle_details(self):
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.details.place(x=15, y=158, width=468, height=124)
        else:
            self.details.place_forget()
        self.details_toggle.configure(text="Ocultar detalhes" if self.details_visible else "Mostrar detalhes")

    def finished(self):
        self.screen.configure(bg=GRAY)
        self.header("Operação concluída" if self.success else "Não foi possível concluir", self.config["title"] + " — " + self.config["version"])
        self.text(self.screen, self.result_message, 22, 85, 455)
        self.text(self.screen, "Clique em Concluir para fechar o instalador." if self.success else "Clique em Voltar para conferir a pasta e tentar novamente.", 22, 251, 455)
        self.next.configure(text="Concluir")
        self.cancel.configure(state="disabled")
        if self.success:
            self.back.configure(state="disabled")

    def go_back(self):
        if self.busy:
            return
        previous = {"information": "welcome", "folder": "information", "done": "folder"}
        if self.page in previous:
            self.show(previous[self.page])

    def go_next(self):
        if self.busy:
            return
        if self.page == "welcome":
            self.show("information")
        elif self.page == "information":
            self.show("folder")
        elif self.page == "folder":
            if self.preview:
                self.show("running")
                self.status.set("Prévia visual — nenhum arquivo do jogo será alterado.")
                return
            if self.action.get() == "uninstall" and not messagebox.askyesno("Lopilol Traduções", "Remover o patch e restaurar os backups desta pasta?", parent=self.root):
                return
            game = Path(self.folder.get().strip())
            action = self.action.get()
            self.busy = True
            self.show("running")
            threading.Thread(target=self.worker, args=(action, game), daemon=True).start()
            self.root.after(100, self.poll)
        elif self.page == "done":
            self.root.destroy()

    def worker(self, action, game):
        try:
            result = getattr(self.backend, action)(game)
            self.results.put((True, result))
        except Exception as exc:
            self.results.put((False, str(exc)))

    def poll(self):
        try:
            self.success, self.result_message = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self.poll)
            return
        self.busy = False
        self.progress.stop()
        self.show("done")

    def close(self):
        if self.busy:
            return
        if self.page == "welcome" or self.page == "done" or messagebox.askyesno("Lopilol Traduções", "Sair do instalador?", parent=self.root):
            self.root.destroy()


def build_window(config, preview=False, backend=None):
    wizard = InstallerWizard(config, preview=preview, backend=backend)
    wizard.root.wizard = wizard
    return wizard.root


def show_installer(config, backend):
    build_window(config, backend=backend).mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--config", type=Path, default=HERE / "project.json")
    parser.add_argument("--page", choices=("welcome", "information", "folder", "running"), default="welcome")
    args = parser.parse_args()
    if not args.preview:
        raise SystemExit("Use --preview para visualizar o modelo sem alterar arquivos.")
    root = build_window(load_config(args.config), preview=True)
    root.wizard.show(args.page)
    root.mainloop()
