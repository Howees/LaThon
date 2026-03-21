import shutil
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox
from lathon.ui.widgets.fixed_input import FixedInputDialog

class WorkspaceManager:
    """
    Controller responsável por todas as operações de arquivos de Repositórios e Projetos.
    Retira essa responsabilidade de processamento pesado da Interface Gráfica (UI).
    """
    def __init__(self, app, router):
        self.app = app
        self.router = router  # Referência para a tela atualizar o render após a ação

    def set_root_directory(self):
        pasta = filedialog.askdirectory(title="Onde ficarão os seus Repositórios?")
        if pasta:
            root_dir = Path(pasta) / "LaThon_Repositories"
            root_dir.mkdir(exist_ok=True)
            self.app.config.set_root_path(str(root_dir))
            self.router._render()

    def create_repository(self, root_path: Path):
        dialog = FixedInputDialog(text="Nome do novo Repositório:", title="Novo Repositório")
        nome = dialog.get_input()
        if nome:
            novo_repo = root_path / nome
            novo_repo.mkdir(exist_ok=True)
            self.router._render()

    def import_repository(self, root_path: Path):
        pasta = filedialog.askdirectory(title="Selecione a pasta do Repositório para importar")
        if pasta:
            src = Path(pasta)
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

    def enter_repository(self, repo_path: Path):
        self.app.config.add_workspace_to_history(str(repo_path))
        self.router._render()

    def force_workspace_selector(self):
        self.app.config.clear_last_workspace()
        self.router._render()

    def delete_folder(self, path: Path, tipo_nome: str):
        if messagebox.askyesno(f"Excluir {tipo_nome}", f"Tem certeza que deseja excluir o {tipo_nome.lower()} '{path.name}' permanentemente?\nISSO NÃO PODE SER DESFEITO!"):
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
        dialog = FixedInputDialog(text="Nome do novo projeto LaTeX:", title="Novo Projeto")
        nome = dialog.get_input()
        if nome:
            novo_proj = ws_path / nome
            if novo_proj.exists():
                messagebox.showerror("Erro", "Já existe um projeto com esse nome.")
                return
            novo_proj.mkdir(exist_ok=True)
            (novo_proj / "main.tex").write_text("\\documentclass{article}\n\\usepackage[utf8]{inputenc}\n\n\\begin{document}\n\nOlá, LaThon!\n\n\\end{document}", encoding="utf-8")
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

    def import_zip(self, ws_path: Path):
        zip_path = filedialog.askopenfilename(title="Selecione o arquivo ZIP", filetypes=[("Arquivos ZIP", "*.zip")])
        if zip_path:
            nome_pasta = Path(zip_path).stem
            destino = ws_path / nome_pasta
            destino.mkdir(exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(destino)
                self.router._render()
                messagebox.showinfo("Sucesso", f"Projeto '{nome_pasta}' importado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao extrair ZIP:\n{e}")

    def import_folder(self, ws_path: Path):
        pasta = filedialog.askdirectory(title="Selecione a pasta do Projeto")
        if pasta:
            src = Path(pasta)
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