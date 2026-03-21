class TextFormatter:
    """Gerencia a aplicação de tags de formatação e manipulação de texto no editor LaTeX."""

    @staticmethod
    def apply_format(editor, style):
        try:
            sel = editor.tag_ranges("sel")
            if not sel: return

            txt = editor.get(sel[0], sel[1])
            cmd = {"bold": "\\textbf", "italic": "\\textit", "underline": "\\underline"}.get(style)

            if not cmd: return

            editor.delete(sel[0], sel[1])
            editor.insert(sel[0], f"{cmd}{{{txt}}}")

            # Avisa o editor para atualizar a sintaxe e as linhas
            if hasattr(editor, '_on_text_changed'):
                editor._on_text_changed()
        except:
            pass

    @staticmethod
    def toggle_comment(editor):
        """Comenta ou descomenta a(s) linha(s) selecionada(s) com '%'."""
        try:
            sel = editor.tag_ranges("sel")
            if not sel:
                # Nenhuma seleção: comenta/descomenta a linha atual onde o cursor está
                idx = editor.index("insert")
                line = idx.split(".")[0]
                content = editor.get(f"{line}.0", f"{line}.end")
                if content.startswith("%"):
                    editor.delete(f"{line}.0", f"{line}.1")
                else:
                    editor.insert(f"{line}.0", "%")
            else:
                # Múltiplas linhas selecionadas
                start_line = int(editor.index(sel[0]).split(".")[0])
                end_line = int(editor.index(sel[1]).split(".")[0])
                for line in range(start_line, end_line + 1):
                    content = editor.get(f"{line}.0", f"{line}.end")
                    if content.startswith("%"):
                        editor.delete(f"{line}.0", f"{line}.1")
                    else:
                        editor.insert(f"{line}.0", "%")

            # Avisa o editor para atualizar a sintaxe e as linhas
            if hasattr(editor, '_on_text_changed'):
                editor._on_text_changed()
        except:
            pass