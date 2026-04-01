import re
import customtkinter as ctk
from pathlib import Path

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts


class TerminalPanel(ctk.CTkFrame):
    """Container visual que simula um console e formata outputs do OS dinamicamente."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        log_header = ctk.CTkFrame(self, height=20, fg_color=Colors.BG_SIDEBAR, corner_radius=0)
        log_header.pack(side="top", fill="x")
        ctk.CTkLabel(log_header, text="TERMINAL / LOG", font=Fonts.LOG_BOLD, text_color=Colors.TEXT_MUTED).pack(
            side="left", padx=5)

        self.log = ctk.CTkTextbox(self, font=Fonts.LOG, state="disabled", fg_color=Colors.BG_PANEL)
        self.log.pack(side="top", fill="both", expand=True)

        is_dark = ctk.get_appearance_mode() == "Dark"
        error_color = Colors.SYNTAX_ERROR[1] if is_dark else Colors.SYNTAX_ERROR[0]
        warning_color = Colors.HIGHLIGHT_CURRENT[1] if is_dark else "#d97706"

        self.log.tag_config("error", foreground=error_color)
        self.log.tag_config("success", foreground=Colors.LA)
        self.log.tag_config("warning", foreground=warning_color)
        self.log.tag_config("info", foreground=Colors.THON)

        self.log.bind("<Button-1>", self._on_click)

    def update_colors(self):
        """Reaplica as cores de fundo e as tags do log após a troca de tema (Ctrl+T)."""
        is_dark = ctk.get_appearance_mode() == "Dark"
        idx = 1 if is_dark else 0

        # Atualiza a cor de fundo e texto do painel
        self.log.configure(
            fg_color=Colors.BG_PANEL[idx],
            text_color=Colors.TEXT_NORMAL[idx]
        )

        # Recalcula as cores das tags
        error_color = Colors.SYNTAX_ERROR[1] if is_dark else Colors.SYNTAX_ERROR[0]
        warning_color = Colors.HIGHLIGHT_CURRENT[1] if is_dark else "#d97706"

        # Reaplica as configurações das tags
        self.log.tag_config("error", foreground=error_color)
        self.log.tag_config("success", foreground=Colors.LA)
        self.log.tag_config("warning", foreground=warning_color)
        self.log.tag_config("info", foreground=Colors.THON)

        # Puxa nossas tags pro topo da pilha visual <<<
        self.log._textbox.tag_raise("error")
        self.log._textbox.tag_raise("warning")
        self.log._textbox.tag_raise("success")
        self.log._textbox.tag_raise("info")

    def log_line(self, text, tag=None):
        """Injeta uma linha visual no terminal do usuário, anexando tag de cor caso necessário."""
        try:
            self.log.configure(state="normal")
            if tag:
                self.log.insert("end", text + "\n", tag)
            else:
                self.log.insert("end", text + "\n")
            self.log.configure(state="disabled")
            self.log.see("end")
        except:
            pass

    def clear(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.app.editor.clear_error_lines()

    def analyze_latex_log(self, log_path: Path):
        """
        Rotina principal de extração de feedback (The Bug Hunter).
        Analisa os subprodutos do processo Batch (.bat) e varre as extensões de compilação.
        """
        if not log_path or not log_path.exists():
            return False

        has_errors = False
        seen_messages = set()  # Filtro Anti-Spam para evitar repetições no terminal

        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):

                # 1. Parsing de Falhas Fatais (Breakpoints MiKTeX)
                if line.startswith('! '):
                    has_errors = True
                    error_msg = line.strip()
                    line_num = "Desconhecida"

                    for j in range(i, min(i + 6, len(lines))):
                        match = re.search(r'l\.(\d+)', lines[j])
                        if match:
                            line_num = match.group(1)
                            if line_num.isdigit():
                                self.app.editor.highlight_error_line(line_num)
                            break

                    msg_hash = f"ERR_{line_num}_{error_msg}"
                    if msg_hash not in seen_messages:
                        seen_messages.add(msg_hash)
                        self.log_line(f"❌ Erro na linha {line_num}: {error_msg}", "error")

                # ==================================================
                # GATILHO DE RENDERIZAÇÃO DE WARNINGS DE ESTILIZAÇÃO
                # ==================================================
                elif getattr(self.app.options_manager, 'show_warnings', True):

                    if 'Warning' in line:
                        if 'Font Info' in line:
                            continue

                        warn_msg = line.strip()
                        line_num = "Desconhecida"
                        match = re.search(r'line (\d+)', line, re.IGNORECASE)

                        # Se não achou na linha atual, varre as próximas 3 linhas procurando "on input line X"
                        if not match:
                            for j in range(i, min(i + 4, len(lines))):
                                match_next = re.search(r'input line (\d+)', lines[j], re.IGNORECASE)
                                if match_next:
                                    match = match_next
                                    break

                        if match:
                            line_num = match.group(1)
                            if line_num.isdigit():
                                self.app.editor.highlight_warning_line(line_num)

                        # Verifica se o aviso exato já foi listado nesta mesma linha
                        msg_hash = f"WARN_{line_num}_{warn_msg}"
                        if msg_hash not in seen_messages:
                            seen_messages.add(msg_hash)
                            self.log_line(f"⚠️ Aviso (Linha {line_num}): {warn_msg}", "warning")

                    # Parsing de Avisos de Estouro Limítrofe (Overfull / Underfull hbox)
                    elif 'Overfull \\hbox' in line or 'Underfull \\hbox' in line:
                        match = re.search(r'lines (\d+)--(\d+)', line) or re.search(r'line (\d+)', line)
                        line_num = match.group(1) if match else "Desconhecida"

                        if line_num.isdigit():
                            self.app.editor.highlight_warning_line(line_num)

                        msg_hash = f"BOX_{line_num}_{line.strip()}"
                        if msg_hash not in seen_messages:
                            seen_messages.add(msg_hash)
                            self.log_line(f"📏 Estouro de Margem (Linha {line_num}): {line.strip()}", "warning")

        except Exception as e:
            self.log_line(f"Erro ao analisar o log: {e}", "error")

        return has_errors

    def _on_click(self, event):
        """Faz a ponte entre a linha com mensagem no terminal com seu espelho no código (Goto Feature)."""
        try:
            idx = self.log.index(f"@{event.x},{event.y}")
            line_text = self.log.get(f"{idx} linestart", f"{idx} lineend")

            # Adicionado re.IGNORECASE para pegar tanto "Linha" quanto "linha"
            match = re.search(r'linha (\d+)', line_text, re.IGNORECASE)
            if not match:
                match = re.search(r'l\.(\d+)', line_text, re.IGNORECASE)

            if match:
                line_num = match.group(1)
                self.app._switch_center_view('editor')
                self.app.editor.see(f"{line_num}.0")
                self.app.editor._textbox.mark_set("insert", f"{line_num}.0")
                self.app.editor.focus_set()
                self.app.editor.tag_add("sel", f"{line_num}.0", f"{line_num}.0 lineend")
        except:
            pass