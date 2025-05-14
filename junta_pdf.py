import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfMerger

class PDFMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Juntar PDFs Personalizado")
        self.pdf_files = []

        self.label = tk.Label(root, text="Arquivos selecionados:", font=("Arial", 12))
        self.label.pack(pady=5)

        self.listbox = tk.Listbox(root, width=60)
        self.listbox.pack(pady=5)

        self.add_button = tk.Button(root, text="Adicionar PDF", command=self.add_pdf)
        self.add_button.pack(pady=5)

        self.finalize_button = tk.Button(root, text="Finalizar e Criar PDF", command=self.merge_pdfs)
        self.finalize_button.pack(pady=5)

    def add_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("Arquivos PDF", "*.pdf")])
        if file_path:
            self.pdf_files.append(file_path)
            self.listbox.insert(tk.END, file_path.split("/")[-1])  # Mostra apenas o nome do arquivo

    def merge_pdfs(self):
        if not self.pdf_files:
            messagebox.showwarning("Aviso", "Nenhum PDF foi adicionado.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Arquivo PDF", "*.pdf")])
        if not output_path:
            return

        merger = PdfMerger()
        try:
            for pdf in self.pdf_files:
                merger.append(pdf)
            merger.write(output_path)
            merger.close()
            messagebox.showinfo("Sucesso", f"PDF criado com sucesso em:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar PDF: {e}")

# Executar o app
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMergerApp(root)
    root.mainloop()
