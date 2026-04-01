import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors, Fonts


class FigureInputDialog(BaseModal):
    """
    Componente Modal: Formulário para inserção de imagem.
    Facilita a inclusão da tag grafica configurando automaticamente a busca pelo arquivo,
    legenda, rótulo (label) e a escala percentual de ocupação na tela.
    """

    def __init__(self, master_app):
        super().__init__(master_app, "Inserir Figura", 480, 350)

        # Cabeçalho
        ctk.CTkLabel(self.border_frame, text="Configurar Figura", font=Fonts.UI_TITLE).pack(pady=(20, 15))

        # ==========================================
        # FORMULÁRIO DE CONFIGURAÇÃO (GRID LAYOUT)
        # ==========================================
        form_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=30)

        # Campo: Seleção de Arquivo
        file_label = ctk.CTkLabel(form_frame, text="Arquivo:", width=80, anchor="e", font=Fonts.UI_BOLD)
        file_label.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="e")

        self.filepath = ctk.CTkEntry(form_frame, placeholder_text="Selecione uma imagem...")
        self.filepath.grid(row=0, column=1, sticky="ew", pady=10)

        btn_browse = ctk.CTkButton(form_frame, text="Procurar", width=80, fg_color="transparent", border_width=1,
                                   text_color=Colors.TEXT_NORMAL, hover_color=Colors.BTN_HOVER,
                                   command=self._browse_file)
        btn_browse.grid(row=0, column=2, padx=(10, 0), pady=10)

        # Campo: Escala de Largura (Width)
        size_label = ctk.CTkLabel(form_frame, text="Escala (%):", width=80, anchor="e", font=Fonts.UI_BOLD)
        size_label.grid(row=1, column=0, padx=(0, 10), pady=10, sticky="e")

        self.width_val = ctk.CTkEntry(form_frame, placeholder_text="Porcentagem da tela preenchida")
        self.width_val.grid(row=1, column=1, sticky="ew", pady=10)

        # Campo: Legenda (Caption)
        cap_label = ctk.CTkLabel(form_frame, text="Legenda:", width=80, anchor="e", font=Fonts.UI_BOLD)
        cap_label.grid(row=2, column=0, padx=(0, 10), pady=10, sticky="e")

        self.caption = ctk.CTkEntry(form_frame, placeholder_text="Ex: Gráfico de dispersão")
        self.caption.grid(row=2, column=1, sticky="ew", pady=10)

        # Campo: Rótulo (Label) para referências cruzadas
        lbl_label = ctk.CTkLabel(form_frame, text="Label (fig:):", width=80, anchor="e", font=Fonts.UI_BOLD)
        lbl_label.grid(row=3, column=0, padx=(0, 10), pady=10, sticky="e")

        self.label = ctk.CTkEntry(form_frame, placeholder_text="nome_da_figura")
        self.label.grid(row=3, column=1, sticky="ew", pady=10)

        # Permite expansão dinâmica da coluna central
        form_frame.grid_columnconfigure(1, weight=1)

        # ==========================================
        # BOTÕES DE AÇÃO
        # ==========================================
        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(fill="x", padx=30, pady=(10, 30))

        ctk.CTkButton(btn_f, text="Cancelar", width=100, fg_color="transparent", border_width=1,
                      text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", expand=True,
                                                                                      anchor="e", padx=(0, 5))
        ctk.CTkButton(btn_f, text="✔ Inserir", width=120, fg_color=Colors.BTN_PRIMARY,
                      hover_color=Colors.BTN_PRIMARY_HOVER, command=self._on_ok).pack(side="right", expand=True,
                                                                                      anchor="w", padx=(5, 0))

    def _browse_file(self):
        """Abre o explorador de arquivos e valida se a imagem selecionada pertence ao diretório do projeto."""
        proj_dir = str(self.app.project_dir.resolve()) if self.app.project_dir else ""
        path = filedialog.askopenfilename(title="Selecione a Imagem", initialdir=proj_dir,
                                          filetypes=[("Imagens e PDFs", "*.png *.jpg *.jpeg *.pdf")])
        if path:
            try:
                rel_path = os.path.relpath(path, proj_dir)
                if rel_path.startswith("..") or os.path.isabs(rel_path):
                    messagebox.showerror("Aviso", "A imagem deve estar dentro da pasta do projeto.")
                    return
                self.filepath.delete(0, "end")
                self.filepath.insert(0, rel_path.replace("\\", "/"))
            except ValueError:
                messagebox.showerror("Erro", "O arquivo deve estar na mesma unidade de disco do projeto.")

    def _on_ok(self):
        """Finaliza a coleta de dados e os empacota na variável 'result' para o gerenciador pai."""
        if not self.filepath.get().strip():
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo de imagem.")
            return

        w_val = self.width_val.get().strip()
        if not w_val:
            w_val = "80"

        self.result = (self.filepath.get().strip(), w_val, self.caption.get().strip(),
                       f"fig:{self.label.get().strip()}")
        self._close_dialog()