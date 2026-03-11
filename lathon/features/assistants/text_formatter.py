class TextFormatter:
    """Gerencia a aplicação de tags de formatação no texto selecionado do editor LaTeX."""

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
        except:
            pass