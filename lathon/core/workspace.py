import shutil
import zipfile
from tkinter import filedialog, messagebox
from pathlib import Path
import customtkinter as ctk
import tempfile
from lathon.ui.design import Colors
from lathon.ui.widgets.fixed_input import FixedInputDialog


class WorkspaceManager:
    """
    Gerencia as operações de disco rígido relativas à estrutura do Cofre (Root).
    Gerencia a lógica de criação, cópia, exclusão, importação de ZIPs e validação de pastas
    do ecossistema de Repositórios e Projetos do LaThon, aliviando o main_window.py de operações pesadas de I/O.
    """

    def __init__(self, app, router):
        self.app = app
        self.router = router

    def set_root_directory(self):
        """
        Primeira configuração do sistema.
        Define onde o cofre será alocado e atualiza a interface graficamente
        escondendo o peso do carregamento do editor por trás de um update visual prévio.
        """
        pasta = filedialog.askdirectory(title="Onde ficarão os seus Repositórios?")
        if pasta:
            root_dir = Path(pasta) / "LaThon_Repositories"
            root_dir.mkdir(exist_ok=True)
            self.app.config.set_root_path(str(root_dir))

            appearance = self.app.config.get_appearance()
            Colors.load_theme(appearance.get("color_theme", "black"))
            mode = appearance.get("mode", "Dark")
            ctk.set_appearance_mode(mode)

            # Centraliza e expande a janela dinamicamente com base na resolução do monitor
            w, h = 1200, 800
            x = int((self.app.winfo_screenwidth() / 2) - (w / 2))
            y = int((self.app.winfo_screenheight() / 2) - (h / 2))
            self.app.geometry(f"{w}x{h}+{x}+{y}")

            self.router.configure(fg_color=Colors.BG_MAIN)

            # Truque de Performance: Renderiza a tela leve de repositórios e força o Tkinter
            # a atualizar o frame visual imediatamente ANTES de criar os componentes pesados.
            self.router._render()
            self.app.update_idletasks()

            # Reconstrói a interface de edição em background
            if hasattr(self.app, 'main_frame'):
                self.app.main_frame.destroy()

            self.app.scroll_conf = {
                "scrollbar_button_color": Colors.SCROLL_BTN,
                "scrollbar_button_hover_color": Colors.SCROLL_HOVER
            }

            self.app._build_ui()
            self.app.editor.bind("<KeyRelease>", self.app._schedule_outline_update, add="+")

            layout_cfg = self.app.config.get_layout()
            self.app.preferences_manager.apply_font_config(layout_cfg.get("font_family"), layout_cfg.get("font_size"))
            self.app.editor.update_colors()

    # ==========================================
    # GERENCIAMENTO DE REPOSITÓRIOS (PASTAS PAI)
    # ==========================================
    def create_repository(self, root_path: Path):
        dialog = FixedInputDialog(text="Nome do novo Repositório:", title="Novo Repositório")
        nome = dialog.get_input()
        if nome:
            novo_repo = root_path / nome
            novo_repo.mkdir(exist_ok=True)
            self.router._render()

    def import_repository(self, root_path: Path):
        """Copia uma pasta externa para o Cofre, validando sua estrutura estrutural."""
        pasta = filedialog.askdirectory(title="Selecione a pasta do Repositório para importar")
        if pasta:
            src = Path(pasta)

            # Validação de Hierarquia: Um Repositório NÃO pode conter arquivos .tex diretamente em sua raiz.
            # Ele deve conter subpastas (Projetos), e são estas subpastas que abrigam os arquivos .tex.
            if any(src.glob('*.tex')):
                messagebox.showerror("Ação Incorreta",
                                     "Esta pasta possui arquivos .tex na raiz, o que significa que ela é um PROJETO, e não um Repositório.\n\nPara importar este projeto, entre em um Repositório primeiro.")
                return
            elif not any(src.rglob('*.tex')):
                messagebox.showerror("Importação Bloqueada",
                                     "A pasta selecionada não contém nenhum arquivo LaTeX (.tex) em seu interior.\n\nSelecione um repositório válido.")
                return

            dst = root_path / src.name
            if dst.exists():
                messagebox.showerror("Erro", "Já existe um repositório com esse nome no cofre.")
                return
            try:
                shutil.copytree(src, dst)
                self.router._render()
                messagebox.showinfo("Sucesso", f"Repositório '{src.name}' copiado para o seu cofre!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar repositório: {e}")

    def import_repo_zip(self, root_path: Path):
        """Extrai um arquivo ZIP, avalia se trata-se de um Repositório válido e move para o Cofre."""
        zip_path = filedialog.askopenfilename(title="Selecione o arquivo ZIP do Repositório",
                                              filetypes=[("Arquivos ZIP", "*.zip")])
        if zip_path:
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir)

                    # Trata casos onde o ZIP contém os arquivos soltos ou dentro de uma pasta raiz única
                    tmp_path = Path(tmp_dir)
                    items = list(tmp_path.iterdir())
                    repo_root = items[0] if len(items) == 1 and items[0].is_dir() else tmp_path

                    # Validação de Hierarquia de Repositório
                    if any(repo_root.glob('*.tex')):
                        messagebox.showerror("Ação Incorreta",
                                             "Este ZIP contém arquivos .tex na raiz, o que significa que é um PROJETO.\n\nPara importá-lo, entre em um Repositório primeiro.")
                        return
                    elif not any(repo_root.rglob('*.tex')):
                        messagebox.showerror("Importação Bloqueada",
                                             "Este ZIP não contém nenhum código LaTeX em seu interior.")
                        return

                    repo_name = Path(zip_path).stem
                    destino = root_path / repo_name

                    # Resolve conflito de nomes incrementando um contador "(1)", "(2)"...
                    counter = 1
                    while destino.exists():
                        destino = root_path / f"{repo_name} ({counter})"
                        counter += 1

                    shutil.move(str(repo_root), str(destino))

                self.router._render()
                messagebox.showinfo("Sucesso", f"Repositório '{destino.name}' importado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao extrair ZIP:\n{e}")

    # ==========================================
    # GERENCIAMENTO DE PROJETOS (SUBPASTAS COM CÓDIGO)
    # ==========================================
    def enter_repository(self, repo_path: Path):
        """Registra o repositório atual no histórico (Recentes) e renderiza a tela de Projetos."""
        self.app.config.add_workspace_to_history(str(repo_path))
        self.router._render()

    def force_workspace_selector(self):
        """Retorna manualmente à tela de Cofre (Raiz)."""
        self.app.config.clear_last_workspace()
        self.router._render()

    def delete_folder(self, path: Path, tipo_nome: str):
        if messagebox.askyesno(f"Excluir {tipo_nome}",
                               f"Tem certeza que deseja excluir o {tipo_nome.lower()} '{path.name}' permanentemente?\nISSO NÃO PODE SER DESFEITO!"):
            shutil.rmtree(path, ignore_errors=True)
            self.router._render()

    def rename_project(self, project_path: Path):
        dialog = FixedInputDialog(text="Novo nome para o projeto:", title="Renomear")
        novo_nome = dialog.get_input()
        if novo_nome:
            novo_caminho = project_path.parent / novo_nome
            if not novo_caminho.exists():
                project_path.rename(novo_caminho)
                self.router._render()
            else:
                messagebox.showerror("Erro", "Já existe um projeto com esse nome.")

    def create_new_project(self, ws_path: Path):
        """Cria a pasta do projeto e já injeta um arquivo main.tex base."""
        dialog = FixedInputDialog(text="Nome do novo projeto LaTeX:", title="Novo Projeto")
        nome = dialog.get_input()
        if nome:
            novo_proj = ws_path / nome
            if novo_proj.exists():
                messagebox.showerror("Erro", "Já existe um projeto com esse nome.")
                return
            novo_proj.mkdir(exist_ok=True)
            (novo_proj / "main.tex").write_text(
                "\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\n\\begin{document}\n\nOlá, LaThon!\n\n\\end{document}",
                encoding="utf-8")
            self.router._render()

    def duplicate_project(self, project_path: Path):
        dialog = FixedInputDialog(text="Nome da cópia do projeto:", title="Duplicar Projeto")
        novo_nome = dialog.get_input()
        if novo_nome:
            novo_caminho = project_path.parent / novo_nome
            if not novo_caminho.exists():
                try:
                    shutil.copytree(project_path, novo_caminho)
                    self.router._render()
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao duplicar: {e}")
            else:
                messagebox.showerror("Erro", "Já existe um projeto com esse nome.")

    def import_folder(self, ws_path: Path):
        """Importa uma pasta de projeto, validando se a mesma possui um .tex diretamente na sua raiz."""
        pasta = filedialog.askdirectory(title="Selecione a pasta do Projeto")
        if pasta:
            src = Path(pasta)

            # Validação de Hierarquia de Projeto
            if not any(src.glob('*.tex')):
                if any(src.rglob('*.tex')):
                    messagebox.showerror("Ação Incorreta",
                                         "Esta pasta não possui arquivos .tex na raiz, mas possui em subpastas. Isso indica que ela é um REPOSITÓRIO inteiro, e não um único projeto.\n\nVolte para a tela inicial para importar Repositórios.")
                else:
                    messagebox.showerror("Importação Bloqueada",
                                         "A pasta selecionada não é um projeto LaTeX válido.\n\nUm projeto deve conter pelo menos um arquivo .tex na sua raiz.")
                return

            dst = ws_path / src.name
            if dst.exists():
                messagebox.showerror("Erro", "Já existe um projeto com esse nome.")
                return
            try:
                shutil.copytree(src, dst)
                self.router._render()
                messagebox.showinfo("Sucesso", f"Projeto '{src.name}' importado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao importar pasta:\n{e}")

    def import_zip(self, ws_path: Path):
        """Extrai um arquivo ZIP, avalia se trata-se de um Projeto válido e move para o Repositório atual."""
        import tempfile
        zip_path = filedialog.askopenfilename(title="Selecione o arquivo ZIP do Projeto",
                                              filetypes=[("Arquivos ZIP", "*.zip")])
        if zip_path:
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(tmp_dir)

                    tmp_path = Path(tmp_dir)
                    items = list(tmp_path.iterdir())
                    proj_root = items[0] if len(items) == 1 and items[0].is_dir() else tmp_path

                    # Validação de Hierarquia de Projeto
                    if not any(proj_root.glob('*.tex')):
                        if any(proj_root.rglob('*.tex')):
                            messagebox.showerror("Ação Incorreta",
                                                 "Este ZIP contém um REPOSITÓRIO (pastas com projetos dentro), e não um projeto único.\n\nVolte para a tela inicial para importar Repositórios.")
                        else:
                            messagebox.showerror("Importação Bloqueada",
                                                 "O arquivo ZIP selecionado não é um projeto LaTeX válido.")
                        return

                    proj_name = Path(zip_path).stem
                    destino = ws_path / proj_name

                    counter = 1
                    while destino.exists():
                        destino = ws_path / f"{proj_name} ({counter})"
                        counter += 1

                    shutil.move(str(proj_root), str(destino))

                self.router._render()
                messagebox.showinfo("Sucesso", f"Projeto '{destino.name}' importado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao extrair ZIP:\n{e}")