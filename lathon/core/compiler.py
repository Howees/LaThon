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

    def log(self, message):
        self.queue.put(message)

    def run(self):
        # 1. Monta o conteúdo do .bat
        # Usamos ECHO com códigos específicos para o Python identificar o passo
        bib_files_exist = any(self.project_dir.glob("*.bib"))

        if bib_files_exist:
            bat_content = f'''
                @echo off
                cd /d "{self.project_dir}"
                echo "___STATUS:1:4:Gerando estrutura inicial (PDFLaTeX)..."
                "{self.compiler_path}" -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:2:4:Processando bibliografia (BibTeX)..."
                bibtex "{self.tex_file_name_no_ext}"
                echo "___STATUS:3:4:Integrando referencias (PDFLaTeX)..."
                "{self.compiler_path}" -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:4:4:Finalizando documento (PDFLaTeX)..."
                "{self.compiler_path}" -interaction=nonstopmode "{self.tex_file_name_no_ext}"
            '''
        else:
            bat_content = f'''
                @echo off
                cd /d "{self.project_dir}"
                echo "___STATUS:1:2:Compilacao inicial..."
                "{self.compiler_path}" -interaction=nonstopmode "{self.tex_file_name_no_ext}"
                echo "___STATUS:2:2:Finalizando documento..."
                "{self.compiler_path}" -interaction=nonstopmode "{self.tex_file_name_no_ext}"
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

        # 2. Configurações para esconder a janela (Performance Máxima)
        startupinfo = None
        creationflags = 0

        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            # Executa o .bat
            p = subprocess.Popen(
                [str(runner_bat_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Erros também vão para o stdout para filtrarmos
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                startupinfo=startupinfo,
                creationflags=creationflags,
                bufsize=1
            )

            download_message_sent = False

            # --- LOOP DE LEITURA OTIMIZADO ---
            for line in iter(p.stdout.readline, ''):
                if not line: break
                stripped = line.strip()
                if not stripped: continue

                # 1. Detecta Marcadores de Status do nosso .bat
                if stripped.startswith('"___STATUS'):
                    # Formato esperado: "___STATUS:Passo:Total:Mensagem..."
                    parts = stripped.replace('"', '').split(':')
                    if len(parts) >= 4:
                        msg = f">> [{parts[1]}/{parts[2]}] {parts[3]}"
                        self.log(msg)
                    continue

                # 2. Detecta Erros Críticos do LaTeX (Começam com !)
                # Ex: ! LaTeX Error: File `article.cls' not found.
                if stripped.startswith('!'):
                    self.log(f"ERRO: {stripped[1:].strip()}")  # Remove o ! e mostra o erro
                    continue

                # 3. Detecta Erros Fatais genéricos
                if "Fatal error" in stripped:
                    self.log(f"ERRO FATAL: {stripped}")
                    continue

                # 4. Detecta Download de Pacotes (MiKTeX)
                # Isso é importante não filtrar, pois o usuário precisa saber por que está demorando
                if "installing package" in stripped.lower() and not download_message_sent:
                    self.queue.put(("downloading_package", True))
                    self.log(">> Baixando pacote necessário (isso pode demorar)...")
                    download_message_sent = True
                    continue

            p.stdout.close()
            p.wait()

        except Exception as e:
            self.log(f"ERRO CRÍTICO no Python: {e}")
            self.queue.put(("finished", False))
            return

        # Verifica o resultado final
        pdf_path = self.project_dir / Path(self.tex_file_name_no_ext).with_suffix(".pdf")

        # Verifica se o PDF existe e se foi modificado recentemente (opcional, mas bom)
        success = pdf_path.exists() and pdf_path.stat().st_size > 0
        self.queue.put(("finished", success))