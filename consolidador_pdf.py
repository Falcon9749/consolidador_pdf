#pip install pypdf
import os
import pypdf

os.chdir("C:\\caminha_da_pasta")

pdf_destino = pypdf.PdfWriter()

for arquivo in os.listdir():
    nome, extensao = arquivo.rsplit(".")
    if extensao.lower() == 'pdf':
        pdf = pypdf.PdfReader(arquivo)
        for pagina in pdf.pages:
            pdf_destino.add_page(pagina)

pdf_destino.write("Report-Consolidado.pdf")
