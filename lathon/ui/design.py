import sys
import os
import customtkinter as ctk
from PIL import Image, ImageTk


def resource_path(relative_path):
    """ Encontra o caminho absoluto dos arquivos independentemente de onde o run.py for chamado """
    try:
        base_path = sys._MEIPASS
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
    return str(os.path.join(base_path, relative_path))



# ==========================================
# 🎨 1. CORES GLOBAIS (Light Mode, Dark Mode)
# ==========================================
class Colors:
    # Identidade Visual
    LA = "#2ea043"
    THON = "#41a5ee"

    # Fundos (Backgrounds)
    BG_MAIN = ("#e6e6e6", "#2b2b2b")  # Fundo da janela principal
    BG_PANEL = ("white", "#1e1e1e")  # Fundo do editor e painéis internos
    BG_TOPBAR = ("gray90", "#1f1f1f")  # Barra de menus superior
    BG_SIDEBAR = ("gray95", "#252526")  # Fundo da árvore de arquivos

    # Textos e Bordas
    TEXT_NORMAL = ("black", "white")
    TEXT_MUTED = ("gray30", "gray60")
    BORDER = ("gray70", "#454545")

    # Botões e Interações
    BTN_PRIMARY = "#238636"
    BTN_PRIMARY_HOVER = "#2ea043"
    BTN_DANGER = "#ff5555"
    BTN_DANGER_HOVER = "#502020"
    BTN_HOVER = ("gray80", "#3a3d41")
    BTN_TRANSPARENT_TEXT = ("gray10", "gray90")

    # Scrollbars
    SCROLL_BTN = ("#bfbfbf", "#7a7a7a")
    SCROLL_HOVER = ("#a6a6a6", "#a0a0a0")

    # Sintaxe do Editor (Highlighter)
    SYNTAX_CMD = ("#0000ff", "#569cd6")
    SYNTAX_COMMENT = ("#008000", "#6a9955")
    SYNTAX_LABEL = ("#a31515", "#ce9178")
    SYNTAX_FILE = ("#795e26", "#dcdcaa")
    SYNTAX_ERROR = ("#d32f2f", "#ff6b6b")

    # Destaque de Capítulos e Buscas
    HIGHLIGHT_ALL = ("#f2f2a4", "#5c5c42")
    HIGHLIGHT_CURRENT = ("#ffcc00", "#ffaa00")


# ==========================================
# 🔤 2. FONTES PADRONIZADAS
# ==========================================
class Fonts:
    UI = ("Segoe UI", 12)
    UI_BOLD = ("Segoe UI", 12, "bold")
    UI_TITLE = ("Segoe UI", 16, "bold")
    UI_LOGO_BIG = ("Segoe UI", 60, "bold")
    UI_MODAL_TITLE = ("Segoe UI", 24, "bold")

    MONO = ("Consolas", 12)  # Para o Editor de código
    LOG = ("Consolas", 10)  # Para o Terminal
    LOG_BOLD = ("Consolas", 10, "bold")


# ==========================================
# 🖼️ 3. GERENCIADOR DE ÍCONES (.png)
# ==========================================
class Icons:
    _cache_ctk = {}  # Cache para CustomTkinter
    _cache_tk = {}  # Cache para Tkinter Clássico (Árvore)

    @staticmethod
    def get_ctk_image(filename, size=(18, 18)):
        if filename not in Icons._cache_ctk:
            path = resource_path(f"icones/{filename}")
            try:
                pil_img = Image.open(path)
                Icons._cache_ctk[filename] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception as e:
                print(f"⚠️ Aviso: Ícone '{filename}' não encontrado.")
                return None
        return Icons._cache_ctk[filename]

    @staticmethod
    def set_window_icon(window):
        """Define o ícone principal da janela do aplicativo usando o arquivo .ico nativo do Windows"""
        try:
            # Puxa o caminho absoluto garantindo compatibilidade com o .exe depois
            path = resource_path("icones/lathon.ico")
            window.iconbitmap(path)
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível carregar o ícone principal 'lathon.ico' - {e}")

    @staticmethod
    def get_treeview_icon(filename, size=(16, 16)):
        if filename not in Icons._cache_tk:
            path = resource_path(f"icones/{filename}")
            try:
                pil_img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
                Icons._cache_tk[filename] = ImageTk.PhotoImage(pil_img)
            except Exception as e:
                empty = Image.new('RGBA', size, (0, 0, 0, 0))
                Icons._cache_tk[filename] = ImageTk.PhotoImage(empty)
        return Icons._cache_tk[filename]


# ==========================================
# 🧩 4. COMPONENTES REUTILIZÁVEIS
# ==========================================
def create_lathon_logo(parent, font_size=16):
    """Gera o texto 'LaThon' colorido para evitar repetição de código nas telas."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(frame, text="La", font=("Segoe UI", font_size, "bold"), text_color=Colors.LA).pack(side="left")
    ctk.CTkLabel(frame, text="Thon", font=("Segoe UI", font_size, "bold"), text_color=Colors.THON).pack(side="left")
    return frame