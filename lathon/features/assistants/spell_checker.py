import re
from spellchecker import SpellChecker

class SpellCheckHandler:
    def __init__(self, app, editor):
        self.is_active = True
        self.app = app
        self.editor = editor
        self.ignored_in_session = set()
        self.spell_checkers = []

        cfg = self.app.config.get_spell()
        if not cfg.get("is_configured"):
            cfg["is_configured"] = True
            if "pt" not in cfg["enabled_languages"]: cfg["enabled_languages"].append("pt")
            self.app.config.update_spell(**cfg)

        self.initialize_checkers()
        self.spellcheck_timer = None
        self.editor.bind("<<EditorTextChanged>>", self._on_editor_changed, add="+")

    def _on_editor_changed(self, event=None):
        if not self.is_active: return
        if self.spellcheck_timer: self.editor.after_cancel(self.spellcheck_timer)
        self.spellcheck_timer = self.editor.after(1000, self.apply_spell_check)

    def initialize_checkers(self):
        self.spell_checkers.clear()
        cfg = self.app.config.get_spell()
        for lang in cfg.get("enabled_languages", []):
            try:
                c = SpellChecker(language=lang)
                if cfg.get("custom_words"): c.word_frequency.load_words(cfg["custom_words"])
                self.spell_checkers.append(c)
            except: pass

    def apply_spell_check(self):
        self.editor.tag_remove("misspell", "1.0", "end")
        if not self.is_active: return
        if not self.app.active_file or not self.spell_checkers: return
        try:
            content = self.editor.get("1.0", "end-1c")
            pat = re.compile(r'\b([a-zA-ZáàâãéèêíìîóòôõúùûüçÇÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÜ\'-]+)\b')
            cfg = self.app.config.get_spell()
            custom_set = set(cfg.get("custom_words", []))

            for m in pat.finditer(content):
                w = m.group(1)
                start_idx, end_idx = m.start(), m.end()

                if w in self.ignored_in_session or w in custom_set: continue
                if start_idx > 0 and content[start_idx - 1] in ['\\', '/']: continue
                if end_idx < len(content) and content[end_idx] == '/': continue

                correct = any(not c.unknown([w]) for c in self.spell_checkers)
                if not correct: self.editor.tag_add("misspell", f"1.0+{start_idx}c", f"1.0+{end_idx}c")
        except: pass

    def add_to_personal_dict(self, w):
        cfg = self.app.config.get_spell()
        if w and w not in cfg["custom_words"]:
            cfg["custom_words"].append(w)
            self.app.config.update_spell(custom_words=cfg["custom_words"])
            for c in self.spell_checkers: c.word_frequency.load_words([w])
            self.apply_spell_check()

    def ignore_session(self, w):
        self.ignored_in_session.add(w)
        self.apply_spell_check()

    def replace_word(self, s, start, end):
        try:
            self.editor.delete(start, end)
            self.editor.insert(start, s)
            self.app.editor._on_text_changed()
        except: pass

    def clear_state(self):
        self.ignored_in_session.clear()
        try: self.editor.tag_remove("misspell", "1.0", "end")
        except: pass

    # --- MOVido DO CONTEXT_MENU.PY ---
    def build_context_options(self, context_menu, index):
        if not self.spell_checkers: return

        try:
            line, col = map(int, index.split("."))
            line_text = self.editor.get(f"{line}.0", f"{line}.end")
            pat = re.compile(r'\b([a-zA-ZáàâãéèêíìîóòôõúùûüçÇÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÜ\'-]+)\b')
            word, start_str, end_str = "", "", ""
            for m in pat.finditer(line_text):
                if m.start() <= col <= m.end():
                    word = m.group(1)
                    start_str = f"{line}.{m.start()}"
                    end_str = f"{line}.{m.end()}"
                    break
        except: word = ""

        if word:
            self.editor.mark_set("insert", start_str)
            if "misspell" in self.editor.tag_names(start_str):
                context_menu.add_command(f"➕ Adicionar '{word}' ao Dicionário", lambda w=word: self.add_to_personal_dict(w), text_color=("#2ea043", "#55ff55"))
                context_menu.add_command(f"👁️ Ignorar '{word}'", lambda w=word: self.ignore_session(w))
                context_menu.add_separator()

                sugs = set()
                for c in self.spell_checkers:
                    try:
                        cands = c.candidates(word)
                        if cands: sugs.update(cands)
                    except: pass

                if word in sugs: sugs.remove(word)
                final_sugs = sorted(list(sugs))[:5]

                if final_sugs:
                    for s in final_sugs: context_menu.add_command(f"Substituir por: '{s}'", lambda x=s, st=start_str, en=end_str: self.replace_word(x, st, en))
                else:
                    context_menu.add_command("(Sem sugestões ortográficas)", None, text_color="gray")