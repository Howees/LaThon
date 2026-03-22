import re
import customtkinter as ctk
from pathlib import Path

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

class TerminalPanel(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app

        # ==========================================
        # CONSTRUÇÃO DO PAINEL
        # ==========================================
        log_header = ctk.CTkFrame(self, height=20, fg_color=Colors.BG_SIDEBAR, corner_radius=0)
        log_header.pack(side="top", fill="x")
        ctk.CTkLabel(log_header, text="TERMINAL / LOG", font=Fonts.LOG_BOLD, text_color=Colors.TEXT_MUTED).pack(side="left", padx=5)

        self.log = ctk.CTkTextbox(self, font=Fonts.LOG, state="disabled", fg_color=Colors.BG_PANEL)
        self.log.pack(side="top", fill="both", expand=True)

        # Configurando as cores de sucesso, erro e avisos
        is_dark = ctk.get_appearance_mode() == "Dark"
        error_color = Colors.SYNTAX_ERROR[1] if is_dark else Colors.SYNTAX_ERROR[0]
        warning_color = Colors.HIGHLIGHT_CURRENT[
            1] if is_dark else "#d97706"  # Laranja escuro no light, amarelo no dark

        self.log.tag_config("error", foreground=error_color)
        self.log.tag_config("success", foreground=Colors.LA)
        self.log.tag_config("warning", foreground=warning_color)

        # Evento de clique para ir até a linha do erro
        self.log.bind("<Button-1>", self._on_click)

    # ==========================================
    # LÓGICA DE REGISTRO E ANÁLISE
    # ==========================================
    def log_line(self, text, tag=None):
        """Escreve uma linha no terminal. Pode receber uma tag de cor ('error' ou 'success')."""
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
        """Limpa o terminal a cada nova compilação."""
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.app.editor.clear_error_lines() # <- ADICIONE ISTO!

    def analyze_latex_log(self, log_path: Path):
        """O Caçador de Bugs! Lê o arquivo .log do MiKTeX e extrai erros e avisos limpos."""
        if not log_path or not log_path.exists():
            return False

        has_errors = False
        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                # 1. CAÇADOR DE ERROS FATAIS (Começam com "!")
                if line.startswith('! '):
                    has_errors = True
                    error_msg = line.strip()
                    line_num = "Desconhecida"

                    # Procura a linha do erro nas próximas 6 linhas do log
                    for j in range(i, min(i + 6, len(lines))):
                        match = re.search(r'l\.(\d+)', lines[j])
                        if match:
                            line_num = match.group(1)
                            if line_num.isdigit():
                                self.app.editor.highlight_error_line(line_num)
                            break

                    self.log_line(f"❌ Erro na linha {line_num}: {error_msg}", "error")

                # ==================================================
                # SÓ RODA OS CAÇADORES DE AVISOS SE ESTIVEREM LIGADOS
                # ==================================================
                elif getattr(self.app.options_manager, 'show_warnings', True):

                    # 2. CAÇADOR DE WARNINGS REAIS
                    if 'Warning' in line:
                        # Pula aqueles avisos inúteis de fontes do compilador
                        if 'Font Info' in line:
                            continue

                        warn_msg = line.strip()
                        line_num = "Desconhecida"
                        match = re.search(r'line (\d+)', line)
                        if match:
                            line_num = match.group(1)
                            if line_num.isdigit():
                                self.app.editor.highlight_warning_line(line_num)

                        self.log_line(f"⚠️ Aviso (Linha {line_num}): {warn_msg}", "warning")

                    # 3. CAÇADOR DE ESTOURO DE MARGEM
                    elif 'Overfull \\hbox' in line or 'Underfull \\hbox' in line:
                        match = re.search(r'lines (\d+)--(\d+)', line) or re.search(r'line (\d+)', line)
                        line_num = match.group(1) if match else "Desconhecida"

                        if line_num.isdigit():
                            self.app.editor.highlight_warning_line(line_num)

                        self.log_line(f"📏 Estouro de Margem (Linha {line_num}): {line.strip()}", "warning")

        except Exception as e:
            self.log_line(f"Erro ao analisar o log: {e}", "error")

        return has_errors

    def _on_click(self, event):
        """Navega no editor quando o usuário clica num erro."""
        try:
            idx = self.log.index(f"@{event.x},{event.y}")
            line_text = self.log.get(f"{idx} linestart", f"{idx} lineend")

            # Procura pela nossa marcação "linha X" ou a original "l.X"
            match = re.search(r'linha (\d+)', line_text)
            if not match:
                match = re.search(r'l\.(\d+)', line_text)

            if match:
                line_num = match.group(1)
                self.app._switch_center_view('editor')
                self.app.editor.see(f"{line_num}.0")
                self.app.editor._textbox.mark_set("insert", f"{line_num}.0")
                self.app.editor.focus_set()
                self.app.editor.tag_add("sel", f"{line_num}.0", f"{line_num}.0 lineend")
        except:
            pass