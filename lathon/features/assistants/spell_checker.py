import re
from spellchecker import SpellChecker

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors


class SpellCheckHandler:
    """Analisa as palavras renderizadas e pinta/apresenta correções de texto vivo."""

    def __init__(self, app, editor):
        self.is_active = True
        self.app = app
        self.editor = editor
        self.ignored_in_session = set()
        self.spell_checkers = []

        cfg = self.app.config.get_spell()

        # Rotina de auto-configuração no setup inicial para o idioma padrão da máquina (Português)
        if not cfg.get("is_configured"):
            cfg["is_configured"] = True
            if "pt" not in cfg["enabled_languages"]:
                cfg["enabled_languages"].append("pt")
            self.app.config.update_spell(**cfg)

        self.initialize_checkers()
        self.spellcheck_timer = None
        self.editor.bind("<<EditorTextChanged>>", self._on_editor_changed, add="+")

    def _on_editor_changed(self, event=None):
        """Timer robusto (1000ms) que restringe as leituras apenas quando o usuário pausa a digitação."""
        if not self.is_active: return
        if self.spellcheck_timer: self.editor.after_cancel(self.spellcheck_timer)
        self.spellcheck_timer = self.editor.after(1000, self.apply_spell_check)

    def initialize_checkers(self):
        """Instancia os objetos verificadores nativos, carregando os dicionários na memória RAM."""
        self.spell_checkers.clear()
        cfg = self.app.config.get_spell()
        for lang in cfg.get("enabled_languages", []):
            try:
                c = SpellChecker(language=lang)
                if cfg.get("custom_words"):
                    c.word_frequency.load_words(cfg["custom_words"])
                self.spell_checkers.append(c)
            except:
                pass

    def apply_spell_check(self):
        """Varredura total (Parsing) detectando exceções e aplicando underline vermelho aos erros."""
        self.editor.tag_remove("misspell", "1.0", "end")
        if not self.is_active: return
        if not self.app.active_file or not self.spell_checkers: return

        try:
            content = self.editor.get("1.0", "end-1c")
            # Expressão Regular para detecção exclusiva de palavras alfanuméricas com acentos latinos
            pat = re.compile(r'\b([a-zA-ZáàâãéèêíìîóòôõúùûüçÇÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÜ\'-]+)\b')
            cfg = self.app.config.get_spell()
            custom_set = set(cfg.get("custom_words", []))

            for m in pat.finditer(content):
                w = m.group(1)
                start_idx, end_idx = m.start(), m.end()

                # Pula as palavras que foram configuradas como corretas ou ignoradas
                if w in self.ignored_in_session or w in custom_set:
                    continue

                # Ignora palavras adjacentes a elementos estruturais (ex: Comandos \ ou Divisões /)
                if start_idx > 0 and content[start_idx - 1] in ['\\', '/']:
                    continue
                if end_idx < len(content) and content[end_idx] == '/':
                    continue

                # Identifica se a palavra é classificada como 'Desconhecida' em pelo menos 1 idioma ativo
                correct = any(not c.unknown([w]) for c in self.spell_checkers)

                if not correct:
                    self.editor.tag_add("misspell", f"1.0+{start_idx}c", f"1.0+{end_idx}c")
        except:
            pass

    def add_to_personal_dict(self, w):
        """Alimenta o dicionário global na variável JSON e atualiza o estado."""
        cfg = self.app.config.get_spell()
        if w and w not in cfg["custom_words"]:
            cfg["custom_words"].append(w)
            self.app.config.update_spell(custom_words=cfg["custom_words"])
            for c in self.spell_checkers:
                c.word_frequency.load_words([w])
            self.apply_spell_check()

    def ignore_session(self, w):
        """Mantém uma palavra ignorada ativamente APENAS durante o tempo de vida do software atual."""
        self.ignored_in_session.add(w)
        self.apply_spell_check()

    def replace_word(self, s, start, end):
        """Aplicação da sugestão de correção automática dentro do ContextMenu."""
        try:
            self.editor.delete(start, end)
            self.editor.insert(start, s)
            self.app.editor._on_text_changed()
        except:
            pass

    def clear_state(self):
        """Reinicia listas de sessão ao mudar de arquivos/projetos."""
        self.ignored_in_session.clear()
        try:
            self.editor.tag_remove("misspell", "1.0", "end")
        except:
            pass

    def build_context_options(self, context_menu, index):
        """
        Constrói o sub-menu pop-up ao clicar com botão direito sob uma palavra com erro.
        Traz no máximo 5 sugestões e fornece os botões rápidos de exclusão.
        """
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
        except:
            word = ""

        if word:
            self.editor.mark_set("insert", start_str)

            # Se a palavra estiver catalogada sob erro de sintaxe, extrai suas sugestões
            if "misspell" in self.editor.tag_names(start_str):
                context_menu.add_command(f"Adicionar '{word}' ao Dicionário",
                                         lambda w=word: self.add_to_personal_dict(w), text_color=Colors.LA)
                context_menu.add_command(f"Ignorar '{word}'", lambda w=word: self.ignore_session(w))
                context_menu.add_separator()

                sugs = set()
                for c in self.spell_checkers:
                    try:
                        cands = c.candidates(word)
                        if cands: sugs.update(cands)
                    except:
                        pass

                if word in sugs: sugs.remove(word)

                # Exibe as 5 alternativas mais coerentes extraídas do motor
                final_sugs = sorted(list(sugs))[:5]

                if final_sugs:
                    for s in final_sugs:
                        context_menu.add_command(f"Substituir por: '{s}'",
                                                 lambda x=s, st=start_str, en=end_str: self.replace_word(x, st, en))
                else:
                    context_menu.add_command("(Sem sugestões ortográficas)", None, text_color=Colors.TEXT_MUTED)