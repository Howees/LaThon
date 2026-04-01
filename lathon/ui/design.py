import sys
import os
import customtkinter as ctk
from PIL import Image, ImageTk


def resource_path(relative_path):
    """
    Garante o acesso aos recursos visuais (ícones, imagens) tanto no ambiente de
    desenvolvimento quanto no executável final gerado pelo PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
    return str(os.path.join(base_path, relative_path))


class Colors:
    """
    Gerenciador central de paletas de cores do sistema.
    As variáveis declaradas como None são preenchidas dinamicamente pelo método `load_theme`.
    """

    # --- IDENTIDADE VISUAL FIXA ---
    # Cores de marca do aplicativo, imutáveis independentemente do tema.
    LA = "#2ea043"
    THON = "#41a5ee"

    # Paleta para os botões de seleção de tema na tela de Boas-vindas.
    THEME_BTNS = {
        "black": {"color": "#1a1a1a", "hover": "#454545"},
        "green": {"color": LA, "hover": "#4cd164"},
        "blue": {"color": THON, "hover": "#79c0f2"}
    }

    # --- VARIÁVEIS DE INTERFACE DINÂMICAS ---
    BG_MAIN = None  # Fundo principal das janelas raízes
    BG_PANEL = None  # Fundo de painéis de destaque (Editor de texto, Abas)
    BG_TOPBAR = None  # Fundo do menu superior
    BG_SIDEBAR = None  # Fundo do gerenciador de arquivos e terminal lateral
    TEXT_NORMAL = None  # Cor primária de leitura e escrita
    TEXT_MUTED = None  # Textos secundários, legendas e placeholders
    BORDER = None  # Contornos e separadores de frames
    BTN_HOVER = None  # Efeito hover para menus dropdown e botões transparentes
    BTN_TRANSPARENT_TEXT = None  # Texto para botões sem fundo (fg_color="transparent")
    SCROLL_BTN = None  # Barra de rolagem estática
    SCROLL_HOVER = None  # Barra de rolagem em uso (arrastando)

    BTN_PRIMARY = None  # Cor sólida para botões de ação afirmativa (Salvar, Compilar)
    BTN_PRIMARY_HOVER = None  # Efeito hover para os botões primários

    @classmethod
    def load_theme(cls, theme_name="black"):
        """
        Injeta as cores do tema selecionado nas variáveis dinâmicas da classe.
        Padrão CustomTkinter: A tupla define ("Cor Light Mode", "Cor Dark Mode").
        """
        if theme_name == "green":
            cls.BG_MAIN = ("#E0EBE0", "#0A1710")
            cls.BG_PANEL = ("#F4FAF4", "#112117")
            cls.BG_TOPBAR = ("#CDE0CD", "#07120B")
            cls.BG_SIDEBAR = ("#D6E5D6", "#0C1C13")
            cls.TEXT_NORMAL = ("#0C1C11", "#D8EBE0")
            cls.TEXT_MUTED = ("#4A6B56", "#739982")
            cls.BORDER = ("#A9C2B0", "#1F3D2A")
            cls.BTN_HOVER = ("#C5D9C9", "#183021")
            cls.BTN_TRANSPARENT_TEXT = ("#0C1C11", "#D8EBE0")
            cls.SCROLL_BTN = ("#9CBFA9", "#254A33")
            cls.SCROLL_HOVER = ("#82A890", "#2E5C40")
            cls.BTN_PRIMARY = cls.LA
            cls.BTN_PRIMARY_HOVER = "#238636"

        elif theme_name == "blue":
            cls.BG_MAIN = ("#DFE8F0", "#0D1424")
            cls.BG_PANEL = ("#F2F6FA", "#131D33")
            cls.BG_TOPBAR = ("#C3D4E6", "#090F1C")
            cls.BG_SIDEBAR = ("#D0DCE8", "#0F1629")
            cls.TEXT_NORMAL = ("#0A1321", "#DDE8F5")
            cls.TEXT_MUTED = ("#546785", "#7D94B5")
            cls.BORDER = ("#A4B9D1", "#223252")
            cls.BTN_HOVER = ("#BCCFE0", "#1B2845")
            cls.BTN_TRANSPARENT_TEXT = ("#0A1321", "#DDE8F5")
            cls.SCROLL_BTN = ("#96ADC4", "#2B406B")
            cls.SCROLL_HOVER = ("#7E99B3", "#365085")
            cls.BTN_PRIMARY = cls.THON
            cls.BTN_PRIMARY_HOVER = "#2B7BB5"

        else:  # Padrão Clássico/Dark
            cls.BG_MAIN = ("#e6e6e6", "#2b2b2b")
            cls.BG_PANEL = ("white", "#1e1e1e")
            cls.BG_TOPBAR = ("gray90", "#1f1f1f")
            cls.BG_SIDEBAR = ("gray95", "#252526")
            cls.TEXT_NORMAL = ("black", "white")
            cls.TEXT_MUTED = ("gray30", "gray60")
            cls.BORDER = ("gray70", "#454545")
            cls.BTN_HOVER = ("gray80", "#3a3d41")
            cls.BTN_TRANSPARENT_TEXT = ("gray10", "gray90")
            cls.SCROLL_BTN = ("#bfbfbf", "#7a7a7a")
            cls.SCROLL_HOVER = ("#a6a6a6", "#a0a0a0")
            cls.BTN_PRIMARY = "#238636"
            cls.BTN_PRIMARY_HOVER = "#2ea043"

        # --- CORES ESTRUTURAIS FIXAS ---
        # Ações destrutivas (ex: deletar arquivo, fechar sem salvar)
        cls.BTN_DANGER = "#ff5555"
        cls.BTN_DANGER_HOVER = "#502020"

        # Syntax Highlighting do Editor de Texto (Tema de cores do código)
        cls.SYNTAX_CMD = ("#0000ff", "#569cd6")  # Comandos LaTeX: \textbf, \section
        cls.SYNTAX_COMMENT = ("#008000", "#6a9955")  # Comentários: % texto
        cls.SYNTAX_LABEL = ("#a31515", "#ce9178")  # Ambientes: \begin{figure}
        cls.SYNTAX_FILE = ("#795e26", "#dcdcaa")  # Arquivos importados via \include
        cls.SYNTAX_ERROR = ("#d32f2f", "#ff6b6b")  # Sublinhado do corretor ortográfico

        # Ferramenta de Busca (Find/Replace)
        cls.HIGHLIGHT_ALL = ("#f2f2a4", "#5c5c42")  # Fundo de todas as ocorrências encontradas
        cls.HIGHLIGHT_CURRENT = ("#ffcc00", "#ffaa00")  # Fundo da ocorrência focada atualmente

        # Ferramenta de Revisão/Marcação de Texto
        cls.MARKER_YELLOW = "#ffeb3b"
        cls.MARKER_GREEN = "#81c784"
        cls.MARKER_BLUE = "#64b5f6"
        cls.MARKER_RED = "#e57373"
        cls.MARKER_PALETTE = [
            (cls.MARKER_YELLOW, "Amarelo"),
            (cls.MARKER_GREEN, "Verde"),
            (cls.MARKER_BLUE, "Azul"),
            (cls.MARKER_RED, "Vermelho")
        ]

        # Estilo do balão de anotações flutuante
        cls.MARKER_TOOLTIP_BG = "#ffffe0"
        cls.MARKER_TOOLTIP_FG = "black"


# Inicialização padrão para garantir que a UI tenha dados no startup
Colors.load_theme("black")


class Fonts:
    """Padronização tipográfica de toda a interface para evitar hardcoding."""
    UI = ("Segoe UI", 12)
    UI_BOLD = ("Segoe UI", 12, "bold")
    UI_TITLE = ("Segoe UI", 16, "bold")
    UI_LOGO_BIG = ("Segoe UI", 60, "bold")
    UI_MODAL_TITLE = ("Segoe UI", 24, "bold")

    MONO = ("Consolas", 12)  # Fonte monoespaçada para o editor de código
    LOG = ("Consolas", 10)  # Fonte para a saída do compilador no terminal
    LOG_BOLD = ("Consolas", 10, "bold")


class Icons:
    """
    Sistema de cache de imagens para evitar vazamento de memória.
    Mantém apenas uma instância de cada ícone em memória durante a execução.
    """
    _cache_ctk = {}  # Cache para o framework CustomTkinter
    _cache_tk = {}  # Cache para o framework Tkinter nativo (ex: Treeview)

    @staticmethod
    def get_ctk_image(filename, size=(18, 18)):
        """Carrega e retorna um ícone otimizado para botões e labels do CustomTkinter."""
        cache_key = (filename, size)

        if cache_key not in Icons._cache_ctk:
            path = resource_path(f"icones/{filename}")
            try:
                pil_img = Image.open(path)
                Icons._cache_ctk[cache_key] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            except Exception:
                print(f"⚠️ Aviso: Ícone '{filename}' não encontrado.")
                return None

        return Icons._cache_ctk[cache_key]

    @staticmethod
    def set_window_icon(window):
        """Aplica o ícone oficial da aplicação na barra de tarefas do SO."""
        try:
            path = resource_path("icones/lathon.ico")
            window.iconbitmap(path)
        except Exception as e:
            print(f"⚠️ Aviso: Falha ao carregar lathon.ico - {e}")

    @staticmethod
    def get_treeview_icon(filename, size=(16, 16)):
        """Carrega e retorna um ícone compatível com componentes clássicos do Tkinter (como a Treeview)."""
        if filename not in Icons._cache_tk:
            path = resource_path(f"icones/{filename}")
            try:
                # O filtro LANCZOS preserva a nitidez em reduções severas (ex: 16x16)
                pil_img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
                Icons._cache_tk[filename] = ImageTk.PhotoImage(pil_img)
            except Exception:
                # Retorna um pixel transparente para preservar o alinhamento caso falhe
                empty = Image.new('RGBA', size, (0, 0, 0, 0))
                Icons._cache_tk[filename] = ImageTk.PhotoImage(empty)
        return Icons._cache_tk[filename]


def create_lathon_logo(parent, font_size=16):
    """Gera o componente visual da logo bicolor."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(frame, text="La", font=("Segoe UI", font_size, "bold"), text_color=Colors.LA).pack(side="left")
    ctk.CTkLabel(frame, text="Thon", font=("Segoe UI", font_size, "bold"), text_color=Colors.THON).pack(side="left")
    return frame