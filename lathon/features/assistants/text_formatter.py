class TextFormatter:
    """Provém funções utilitárias diretas aos botões de topbar da janela Editor Panel."""

    @staticmethod
    def apply_format(editor, style):
        """Envelopa o texto selecionado dentro da tag de estilo indicada (Ex. \textbf{texto})."""
        try:
            sel = editor.tag_ranges("sel")
            if not sel: return

            txt = editor.get(sel[0], sel[1])
            cmd = {"bold": "\\textbf", "italic": "\\textit", "underline": "\\underline"}.get(style)

            if not cmd: return

            editor.delete(sel[0], sel[1])
            editor.insert(sel[0], f"{cmd}{{{txt}}}")

            if hasattr(editor, '_on_text_changed'):
                editor._on_text_changed()
        except:
            pass

    @staticmethod
    def toggle_comment(editor):
        """Comenta ou Descomenta linhas injetando/deletando do bloco as tags % de comentário global LaTeX."""
        try:
            sel = editor.tag_ranges("sel")
            if not sel:
                # Comentário de Linha Única sem marcação via arraste
                idx = editor.index("insert")
                line = idx.split(".")[0]
                content = editor.get(f"{line}.0", f"{line}.end")

                if content.startswith("%"):
                    editor.delete(f"{line}.0", f"{line}.1")
                else:
                    editor.insert(f"{line}.0", "%")
            else:
                # Comentário Multi-linhas em Bloco (Ctrl+/)
                start_line = int(editor.index(sel[0]).split(".")[0])
                end_line = int(editor.index(sel[1]).split(".")[0])

                for line in range(start_line, end_line + 1):
                    content = editor.get(f"{line}.0", f"{line}.end")
                    if content.startswith("%"):
                        editor.delete(f"{line}.0", f"{line}.1")
                    else:
                        editor.insert(f"{line}.0", "%")

            if hasattr(editor, '_on_text_changed'):
                editor._on_text_changed()
        except:
            pass