import shutil
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox


class ProjectExporter:
    """Módulo responsável exclusivamente por empacotar e salvar os arquivos finais."""

    @staticmethod
    def export_pdf(project_dir, active_file):
        if not project_dir: return
        main_file = next((f for f in list(project_dir.rglob("*.tex")) if f.name.lower() in ("main.tex", "root.tex")),
                         active_file)
        if not main_file: return

        pdf_path = project_dir / main_file.with_suffix(".pdf").name
        if not pdf_path.exists():
            messagebox.showwarning("Aviso", "Compile o projeto primeiro para gerar o PDF.")
            return

        dest = filedialog.asksaveasfilename(title="Exportar PDF", initialfile=pdf_path.name, defaultextension=".pdf",
                                            filetypes=[("PDF", "*.pdf")])
        if dest:
            try:
                shutil.copy2(str(pdf_path), dest)
                messagebox.showinfo("Sucesso", "PDF Exportado com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    @staticmethod
    def export_zip(project_dir):
        if not project_dir: return
        dest = filedialog.asksaveasfilename(title="Exportar ZIP", initialfile=f"{project_dir.name}.zip",
                                            defaultextension=".zip", filetypes=[("ZIP", "*.zip")])
        if dest:
            try:
                with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in project_dir.rglob('*'):
                        if f.resolve() == Path(dest).resolve(): continue
                        if f.suffix in {".aux", ".log", ".out", ".bbl",
                                        ".blg"} or f.name == "run_compiler.bat": continue
                        zf.write(f, f.relative_to(project_dir))
                messagebox.showinfo("Sucesso", "Projeto ZIP Exportado com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", str(e))