import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal


class FormulaInputDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Construtor de Fórmulas", 580, 480)
        self.minsize(550, 420)

        self.border_frame.grid_rowconfigure(1, weight=1)
        self.border_frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        self.display_mode = ctk.StringVar(value="block")
        ctk.CTkRadioButton(top_bar, text="Bloco Numerado (Equação)", variable=self.display_mode, value="block",
                           font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkRadioButton(top_bar, text="Na mesma linha ($...$)", variable=self.display_mode, value="inline",
                           font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

        self.editor = ctk.CTkTextbox(self.border_frame, font=("Consolas", 16), height=100,
                                     fg_color=("gray95", "#1e1e1e"), border_width=1, border_color=("gray70", "#454545"))
        self.editor.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.editor.insert("1.0", "% Monte sua fórmula aqui...\n")

        self.tabs = ctk.CTkTabview(self.border_frame, height=180)
        self.tabs.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        self._build_grid(self.tabs.add("Estruturas"),
                         [("Fração (a/b)", "\\frac{a}{b}"), ("Raiz (√)", "\\sqrt{x}"), ("Raiz-N", "\\sqrt[n]{x}"),
                          ("Sobrescrito (x²)", "x^{a}"), ("Subscrito (x₂)", "x_{a}"),
                          ("Matriz 2x2", "\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}")])
        self._build_grid(self.tabs.add("Operadores"),
                         [("Integral (∫)", "\\int_{a}^{b}"), ("Somatório (∑)", "\\sum_{i=1}^{n}"),
                          ("Limite (lim)", "\\lim_{x \\to \\infty}"), ("Infinito (∞)", "\\infty"),
                          ("Produtório (∏)", "\\prod_{i=1}^{n}"), ("Derivada (∂)", "\\frac{\\partial y}{\\partial x}")])
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

        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.grid(row=3, column=0, sticky="e", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_f, text="Cancelar", width=100, fg_color="transparent", border_width=1,
                      text_color=("black", "white"), command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="✔ Inserir", width=140, fg_color="#238636", hover_color="#2ea043",
                      command=self._on_ok).pack(side="left", padx=5)

    def _build_grid(self, parent_tab, button_data):
        row, col = 0, 0
        for label, snippet in button_data:
            btn = ctk.CTkButton(parent_tab, text=label, height=35, fg_color=("gray85", "#333333"),
                                hover_color=("gray75", "#454545"), text_color=("black", "white"), font=("Segoe UI", 12),
                                command=lambda s=snippet: self._insert_snippet(s))
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            parent_tab.grid_columnconfigure(col, weight=1)
            col += 1
            if col >= 4: col, row = 0, row + 1

    def _insert_snippet(self, snippet):
        self.editor.insert("insert", snippet + " ")
        self.editor.focus_set()

    def _on_ok(self):
        raw_text = self.editor.get("1.0", "end-1c").replace("% Monte sua fórmula aqui...", "").strip()
        self.result = (self.display_mode.get(), raw_text)
        self._close_dialog()