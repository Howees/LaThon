import re
import json
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from ui_widgets import ModernMenu

try:
    from spellchecker import SpellChecker

    PYSPELLCHECKER_AVAILABLE = True
except ImportError:
    PYSPELLCHECKER_AVAILABLE = False

CONFIG_FILE = "spell_config.json"
AVAILABLE_LANGUAGES = {"pt": "Português (Brasil)", "en": "Inglês (US)", "es": "Espanhol"}


class SpellCheckHandler:
    def __init__(self, app: 'MiniOverleaf', editor: ctk.CTkTextbox, spell_menu: tk.Menu):
        self.app = app
        self.editor = editor
        self.context_menu = ModernMenu(app, width=220)
        self.settings_window = None
        self.ignored_in_session = set()
        self.spell_checkers = []
        self.config = {"enabled_languages": ["pt"], "custom_words": [], "font_size": 12}

        self._load_config()
        self._initialize_checkers()

        # Aplica fonte inicial
        self._apply_font_size()

        self.editor._textbox.tag_configure("misspell", underline=True, foreground="#ff6b6b")
        self.editor.bind("<Button-3>", self._on_editor_right_click, add="+")

    def _load_config(self):
        if Path(CONFIG_FILE).exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except:
                pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except:
            pass

    def _apply_font_size(self):
        size = self.config.get("font_size", 12)
        font = ("Consolas", size)
        self.editor.configure(font=font)
        # Tenta atualizar line number bar tb
        try:
            self.app.line_number_bar.configure(font=font)
        except:
            pass

    def _initialize_checkers(self):
        self.spell_checkers.clear()
        if not PYSPELLCHECKER_AVAILABLE: return
        for lang in self.config["enabled_languages"]:
            try:
                c = SpellChecker(language=lang)
                if self.config["custom_words"]: c.word_frequency.load_words(self.config["custom_words"])
                self.spell_checkers.append(c)
            except:
                pass

    def apply_spell_check(self):
        self.editor._textbox.tag_remove("misspell", "1.0", "end")
        if not self.spell_checkers or not self.app.active_file: return
        try:
            content = self.editor.get("1.0", "end-1c")
            pat = re.compile(r'\b([a-zA-ZáàâãéèêíìîóòôõúùûüçÇ\'-]+)\b')
            for m in pat.finditer(content):
                w = m.group(1)
                if len(w) < 2: continue
                if w in self.ignored_in_session: continue
                correct = any(not c.unknown([w]) for c in self.spell_checkers)
                if not correct:
                    self.editor._textbox.tag_add("misspell", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        except:
            pass

    def _on_editor_right_click(self, event):
        self.context_menu.clear()
        try:
            index = self.editor.index(f"@{event.x},{event.y}")
            word = self.editor.get(f"{index} wordstart", f"{index} wordend").strip(".,;:!?\"'()[]{}")
        except:
            word = ""
        is_misspelled = "misspell" in self.editor.tag_names(index)
        if is_misspelled and self.spell_checkers and word:
            self.context_menu.add_command(f"➕ Adicionar '{word}'", lambda w=word: self._add_to_personal_dict(w),
                                          text_color=("#2ea043", "#55ff55"))
            self.context_menu.add_command(f"👁️ Ignorar", lambda w=word: self._ignore_session(w))
            self.context_menu.add_separator()
            sugs = set()
            for c in self.spell_checkers:
                try:
                    s = c.candidates(word)
                    if s: sugs.update(s)
                except:
                    pass
            if word in sugs: sugs.remove(word)
            final_sugs = sorted(list(sugs))[:5]
            if final_sugs:
                for s in final_sugs:
                    self.context_menu.add_command(f"Mudar para '{s}'", lambda x=s, start=f"{index} wordstart",
                                                                              end=f"{index} wordend": self._replace_word(
                        x, start, end))
            else:
                self.context_menu.add_command("(Sem sugestões)", None, text_color="gray")
            self.context_menu.add_separator()
        self.context_menu.add_command("Copiar", lambda: self.editor.focus_get().event_generate('<<Copy>>'))
        self.context_menu.add_command("Colar", lambda: self.editor.focus_get().event_generate('<<Paste>>'))
        self.context_menu.popup(event.x_root, event.y_root)
        return "break"

    def _add_to_personal_dict(self, w):
        if w and w not in self.config["custom_words"]:
            self.config["custom_words"].append(w)
            self._save_config()
            for c in self.spell_checkers: c.word_frequency.load_words([w])
            self.apply_spell_check()
            if self.settings_window and self.settings_window.winfo_exists(): self._refresh_listbox()

    def _ignore_session(self, w):
        self.ignored_in_session.add(w)
        self.apply_spell_check()

    def _replace_word(self, s, start, end):
        try:
            self.editor.delete(start, end)
            self.editor.insert(start, s)
            self.app._on_text_changed()
        except:
            pass

    # --- JANELA CONFIGURAÇÕES ---
    def open_settings_window(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift();
            return

        self.settings_window = ctk.CTkToplevel(self.app)
        self.settings_window.title("Configurações")
        self.settings_window.overrideredirect(True)
        self.settings_window.attributes("-topmost", True)
        self.settings_window.grab_set()

        w, h = 500, 600
        ws, hs = self.settings_window.winfo_screenwidth(), self.settings_window.winfo_screenheight()
        x, y = (ws / 2) - (w / 2), (hs / 2) - (h / 2)
        self.settings_window.geometry(f"{w}x{h}+{int(x)}+{int(y)}")
        self.settings_window.configure(fg_color=("white", "#2b2b2b"))

        border = ctk.CTkFrame(self.settings_window, fg_color="transparent", border_width=2,
                              border_color=("gray70", "#454545"))
        border.pack(fill="both", expand=True)

        close_btn = ctk.CTkButton(border, text="✕", width=30, height=30, fg_color="transparent", hover_color="red",
                                  text_color="gray", command=self.settings_window.destroy)
        close_btn.place(relx=0.92, rely=0.01)

        ctk.CTkLabel(border, text="Configurações", font=("Segoe UI", 20, "bold"), text_color=("black", "white")).pack(
            pady=15)

        # SEÇÃO FONTE
        ctk.CTkLabel(border, text="Tamanho da Fonte do Editor", font=("Segoe UI", 12, "bold"), text_color="gray").pack(
            anchor="w", padx=30)
        self.font_slider = ctk.CTkSlider(border, from_=10, to=24, number_of_steps=14, command=self._on_font_change)
        self.font_slider.set(self.config.get("font_size", 12))
        self.font_slider.pack(fill="x", padx=30, pady=5)
        self.font_label = ctk.CTkLabel(border, text=f"{int(self.font_slider.get())} px")
        self.font_label.pack(pady=(0, 10))

        ctk.CTkFrame(border, height=2, fg_color=("gray80", "#333333")).pack(fill="x", padx=20, pady=10)

        # SEÇÃO IDIOMAS
        ctk.CTkLabel(border, text="Idiomas do Corretor", font=("Segoe UI", 12, "bold"),
                     text_color=("black", "white")).pack(anchor="w", padx=30)
        f1 = ctk.CTkFrame(border, fg_color="transparent")
        f1.pack(fill="x", padx=30, pady=5)
        self.lang_vars = {}
        for c, n in AVAILABLE_LANGUAGES.items():
            var = ctk.StringVar(value="on" if c in self.config["enabled_languages"] else "off")
            self.lang_vars[c] = var
            ctk.CTkCheckBox(f1, text=n, variable=var, onvalue="on", offvalue="off", command=self._on_lang_change,
                            text_color=("black", "white")).pack(anchor="w", pady=2)

        ctk.CTkFrame(border, height=2, fg_color=("gray80", "#333333")).pack(fill="x", padx=20, pady=10)

        # SEÇÃO DICIONÁRIO
        ctk.CTkLabel(border, text="Dicionário Pessoal", font=("Segoe UI", 12, "bold"),
                     text_color=("black", "white")).pack(anchor="w", padx=30)
        f2 = ctk.CTkFrame(border, fg_color="transparent")
        f2.pack(fill="both", expand=True, padx=30, pady=5)

        is_dark = ctk.get_appearance_mode() == "Dark"
        self.words_listbox = tk.Listbox(f2, bd=0, highlightthickness=0, bg="#1e1e1e" if is_dark else "#f0f0f0",
                                        fg="white" if is_dark else "black", font=("Segoe UI", 11))
        self.words_listbox.pack(fill="both", expand=True, pady=5)
        self._refresh_listbox()

        btn_f = ctk.CTkFrame(f2, fg_color="transparent")
        btn_f.pack(fill="x", pady=5)
        self.new_word_entry = ctk.CTkEntry(btn_f, placeholder_text="Nova palavra...", fg_color=("gray95", "#343638"),
                                           text_color=("black", "white"))
        self.new_word_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_f, text="+", width=30, command=self._add_manual_word).pack(side="left")
        ctk.CTkButton(btn_f, text="Remover", fg_color="#cf222e", hover_color="#8b0000", width=80,
                      command=self._remove_word).pack(side="right", padx=(5, 0))

    def _on_font_change(self, value):
        size = int(value)
        self.font_label.configure(text=f"{size} px")
        self.config["font_size"] = size
        self._save_config()
        self._apply_font_size()

    def _on_lang_change(self):
        l = [c for c, v in self.lang_vars.items() if v.get() == "on"]
        self.config["enabled_languages"] = l
        self._save_config();
        self._initialize_checkers();
        self.apply_spell_check()

    def _remove_word(self):
        sel = self.words_listbox.curselection()
        if not sel: return
        w = self.words_listbox.get(sel[0])
        if w in self.config["custom_words"]:
            self.config["custom_words"].remove(w)
            self._save_config();
            self._refresh_listbox();
            self._initialize_checkers();
            self.apply_spell_check()

    def _add_manual_word(self):
        w = self.new_word_entry.get().strip()
        if w and w not in self.config["custom_words"]: self._add_to_personal_dict(w); self.new_word_entry.delete(0,
                                                                                                                 "end")

    def _refresh_listbox(self):
        self.words_listbox.delete(0, "end")
        for w in sorted(self.config["custom_words"]): self.words_listbox.insert("end", w)