"""
App desenvolvido por Gilnei Monteiro
Licença: MIT License
Copyright (c) 2025 Gilnei Monteiro
"""

# pip install ttkbootstrap PyPDF2

import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as tb

try:
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfFileMerger as PdfMerger
    from PyPDF2 import PdfFileReader as PdfReader
    from PyPDF2 import PdfFileWriter as PdfWriter


class PDFMergerApp:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("Organizador de PDFs")
        self.root.geometry("700x700")
        self.pdf_files = []

        # ---------------- Cabeçalho ----------------
        header = tb.Label(
            root,
            text="📑 Organizador de PDFs",
            font=("Segoe UI", 18, "bold"),
            bootstyle="inverse-dark"
        )
        header.pack(pady=10)

        # ---------------- Área de Lista ----------------
        list_frame = tb.Frame(root, bootstyle="dark")
        list_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 11),
            bg="#2a2a2a",
            fg="white",
            selectbackground="#007fff",
            height=14
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # ---------------- Botões Principais ----------------
        btn_frame = tb.Frame(root)
        btn_frame.pack(pady=12)

        tb.Button(btn_frame, text="➕ Adicionar", bootstyle="info-outline",
                  width=18, command=self.add_pdf).pack(side=tk.LEFT, padx=5)

        tb.Button(btn_frame, text="❌ Remover", bootstyle="danger-outline",
                  width=14, command=self.remove_selected).pack(side=tk.LEFT, padx=5)

        tb.Button(btn_frame, text="⬆️ Acima", bootstyle="secondary",
                  width=10, command=self.move_up).pack(side=tk.LEFT, padx=5)

        tb.Button(btn_frame, text="⬇️ Abaixo", bootstyle="secondary",
                  width=10, command=self.move_down).pack(side=tk.LEFT, padx=5)

        # ---------------- Botões Inferiores ----------------
        bottom_frame = tb.Frame(root)
        bottom_frame.pack(pady=6)

        tb.Button(bottom_frame, text="📂 Criar PDF Final", bootstyle="success",
                  width=20, command=self.merge_pdfs).pack(side=tk.LEFT, padx=8)

        tb.Button(bottom_frame, text="📖 Separar PDF", bootstyle="primary",
                  width=18, command=self.split_pdf).pack(side=tk.LEFT, padx=8)

        tb.Button(bottom_frame, text="🗑 Limpar Lista", bootstyle="warning",
                  width=18, command=self.clear_list).pack(side=tk.LEFT, padx=8)

        # Status bar
        self.status = tb.Label(root, text="Nenhum arquivo selecionado",
                               anchor="w", bootstyle="inverse-dark")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # Atalhos
        self.root.bind("<Delete>", lambda e: self.remove_selected())

    # --------------- Funções -----------------
    def add_pdf(self):
        paths = filedialog.askopenfilenames(
            title="Selecione PDFs",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        for p in paths:
            if os.path.isfile(p) and p not in self.pdf_files:
                self.pdf_files.append(p)
                self.listbox.insert(tk.END, os.path.basename(p))
        self.status.config(text=f"{len(self.pdf_files)} arquivo(s) na lista")

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        for idx in reversed(sel):
            self.listbox.delete(idx)
            del self.pdf_files[idx]
        self.status.config(text=f"{len(self.pdf_files)} arquivo(s) na lista")

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        for i in sel:
            if i == 0:
                continue
            self.pdf_files[i - 1], self.pdf_files[i] = self.pdf_files[i], self.pdf_files[i - 1]
        self.refresh(sel, offset=-1)

    def move_down(self):
        sel = list(self.listbox.curselection())[::-1]
        if not sel:
            return
        for i in sel:
            if i == len(self.pdf_files) - 1:
                continue
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

        save_path = filedialog.asksaveasfilename(
            title="Salvar PDF final",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")]
        )
        if not save_path:
            return

        try:
            merger = PdfMerger()
            for pdf in self.pdf_files:
                merger.append(pdf)
            merger.write(save_path)
            merger.close()
            messagebox.showinfo("Sucesso", f"PDF criado com sucesso:\n{save_path}")
            self.status.config(text=f"PDF criado: {save_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao mesclar PDFs:\n{e}")

    def split_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o PDF para separar",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not file_path:
            return

        # Escolha da opção
        opcao = simpledialog.askinteger(
            "Separar PDF",
            "Escolha a opção:\n\n1 - Todas as páginas\n2 - Intervalo (ex: 2-5)\n3 - Páginas específicas (ex: 1,3,7)"
        )
        if opcao not in [1, 2, 3]:
            return

        save_dir = filedialog.askdirectory(title="Selecione a pasta de saída")
        if not save_dir:
            return

        try:
            reader = PdfReader(file_path)

            if opcao == 1:  # Todas as páginas
                for i, page in enumerate(reader.pages, start=1):
                    writer = PdfWriter()
                    writer.add_page(page)
                    out_path = os.path.join(save_dir, f"pagina_{i}.pdf")
                    with open(out_path, "wb") as f:
                        writer.write(f)

            elif opcao == 2:  # Intervalo
                intervalo = simpledialog.askstring("Intervalo", "Digite o intervalo (ex: 2-5):")
                if not intervalo or "-" not in intervalo:
                    messagebox.showwarning("Aviso", "Intervalo inválido.")
                    return
                start, end = map(int, intervalo.split("-"))
                if start < 1 or end > len(reader.pages) or start > end:
                    messagebox.showwarning("Aviso", "Intervalo fora do limite.")
                    return

                writer = PdfWriter()
                for i in range(start-1, end):
                    writer.add_page(reader.pages[i])
                out_path = os.path.join(save_dir, f"paginas_{start}_a_{end}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)

            elif opcao == 3:  # Páginas específicas
                paginas = simpledialog.askstring("Páginas", "Digite as páginas separadas por vírgula (ex: 1,3,7):")
                if not paginas:
                    return
                try:
                    indices = [int(p.strip()) for p in paginas.split(",")]
                except ValueError:
                    messagebox.showwarning("Aviso", "Formato inválido.")
                    return

                writer = PdfWriter()
                for p in indices:
                    if 1 <= p <= len(reader.pages):
                        writer.add_page(reader.pages[p-1])
                out_path = os.path.join(save_dir, f"paginas_{'_'.join(map(str, indices))}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)

            messagebox.showinfo("Sucesso", f"PDF separado em:\n{save_dir}")
            self.status.config(text=f"PDF separado em {save_dir}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao separar PDF:\n{e}")

    def clear_list(self):
        if not self.pdf_files:
            return
        if messagebox.askyesno("Confirmação", "Limpar todos os arquivos da lista?"):
            self.pdf_files.clear()
            self.listbox.delete(0, tk.END)
            self.status.config(text="Nenhum arquivo selecionado")


if __name__ == "__main__":
    app = tb.Window(themename="darkly")
    PDFMergerApp(app)
    app.mainloop()
