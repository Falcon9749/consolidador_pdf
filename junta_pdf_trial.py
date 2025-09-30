# pip install PyPDF2 ttkbootstrap Pillow

import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import ttkbootstrap as tb
import json
import datetime
import uuid
import hashlib
import platform
import getpass

try:
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfFileMerger as PdfMerger
    from PyPDF2 import PdfFileReader as PdfReader
    from PyPDF2 import PdfFileWriter as PdfWriter

# ================== LOGGER ==================
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=30, encoding="utf-8")
handler.suffix = "%Y-%m-%d.log"
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

def excecao_nao_tratada(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Exceção não tratada", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = excecao_nao_tratada

def report_callback_exception(self, exc, val, tb_):
    erro = "".join(traceback.format_exception(exc, val, tb_))
    logger.error(f"Erro no Tkinter:\n{erro}")
tk.Tk.report_callback_exception = report_callback_exception
# ====================================================

LICENSE_TEXT = """
MIT License

Copyright (c) 2025 Gilnei Monteiro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# ================== CLASSE PRINCIPAL ==================
class PDFMergerApp:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("📝 PDF Merger - Trial/Ativação")
        self.root.geometry("720x820")
        self.pdf_files = []

        # Pasta padrão para licença/trial
        self.lic_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "PDFMergerApp")
        os.makedirs(self.lic_dir, exist_ok=True)
        self.lic_path = os.path.join(self.lic_dir, "license.json")

        # Inicializa trial/licença (cria arquivo se não existir)
        self.init_license()

        # CRIA a tela principal (widgets) — sempre cria para manter estrutura original
        self.app_frame = tb.Frame(root)
        self.create_app_widgets()
        self.app_frame.pack_forget()

        # Lê license.json (se houver)
        lic = self.read_license()

        # Se já ativado, abre direto o app principal
        if lic.get("activated", False):
            self.show_app()
            return

        # ---------------- Tela de Licença ----------------
        self.license_frame = tb.Frame(root)
        tb.Label(self.license_frame, text="📜 Licença / Trial", font=("Segoe UI", 18, "bold")).pack(pady=10)

        # Mostra a licença
        self.license_text = tk.Text(self.license_frame, wrap="word", height=10, font=("Segoe UI", 10))
        self.license_text.insert("1.0", LICENSE_TEXT)
        self.license_text.config(state="disabled")
        self.license_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # HWID
        hwid_frame = tb.Frame(self.license_frame)
        hwid_frame.pack(pady=5)
        tb.Label(hwid_frame, text="HWID da máquina:").pack(side=tk.LEFT)

        self.hwid_entry = tk.Entry(hwid_frame, width=40, fg="black", bg="#ffffff", font=("Segoe UI", 10))
        self.hwid_entry.pack(side=tk.LEFT, padx=5)

        # sempre preenche o HWID agora
        self.hwid_entry.delete(0, tk.END)
        self.hwid_entry.insert(0, self.get_hwid())
        self.hwid_entry.config(state="readonly", fg="black", bg="#ffffff")

        tb.Button(hwid_frame, text="📋 Copiar", command=self.copy_hwid).pack(side=tk.LEFT, padx=5)

        # Chave
        key_frame = tb.Frame(self.license_frame)
        key_frame.pack(pady=5)
        tb.Label(key_frame, text="Chave de ativação:").pack(side=tk.LEFT)
        self.key_entry = tb.Entry(key_frame, width=40)
        self.key_entry.pack(side=tk.LEFT, padx=5)
        tb.Button(key_frame, text="Ativar", bootstyle="success", command=self.validate_key).pack(side=tk.LEFT, padx=5)

        # Continuar trial
        self.trial_button = tb.Button(
            self.license_frame,
            text=f"Continuar Trial ({self.trial_days_left()} dias restantes)",
            bootstyle="warning", width=40,
            command=self.continue_trial
        )
        self.trial_button.pack(pady=15)

        # Botão sair
        tb.Button(self.license_frame, text="Sair", bootstyle="danger", width=10, command=self.root.quit).pack(pady=5)

        # Exibe tela
        self.license_frame.pack(fill=tk.BOTH, expand=True)

    # ================== Funções de Trial/License ==================
    def get_hwid(self):
        """
        Retorna um HWID consistente e único.
        Usa uuid.getnode(), mas garante que nunca retorna 0 ou vazio.
        """
        try:
            hwid = uuid.getnode()
            if hwid and hwid != 0:
                return str(hwid)
            else:
                raw = platform.node() + getpass.getuser() + sys.executable
                return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()
        except Exception as e:
            logger.error(f"Erro ao obter HWID: {e}")
            return hashlib.sha256(b"default-hwid").hexdigest()[:12].upper()

    def copy_hwid(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.hwid_entry.get())
            messagebox.showinfo("HWID", "HWID copiado para área de transferência!")
        except Exception as e:
            logger.error(f"Erro ao copiar HWID: {e}")
            messagebox.showerror("Erro", "Não foi possível copiar o HWID.")

    def init_license(self):
        if not os.path.exists(self.lic_path):
            expire = datetime.datetime.now() + datetime.timedelta(days=7)
            data = {"trial_expire": expire.isoformat(), "activated": False, "key": ""}
            with open(self.lic_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

    def read_license(self):
        try:
            with open(self.lic_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "trial_expire" not in data:
                    data["trial_expire"] = (datetime.datetime.now() + datetime.timedelta(days=7)).isoformat()
                if "activated" not in data:
                    data["activated"] = False
                if "key" not in data:
                    data["key"] = ""
                return data
        except Exception as e:
            logger.error(f"Erro lendo license.json: {e}")
            expire = datetime.datetime.now() + datetime.timedelta(days=7)
            data = {"trial_expire": expire.isoformat(), "activated": False, "key": ""}
            with open(self.lic_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return data

    def write_license(self, data):
        with open(self.lic_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def trial_days_left(self):
        data = self.read_license()
        try:
            expire = datetime.datetime.fromisoformat(data["trial_expire"])
        except Exception:
            expire = datetime.datetime.now() + datetime.timedelta(days=7)
            data["trial_expire"] = expire.isoformat()
            self.write_license(data)
        days_left = (expire - datetime.datetime.now()).days
        return max(days_left, 0)

    def continue_trial(self):
        if self.trial_days_left() <= 0:
            messagebox.showwarning("Trial Expirado", "O período de trial acabou. Insira uma chave para continuar.")
            return
        self.show_app()

    def validate_key(self):
        key = self.key_entry.get().strip()
        hwid = self.get_hwid()
        salt = "PDFMergerSecret2025"
        raw = hwid + salt
        expected_raw = hashlib.sha256(raw.encode()).hexdigest()
        expected_key = "-".join([expected_raw[i:i+5].upper() for i in range(0, 25, 5)])

        if key == expected_key:
            data = self.read_license()
            data["activated"] = True
            data["key"] = key
            self.write_license(data)
            messagebox.showinfo("Ativado", "Licença ativada com sucesso!")
            self.show_app()
        else:
            messagebox.showerror("Erro", "Chave inválida!")

    # ================== Tela Principal do App ==================
    def create_app_widgets(self):
        header = tb.Label(self.app_frame, text="📑 Organizador de PDFs", font=("Segoe UI", 18, "bold"), bootstyle="inverse-dark")
        header.pack(pady=10)

        list_frame = tb.Frame(self.app_frame, bootstyle="dark")
        list_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#2a2a2a", fg="white",
                                  selectbackground="#007fff", height=14)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = tb.Frame(self.app_frame)
        btn_frame.pack(pady=12)
        tb.Button(btn_frame, text="➕ Adicionar", bootstyle="info-outline", width=18, command=self.add_pdf).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="❌ Remover", bootstyle="danger-outline", width=14, command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="⬆️ Acima", bootstyle="secondary", width=10, command=self.move_up).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="⬇️ Abaixo", bootstyle="secondary", width=10, command=self.move_down).pack(side=tk.LEFT, padx=5)

        bottom_frame = tb.Frame(self.app_frame)
        bottom_frame.pack(pady=6)
        tb.Button(bottom_frame, text="📂 Criar PDF Final", bootstyle="success", width=20, command=self.merge_pdfs).pack(side=tk.LEFT, padx=8)
        tb.Button(bottom_frame, text="📖 Separar PDF", bootstyle="primary", width=18, command=self.split_pdf).pack(side=tk.LEFT, padx=8)
        tb.Button(bottom_frame, text="🗑 Limpar Lista", bootstyle="warning", width=18, command=self.clear_list).pack(side=tk.LEFT, padx=8)
        tb.Button(bottom_frame, text="Sair", bootstyle="danger", width=10, command=self.root.quit).pack(side=tk.LEFT, padx=8)

        self.status = tb.Label(self.app_frame, text="Nenhum arquivo selecionado", anchor="w", bootstyle="inverse-dark")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def show_app(self):
        try:
            if hasattr(self, "license_frame"):
                self.license_frame.pack_forget()
        except Exception as e:
            logger.error(f"Erro ao esconder license_frame: {e}")
        self.app_frame.pack(fill=tk.BOTH, expand=True)

    # ---------------- Funções PDF ----------------
    def add_pdf(self):
        paths = filedialog.askopenfilenames(title="Selecione PDFs", filetypes=[("Arquivos PDF", "*.pdf")])
        for p in paths:
            if os.path.isfile(p) and p not in self.pdf_files:
                self.pdf_files.append(p)
                self.listbox.insert(tk.END, os.path.basename(p))
        self.status.config(text=f"{len(self.pdf_files)} arquivo(s) na lista")

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        for idx in reversed(sel):
            del self.pdf_files[idx]
            self.listbox.delete(idx)
        self.status.config(text=f"{len(self.pdf_files)} arquivo(s) na lista")

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel: return
        for i in sel:
            if i == 0: continue
            self.pdf_files[i - 1], self.pdf_files[i] = self.pdf_files[i], self.pdf_files[i - 1]
        self.refresh(sel, offset=-1)

    def move_down(self):
        sel = list(self.listbox.curselection())[::-1]
        if not sel: return
        for i in sel:
            if i == len(self.pdf_files) - 1: continue
            self.pdf_files[i + 1], self.pdf_files[i] = self.pdf_files[i], self.pdf_files[i + 1]
        self.refresh(sel, offset=1)

    def refresh(self, sel, offset):
        self.listbox.delete(0, tk.END)
        for p in self.pdf_files:
            self.listbox.insert(tk.END, os.path.basename(p))
        for i in sel:
            self.listbox.selection_set(i + offset)

    def merge_pdfs(self):
        if not self.pdf_files:
            messagebox.showwarning("Aviso", "Nenhum PDF na lista.")
            return
        save_path = filedialog.asksaveasfilename(title="Salvar PDF final", defaultextension=".pdf", filetypes=[("Arquivo PDF", "*.pdf")])
        if not save_path:
            return
        merger = PdfMerger()
        for pdf in self.pdf_files:
            merger.append(pdf)
        merger.write(save_path)
        merger.close()
        messagebox.showinfo("Sucesso", f"PDF criado:\n{save_path}")
        self.status.config(text=f"PDF criado: {save_path}")

    def split_pdf(self):
        file_path = filedialog.askopenfilename(title="Selecione o PDF", filetypes=[("Arquivos PDF", "*.pdf")])
        if not file_path: return
        opcao = simpledialog.askinteger("Separar PDF","1-Todas\n2-Intervalo\n3-Páginas específicas")
        if opcao not in [1,2,3]: return
        save_dir = filedialog.askdirectory(title="Pasta de saída")
        if not save_dir: return
        reader = PdfReader(file_path)
        if opcao==1:
            for i, page in enumerate(reader.pages, start=1):
                writer=PdfWriter()
                writer.add_page(page)
                out_path=os.path.join(save_dir,f"pagina_{i}.pdf")
                with open(out_path,"wb") as f: writer.write(f)
        elif opcao==2:
            intervalo = simpledialog.askstring("Intervalo","Ex:2-5")
            start,end = map(int,intervalo.split("-"))
            writer=PdfWriter()
            for i in range(start-1,end): writer.add_page(reader.pages[i])
            out_path=os.path.join(save_dir,f"paginas_{start}_a_{end}.pdf")
            with open(out_path,"wb") as f: writer.write(f)
        elif opcao==3:
            paginas = simpledialog.askstring("Páginas","Ex:1,3,7")
            indices=[int(p.strip()) for p in paginas.split(",")]
            writer=PdfWriter()
            for p in indices:
                if 1<=p<=len(reader.pages): writer.add_page(reader.pages[p-1])
            out_path=os.path.join(save_dir,f"paginas_{'_'.join(map(str,indices))}.pdf")
            with open(out_path,"wb") as f: writer.write(f)
        messagebox.showinfo("Sucesso", f"PDF separado em:\n{save_dir}")
        self.status.config(text=f"PDF separado em {save_dir}")

    def clear_list(self):
        self.pdf_files.clear()
        self.listbox.delete(0, tk.END)
        self.status.config(text="Nenhum arquivo selecionado")

# ================== EXECUÇÃO ==================
if __name__ == "__main__":
    win = tb.Window(themename="darkly")
    PDFMergerApp(win)
    win.mainloop()
