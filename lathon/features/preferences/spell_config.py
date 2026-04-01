import customtkinter as ctk
import tkinter as tk
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

AVAILABLE_LANGUAGES = {
    "pt": "Português", "en": "Inglês", "es": "Espanhol",
    "fr": "Francês", "de": "Alemão", "ru": "Russo", "ar": "Árabe"
}


class SpellConfigDialog(BaseModal):
    """
    Componente Modal: Configurações e Dicionário de Ortografia.
    Permite ativar/desativar idiomas e gerenciar o dicionário pessoal do usuário,
    prevenindo falso-positivos em jargões técnicos ou nomes próprios.
    """

    def __init__(self, master_app, spell_checker):
        super().__init__(master_app, "Configurações de Ortografia", 450, 520)
        self.spell_checker = spell_checker

        # ==========================================
        # 1. SELEÇÃO DE IDIOMAS ATIVOS
        # ==========================================
        ctk.CTkLabel(self.border_frame, text="Idiomas do Corretor", font=Fonts.UI_BOLD).pack(anchor="w", padx=30,
                                                                                             pady=(15, 0))

        f1 = ctk.CTkScrollableFrame(self.border_frame, height=120, fg_color="transparent")
        f1.pack(fill="x", padx=30, pady=0)

        cfg = self.app.config.get_spell()
        self.lang_vars = {}
        for code, name in AVAILABLE_LANGUAGES.items():
            var = ctk.StringVar(value="on" if code in cfg.get("enabled_languages", []) else "off")
            self.lang_vars[code] = var
            ctk.CTkCheckBox(f1, text=name, variable=var, onvalue="on", offvalue="off",
                            command=self._on_lang_change).pack(anchor="w", pady=2)

        ctk.CTkFrame(self.border_frame, height=1, fg_color=Colors.BORDER).pack(fill="x", padx=20, pady=10)

        # ==========================================
        # 2. GERENCIAMENTO DE DICIONÁRIO PESSOAL
        # ==========================================
        ctk.CTkLabel(self.border_frame, text="Dicionário Pessoal", font=Fonts.UI_BOLD).pack(anchor="w", padx=30,
                                                                                            pady=(0, 5))

        f2 = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f2.pack(fill="both", expand=True, padx=30, pady=(0, 10))

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = Colors.BG_PANEL[1] if is_dark else "#f0f0f0"
        fg_color = Colors.TEXT_NORMAL[1] if is_dark else Colors.TEXT_NORMAL[0]

        # Âncora Inferior: Inputs e Botões são inseridos no fundo da view para prevenir colapso visual
        btn_f = ctk.CTkFrame(f2, fg_color="transparent")
        btn_f.pack(side="bottom", fill="x")
        btn_f.grid_columnconfigure(0, weight=1)

        self.new_word_entry = ctk.CTkEntry(btn_f, placeholder_text="Nova palavra...", height=30)
        self.new_word_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        btn_add = ctk.CTkButton(btn_f, text="+", width=35, height=30, command=self._add_manual_word)
        btn_add.grid(row=0, column=1, padx=(0, 5))

        btn_remove = ctk.CTkButton(btn_f, text="Remover", fg_color=Colors.BTN_DANGER,
                                   hover_color=Colors.BTN_DANGER_HOVER, width=70, height=30, command=self._remove_word)
        btn_remove.grid(row=0, column=2)

        # Container Expansivo: Listbox das palavras já adicionadas pelo usuário
        list_frame = ctk.CTkFrame(f2, fg_color=bg_color, corner_radius=6, border_width=1, border_color=Colors.BORDER)
        list_frame.pack(side="top", fill="both", expand=True, pady=(0, 10))

        scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical")
        scrollbar.pack(side="right", fill="y", padx=2, pady=2)

        self.words_listbox = tk.Listbox(list_frame, bd=0, highlightthickness=0, bg=bg_color, fg=fg_color, font=Fonts.UI)
        self.words_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.words_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.words_listbox.yview)

        self._refresh_listbox()
        self._create_action_buttons("Fechar", self._close_dialog)

    # ==========================================
    # LÓGICA DE DADOS E EVENTOS
    # ==========================================
    def _on_lang_change(self):
        """Atualiza e reinicializa os pacotes de idioma do motor PySpellChecker na hora."""
        l = [c for c, v in self.lang_vars.items() if v.get() == "on"]
        self.app.config.update_spell(enabled_languages=l)
        self.spell_checker.initialize_checkers()
        self.spell_checker.apply_spell_check()

    def _remove_word(self):
        """Retira a permissão de uma palavra do dicionário pessoal e reanalisa o texto."""
        sel = self.words_listbox.curselection()
        if not sel: return
        w = self.words_listbox.get(sel[0])
        cfg = self.app.config.get_spell()
        if w in cfg["custom_words"]:
            cfg["custom_words"].remove(w)
            self.app.config.update_spell(custom_words=cfg["custom_words"])
            self._refresh_listbox()
            self.spell_checker.initialize_checkers()
            self.spell_checker.apply_spell_check()

    def _add_manual_word(self):
        """Adiciona uma nova exceção ortográfica diretamente pela interface da configuração."""
        w = self.new_word_entry.get().strip()
        cfg = self.app.config.get_spell()
        if w and w not in cfg["custom_words"]:
            self.spell_checker.add_to_personal_dict(w)
            self.new_word_entry.delete(0, "end")
            self._refresh_listbox()

    def _refresh_listbox(self):
        """Atualiza listbox"""
        self.words_listbox.delete(0, "end")
        cfg = self.app.config.get_spell()
        for w in sorted(cfg["custom_words"]):
            self.words_listbox.insert("end", w)