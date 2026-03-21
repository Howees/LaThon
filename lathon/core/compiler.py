import os
import sys
import shutil
import subprocess
import queue
from threading import Thread
from pathlib import Path

APP_DIR = Path.cwd()
LATEX_NAMES = ["pdflatex", "pdflatex.exe"]


def find_latex_compiler():
    """Encontra o compilador LaTeX, priorizando versão portátil."""
    possible_paths = [
        APP_DIR / "miktex" / "texmfs" / "install" / "miktex" / "bin" / "x64",
        APP_DIR / "miktex" / "texmfs" / "install" / "miktex" / "bin"
    ]
    for path in possible_paths:
        for name in LATEX_NAMES:
            compiler_path = path / name
            if compiler_path.exists():
                return str(compiler_path)

    for name in LATEX_NAMES:
        path = shutil.which(name)
        if path:
            return path
    return None


class CompilerThread(Thread):
    def __init__(self, project_dir: Path, tex_file_name: str, compiler_path: str, q: queue.Queue):
        super().__init__()
        self.project_dir = project_dir
        self.tex_file_name_no_ext = Path(tex_file_name).stem
        self.compiler_path = compiler_path
        self.queue = q
        self.process = None
        self.is_cancelled = False

    def cancel(self):
        """Cancela a thread e mata o processo do compilador no Windows."""
        self.is_cancelled = True
        if self.process:
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                try:
                    self.process.kill()
                except:
                    pass

    def log(self, message):
        if not self.is_cancelled:
            self.queue.put(message)

    def run(self):
        bib_files_exist = any(self.project_dir.glob("*.bib"))

        # ADICIONADO: -synctex=1 para gerar o mapa de sincronização
        if bib_files_exist:
            bat_content = f'''
                @echo off
                cd /d "{self.project_dir}"
                echo "___STATUS:1:4:Gerando estrutura inicial (PDFLaTeX)..."
                "{self.compiler_path}" -synctex=1 -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:2:4:Processando bibliografia (BibTeX)..."
                bibtex "{self.tex_file_name_no_ext}"
                echo "___STATUS:3:4:Integrando referencias (PDFLaTeX)..."
                "{self.compiler_path}" -synctex=1 -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:4:4:Finalizando documento (PDFLaTeX)..."
                "{self.compiler_path}" -synctex=1 -interaction=nonstopmode "{self.tex_file_name_no_ext}"
            '''
        else:
            bat_content = f'''
                @echo off
                cd /d "{self.project_dir}"
                echo "___STATUS:1:2:Compilacao inicial..."
                "{self.compiler_path}" -synctex=1 -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:2:2:Finalizando documento..."
                "{self.compiler_path}" -synctex=1 -interaction=nonstopmode "{self.tex_file_name_no_ext}"
            '''

        runner_bat_path = self.project_dir / "run_compiler.bat"
        try:
            runner_bat_path.write_text(bat_content, encoding='utf-8')
        except Exception as e:
            self.log(f"ERRO: Não foi possível criar o script: {e}")
            self.queue.put(("finished", False))
            return

        env = os.environ.copy()
        miktex_bin_path = str(Path(self.compiler_path).parent)
        env["PATH"] = f"{miktex_bin_path};{env.get('PATH', '')}"

        startupinfo = None
        creationflags = 0

        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            self.process = subprocess.Popen(
                [str(runner_bat_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags,
                bufsize=1
            )

            download_message_sent = False

            for line in iter(self.process.stdout.readline, ''):
                if self.is_cancelled:
                    break

                if not line: break
                stripped = line.strip()
                if not stripped: continue

                if stripped.startswith('"___STATUS'):
                    parts = stripped.replace('"', '').split(':')
                    if len(parts) >= 4:
                        msg = f">> [{parts[1]}/{parts[2]}] {parts[3]}"
                        self.log(msg)
                    continue

                if stripped.startswith('!'):
                    self.log(f"ERRO: {stripped[1:].strip()}")
                    continue

                if "Fatal error" in stripped:
                    self.log(f"ERRO FATAL: {stripped}")
                    continue

                if "installing package" in stripped.lower() and not download_message_sent:
                    if not self.is_cancelled:
                        self.queue.put(("downloading_package", True))
                    self.log(">> Baixando pacote necessário (isso pode demorar)...")
                    download_message_sent = True
                    continue

            self.process.stdout.close()
            self.process.wait()

        except Exception as e:
            self.log(f"ERRO CRÍTICO no Python: {e}")
            if not self.is_cancelled:
                self.queue.put(("finished", False))
            return

        if not self.is_cancelled:
            pdf_path = self.project_dir / Path(self.tex_file_name_no_ext).with_suffix(".pdf")
            success = pdf_path.exists() and pdf_path.stat().st_size > 0
            self.queue.put(("finished", success))