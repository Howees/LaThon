import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal
from lathon.ui.design import Colors, Fonts


class FormulaInputDialog(BaseModal):
    """
    Componente Modal: Construtor interativo de Fórmulas Matemáticas.
    Disponibiliza uma interface com abas categorizadas (Matrizes, Operadores, Gregas, etc)
    e botões que inserem os respectivos snippets no minieditor de pré-visualização.
    """

    def __init__(self, master_app):
        super().__init__(master_app, "Construtor de Fórmulas", 650, 500)
        self.minsize(580, 450)

        self.border_frame.grid_rowconfigure(1, weight=1)
        self.border_frame.grid_columnconfigure(0, weight=1)

        # ==========================================
        # MODO DE EXIBIÇÃO (BLOCK VS INLINE)
        # ==========================================
        top_bar = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))

        self.display_mode = ctk.StringVar(value="block")
        ctk.CTkRadioButton(top_bar, text="Bloco Numerado (Equação)", variable=self.display_mode, value="block",
                           font=Fonts.UI_BOLD).pack(side="left", padx=10)
        ctk.CTkRadioButton(top_bar, text="Na mesma linha ($...$)", variable=self.display_mode, value="inline",
                           font=Fonts.UI_BOLD).pack(side="left", padx=10)

        # ==========================================
        # EDITOR DE PRÉVIA
        # ==========================================
        self.editor = ctk.CTkTextbox(self.border_frame, font=("Consolas", 16), height=100,
                                     fg_color=Colors.BG_MAIN, border_width=1, border_color=Colors.BORDER)
        self.editor.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)

        self.placeholder_text = "% Monte sua fórmula aqui...\n"
        self.editor.insert("1.0", self.placeholder_text)
        self.editor.bind("<FocusIn>", self._clear_placeholder)

        # ==========================================
        # PAINEL DE ABAS COM SNIPPETS
        # ==========================================
        self.tabs = ctk.CTkTabview(
            self.border_frame,
            height=200,
            fg_color=Colors.BG_MAIN,  # fundo geral
            segmented_button_fg_color=Colors.BG_MAIN,
            segmented_button_selected_color=Colors.BTN_PRIMARY,
            segmented_button_selected_hover_color=Colors.BTN_PRIMARY_HOVER,
            segmented_button_unselected_color=Colors.BG_MAIN,
            text_color=Colors.TEXT_NORMAL
        )
        self.tabs.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        self._build_grid(self.tabs.add("Estruturas"),
                         [("Fração (a/b)", "\\frac{a}{b}"), ("Raiz (√)", "\\sqrt{x}"),
                          ("Raiz-N", "\\sqrt[n]{x}"), ("Sobrescrito (x²)", "x^{a}"),
                          ("Subscrito (x₂)", "x_{a}"), ("Binomial", "\\binom{n}{k}"),
                          ("Vetor", "\\vec{v}"), ("Valor Absoluto", "|x|")])

        self._build_grid(self.tabs.add("Matrizes"),
                         [("Matriz ( )",
                           "\\begin{pmatrix}\n\ta & b & c \\\\\n\td & e & f \\\\\n\tg & h & i\n\\end{pmatrix}"),
                          ("Matriz [ ]",
                           "\\begin{bmatrix}\n\ta & b & c \\\\\n\td & e & f \\\\\n\tg & h & i\n\\end{bmatrix}"),
                          ("Determinante | |",
                           "\\begin{vmatrix}\n\ta & b & c \\\\\n\td & e & f \\\\\n\tg & h & i\n\\end{vmatrix}"),
                          ("Sistema / Casos",
                           "f(x) = \\begin{cases}\n\t1 & \\text{se } x > 0 \\\\\n\t0 & \\text{caso contrário}\n\\end{cases}")])

        self._build_grid(self.tabs.add("Operadores"),
                         [("Integral (∫)", "\\int_{a}^{b}"), ("Somatório (∑)", "\\sum_{i=1}^{n}"),
                          ("Limite (lim)", "\\lim_{x \\to \\infty}"), ("Infinito (∞)", "\\infty"),
                          ("Produtório (∏)", "\\prod_{i=1}^{n}"), ("Derivada (∂)", "\\frac{\\partial y}{\\partial x}")])

        self._build_grid(self.tabs.add("Lógica"),
                         [("Pertence (∈)", "\\in"), ("Não Pertence (∉)", "\\notin"),
                          ("Contém (⊂)", "\\subset"), ("União (∪)", "\\cup"),
                          ("Interseção (∩)", "\\cap"), ("Vazio (∅)", "\\emptyset"),
                          ("Para Todo (∀)", "\\forall"), ("Existe (∃)", "\\exists")])

        self._build_grid(self.tabs.add("Gregas"),
                         [("α (Alpha)", "\\alpha"), ("β (Beta)", "\\beta"), ("γ (Gamma)", "\\gamma"),
                          ("δ (Delta)", "\\delta"), ("ε (Epsilon)", "\\epsilon"), ("θ (Theta)", "\\theta"),
                          ("π (Pi)", "\\pi"), ("σ (Sigma)", "\\sigma"), ("ω (Omega)", "\\omega"),
                          ("Δ (Maiús)", "\\Delta"), ("Ω (Maiús)", "\\Omega"), ("Σ (Maiús)", "\\Sigma")])

        self._build_grid(self.tabs.add("Símbolos"),
                         [("± (Mais/Menos)", "\\pm"), ("× (Vezes)", "\\times"), ("÷ (Divisão)", "\\div"),
                          ("≈ (Aprox)", "\\approx"), ("≠ (Diferente)", "\\neq"), ("≤ (Menor Igual)", "\\leq"),
                          ("≥ (Maior Igual)", "\\geq"), ("→ (Seta Dir)", "\\rightarrow"),
                          ("← (Seta Esq)", "\\leftarrow")])

        # ==========================================
        # BOTÕES DE AÇÃO
        # ==========================================
        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.grid(row=3, column=0, sticky="e", padx=15, pady=(0, 15))

        ctk.CTkButton(btn_f, text="Cancelar", width=100, fg_color="transparent", border_width=1,
                      text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="✔ Inserir", width=140, fg_color=Colors.BTN_PRIMARY,
                      hover_color=Colors.BTN_PRIMARY_HOVER, command=self._on_ok).pack(side="left", padx=5)

    def _clear_placeholder(self, event=None):
        """Remove o texto indicativo ao primeiro clique do usuário."""
        content = self.editor.get("1.0", "end-1c")
        if content == self.placeholder_text.strip() or content == self.placeholder_text:
            self.editor.delete("1.0", "end")

    def _build_grid(self, parent_tab, button_data):
        """Monta dinamicamente a grade de botões (4 colunas) dentro da aba especificada."""
        row, col = 0, 0
        for label, snippet in button_data:
            btn = ctk.CTkButton(parent_tab, text=label, height=35, fg_color=Colors.BG_MAIN,
                                hover_color=Colors.BTN_HOVER, text_color=Colors.TEXT_NORMAL, font=Fonts.UI,
                                command=lambda s=snippet: self._insert_snippet(s))
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            parent_tab.grid_columnconfigure(col, weight=1)

            col += 1
            if col >= 4:
                col, row = 0, row + 1

    def _insert_snippet(self, snippet):
        """Insere o código LaTeX do botão clicado na área de edição."""
        self._clear_placeholder()
        self.editor.insert("insert", snippet + " ")
        self.editor.focus_set()

    def _on_ok(self):
        """Extrai o código final e finaliza o modal para inserção no documento principal."""
        raw_text = self.editor.get("1.0", "end-1c").strip()
        if raw_text == self.placeholder_text.strip() or not raw_text:
            self._close_dialog()
            return

        self.result = (self.display_mode.get(), raw_text)
        self._close_dialog()