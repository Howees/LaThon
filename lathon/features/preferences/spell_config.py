import customtkinter as ctk
import tkinter as tk
from lathon.ui.widgets.base_modal import BaseModal

AVAILABLE_LANGUAGES = {"pt": "Português", "en": "Inglês", "es": "Espanhol", "fr": "Francês", "de": "Alemão",
                       "ru": "Russo", "ar": "Árabe"}


class SpellConfigDialog(BaseModal):
    def __init__(self, master_app, spell_checker):
        super().__init__(master_app, "Configurações de Ortografia", 450, 480)
        self.spell_checker = spell_checker

        ctk.CTkLabel(self.border_frame, text="Idiomas do Corretor", font=("Segoe UI", 12, "bold")).pack(anchor="w",
                                                                                                        padx=30,
                                                                                                        pady=(20, 0))
        f1 = ctk.CTkScrollableFrame(self.border_frame, height=120, fg_color="transparent")
        f1.pack(fill="x", padx=30, pady=5)

        cfg = self.app.config.get_spell()
        self.lang_vars = {}
        for c, n in AVAILABLE_LANGUAGES.items():
            var = ctk.StringVar(value="on" if c in cfg.get("enabled_languages", []) else "off")
            self.lang_vars[c] = var
            ctk.CTkCheckBox(f1, text=n, variable=var, onvalue="on", offvalue="off", command=self._on_lang_change).pack(
                anchor="w", pady=2)

        ctk.CTkFrame(self.border_frame, height=2, fg_color=("gray80", "#333333")).pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.border_frame, text="Dicionário Pessoal", font=("Segoe UI", 12, "bold")).pack(anchor="w",
                                                                                                       padx=30)

        f2 = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f2.pack(fill="both", expand=True, padx=30, pady=5)

        is_dark = ctk.get_appearance_mode() == "Dark"
        self.words_listbox = tk.Listbox(f2, bd=0, highlightthickness=0, bg="#1e1e1e" if is_dark else "#f0f0f0",
                                        fg="white" if is_dark else "black", font=("Segoe UI", 11))
        self.words_listbox.pack(fill="both", expand=True, pady=5)
        self._refresh_listbox()

        btn_f = ctk.CTkFrame(f2, fg_color="transparent")
        btn_f.pack(fill="x", pady=5)
        self.new_word_entry = ctk.CTkEntry(btn_f, placeholder_text="Nova palavra...")
        self.new_word_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_f, text="+", width=30, command=self._add_manual_word).pack(side="left")
        ctk.CTkButton(btn_f, text="Remover", fg_color="#cf222e", hover_color="#8b0000", width=80,
                      command=self._remove_word).pack(side="right", padx=(5, 0))

        # Como o BaseModal exige um botão de fechar, vamos adicionar um.
        self._create_action_buttons("Fechar", self._close_dialog)

    def _on_lang_change(self):
        l = [c for c, v in self.lang_vars.items() if v.get() == "on"]
        self.app.config.update_spell(enabled_languages=l)
        self.spell_checker.initialize_checkers()
        self.spell_checker.apply_spell_check()

    def _remove_word(self):
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
        w = self.new_word_entry.get().strip()
        cfg = self.app.config.get_spell()
        if w and w not in cfg["custom_words"]:
            self.spell_checker.add_to_personal_dict(w)
            self.new_word_entry.delete(0, "end")
            self._refresh_listbox()

    def _refresh_listbox(self):
        self.words_listbox.delete(0, "end")
        cfg = self.app.config.get_spell()
        for w in sorted(cfg["custom_words"]): self.words_listbox.insert("end", w)