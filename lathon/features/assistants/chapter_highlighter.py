import re
import customtkinter as ctk

class ChapterHighlighter:
    """Gerencia a funcionalidade opcional de 'Evidenciar Capítulos' no editor."""

    def __init__(self, editor):
        self.editor = editor
        self.is_active = False
        self.editor.bind("<<EditorTextChanged>>", self._on_editor_changed, add="+")
        self.highlight_timer = None

    def _on_editor_changed(self, event=None):
        if not self.is_active: return
        if self.highlight_timer: self.editor.after_cancel(self.highlight_timer)
        self.highlight_timer = self.editor.after(850, self.apply)

    def update_colors(self):
        is_dark = ctk.get_appearance_mode() == "Dark"
        c_bg = ["#4a3b59", "#2d4a5e", "#2f5c5c", "#3e523e", "#5e5236"] if is_dark else ["#DAE8FC", "#D5E8D4", "#E1D5E7", "#FFE6CC", "#FFF2CC"]
        tags = ["h_part", "h_chapter", "h_section", "h_subsection", "h_subsubsection"]
        for t, color in zip(tags, c_bg):
            self.editor._textbox.tag_configure(t, background=color)

    def toggle(self):
        self.is_active = not self.is_active
        if self.is_active:
            self.update_colors()
            self.apply()
        else:
            self.remove()

    def apply(self):
        if not self.is_active: return
        self.remove()
        try:
            text_content = self.editor.get("1.0", "end-1c")
        except:
            return

        for match in re.finditer(r'\\(part|chapter|section|subsection|subsubsection)(\*?)\s*\{', text_content, re.MULTILINE):
            cmd = match.group(1)
            start_idx = f"1.0 + {match.start()} chars linestart"
            end_idx = f"1.0 + {match.start()} chars lineend"
            tag_map = {"part": "h_part", "chapter": "h_chapter", "section": "h_section", "subsection": "h_subsection", "subsubsection": "h_subsubsection"}
            self.editor.tag_add(tag_map.get(cmd, "h_section"), start_idx, end_idx)

    def remove(self):
        for tag in ["h_part", "h_chapter", "h_section", "h_subsection", "h_subsubsection"]:
            self.editor.tag_remove(tag, "1.0", "end")