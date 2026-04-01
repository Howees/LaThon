import os
import sys
import shutil
import subprocess
import queue
from threading import Thread
from pathlib import Path

# Garante que o caminho base seja o diretório físico correto,
APP_DIR = Path.cwd()
LATEX_NAMES = ["pdflatex", "pdflatex.exe"]


def find_latex_compiler():
    """
    Busca o executável do compilador priorizando a estrutura de pastas do MiKTeX Portátil.
    Gera scripts dinâmicos (.bat) e intercepta os logs do terminal para exibir o progresso.
    """
    possible_paths = [
        APP_DIR / "miktex" / "texmfs" / "install" / "miktex" / "bin" / "x64",
        APP_DIR / "miktex" / "texmfs" / "install" / "miktex" / "bin"
    ]

    for path in possible_paths:
        for name in LATEX_NAMES:
            compiler_path = path / name
            if compiler_path.exists():
                return str(compiler_path)

    # Fallback: Tenta encontrar o compilador nas variáveis de ambiente do SO
    for name in LATEX_NAMES:
        path = shutil.which(name)
        if path:
            return path

    return None


def _read_output(out, q):
    """Função auxiliar para ler o terminal sem travar o Python (evita Blocking I/O)."""
    for line in iter(out.readline, ''):
        q.put(line)
    out.close()


class CompilerThread(Thread):
    """
    Executa a compilação de forma assíncrona.
    Comunica-se com a thread principal da UI através de uma Queue (Fila),
    enviando mensagens de status e pacotes sendo baixados.
    """

    def __init__(self, project_dir: Path, tex_file_name: str, compiler_path: str, q: queue.Queue):
        super().__init__()
        self.project_dir = project_dir
        self.tex_file_name_no_ext = Path(tex_file_name).stem
        self.compiler_path = compiler_path
        self.queue = q
        self.process = None
        self.is_cancelled = False

    def cancel(self):
        """Interrompe a thread e força a finalização (kill) do processo do compilador no Windows."""
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
        """Envia mensagens de log para o painel do terminal na UI via Queue."""
        if not self.is_cancelled:
            self.queue.put(message)

    def run(self):
        """Monta o script de execução e inicia o processo de compilação encadeada."""
        bib_files_exist = any(self.project_dir.glob("*.bib"))

        # O parâmetro -synctex=1 é mandatório para gerar o arquivo .synctex.gz,
        # que permite a navegação bidirecional (PDF <-> Código) no editor.
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

        # Oculta a janela preta do CMD no Windows durante a compilação
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

            # Usa uma thread auxiliar apenas para ler as linhas sem travar
            local_queue = queue.Queue()
            reader_thread = Thread(target=_read_output, args=(self.process.stdout, local_queue))
            reader_thread.daemon = True
            reader_thread.start()

            download_message_sent = False

            while True:
                if self.is_cancelled:
                    break

                try:
                    # Espera no máximo 2 segundos por uma nova linha
                    line = local_queue.get(timeout=2.0)

                    if not line:
                        if not reader_thread.is_alive():
                            break
                        continue

                    stripped = line.strip()
                    if not stripped: continue

                    # INTERCEPTA APENAS O STATUS DE PROGRESSO
                    if stripped.startswith('"___STATUS'):
                        parts = stripped.replace('"', '').split(':')
                        if len(parts) >= 4:
                            msg = f">> [{parts[1]}/{parts[2]}] {parts[3]}"
                            self.log(msg)
                        continue

                except queue.Empty:
                    if self.process.poll() is None:
                        if not download_message_sent and not self.is_cancelled:
                            self.queue.put(("downloading_package", True))
                            download_message_sent = True
                    else:
                        break  # Processo já encerrou

            self.process.wait()

        except Exception as e:
            self.log(f"ERRO CRÍTICO no Python: {e}")
            if not self.is_cancelled:
                self.queue.put(("finished", False))
            return

        if not self.is_cancelled:
            # Validação simples de integridade do PDF gerado
            pdf_path = self.project_dir / Path(self.tex_file_name_no_ext).with_suffix(".pdf")
            success = pdf_path.exists() and pdf_path.stat().st_size > 0
            self.queue.put(("finished", success))