# pip install PyPDF2 ttkbootstrap Pillow

import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
import traceback
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import ttkbootstrap as tb

try:
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfFileMerger as PdfMerger
    from PyPDF2 import PdfFileReader as PdfReader
    from PyPDF2 import PdfFileWriter as PdfWriter

# ================== LOGGER DIÁRIO ==================
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
        self.root.title("Organizador de PDFs")
        self.root.geometry("700x800")
        self.pdf_files = []

        # ---------------- Área da Licença ----------------
        self.license_frame = tb.Frame(root)
        self.license_frame.pack(fill=tk.BOTH, expand=True)
        tb.Label(self.license_frame, text="📜 Licença MIT", font=("Segoe UI", 18, "bold")).pack(pady=10)
        txt = tk.Text(self.license_frame, wrap="word", font=("Segoe UI", 11))
        txt.insert("1.0", LICENSE_TEXT)
        txt.config(state="disabled")
        txt.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

        btn_frame = tb.Frame(self.license_frame)
        btn_frame.pack(pady=10)
        tb.Button(btn_frame, text="Aceitar e Continuar", bootstyle="success", width=18,
                  command=self.show_app).pack(side=tk.LEFT, padx=10)
        tb.Button(btn_frame, text="Sair", bootstyle="danger", width=10,
                  command=self.root.quit).pack(side=tk.LEFT, padx=10)

        # ---------------- Área do App ----------------
        self.app_frame = tb.Frame(root)
        self.create_app_widgets()
        # inicialmente escondido
        self.app_frame.pack_forget()

    # ---------------- Criar widgets do app ----------------
    def create_app_widgets(self):
        # Cabeçalho
        header = tb.Label(self.app_frame, text="📑 Organizador de PDFs", font=("Segoe UI", 18, "bold"), bootstyle="inverse-dark")
        header.pack(pady=10)

        # Lista
        list_frame = tb.Frame(self.app_frame, bootstyle="dark")
        list_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#2a2a2a", fg="white",
                                  selectbackground="#007fff", height=14)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Botões principais
        btn_frame = tb.Frame(self.app_frame)
        btn_frame.pack(pady=12)
        tb.Button(btn_frame, text="➕ Adicionar", bootstyle="info-outline", width=18, command=self.add_pdf).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="❌ Remover", bootstyle="danger-outline", width=14, command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="⬆️ Cima", bootstyle="secondary", width=10, command=self.move_up).pack(side=tk.LEFT, padx=5)
        tb.Button(btn_frame, text="⬇️ Baixo", bootstyle="secondary", width=10, command=self.move_down).pack(side=tk.LEFT, padx=5)

        # Botões inferiores
        bottom_frame = tb.Frame(self.app_frame)
        bottom_frame.pack(pady=6)
        tb.Button(bottom_frame, text="📂 Criar PDF Final", bootstyle="success", width=20, command=self.merge_pdfs).pack(side=tk.LEFT, padx=8)
        tb.Button(bottom_frame, text="📖 Separar PDF", bootstyle="primary", width=18, command=self.split_pdf).pack(side=tk.LEFT, padx=8)
        tb.Button(bottom_frame, text="🗑 Limpar Lista", bootstyle="warning", width=18, command=self.clear_list).pack(side=tk.LEFT, padx=8)
        tb.Button(btn_frame, text="Sair", bootstyle="danger", width=10, command=self.root.quit).pack(side=tk.LEFT, padx=10)
        
        # Status bar
        self.status = tb.Label(self.app_frame, text="Nenhum arquivo selecionado", anchor="w", bootstyle="inverse-dark")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------------- Mostrar App ----------------
    def show_app(self):
        self.license_frame.pack_forget()
        self.app_frame.pack(fill=tk.BOTH, expand=True)

    # ---------------- Funções do App ----------------
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
