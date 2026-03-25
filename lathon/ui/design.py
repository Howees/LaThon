import sys
import os
import customtkinter as ctk
from PIL import Image, ImageTk


def resource_path(relative_path):
    """
    Encontra o caminho absoluto dos recursos de forma dinâmica.
    Isso é crucial para quando o projeto for compilado com PyInstaller (.exe),
    pois os arquivos são extraídos em uma pasta temporária (sys._MEIPASS).
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
    return str(os.path.join(base_path, relative_path))


# ==========================================
# 🎨 1. CORES GLOBAIS (Dinâmicas e Estáticas)
# ==========================================
class Colors:
    """
    Classe central de Gerenciamento de Cores.
    Separa a Identidade Visual da marca (Estática) dos tons de Interface (Dinâmicos).
    """

    # ---------------------------------------------------------
    # IDENTIDADE VISUAL FIXA DA MARCA (Independe do Tema Atual)
    # ---------------------------------------------------------
    LA = "#2ea043"  # Verde base do LaThon
    THON = "#41a5ee"  # Azul base do LaThon

    # Paleta exclusiva usada no Seletor de Temas (Botões da Tela de Boas-vindas)
    THEME_BTNS = {
        "black": {"color": "#1a1a1a", "hover": "#454545"},  # Classic (Preto/Cinza)
        "green": {"color": LA, "hover": "#4cd164"},  # La (Verde e Verde Claro)
        "blue": {"color": THON, "hover": "#79c0f2"}  # Thon (Azul e Azul Claro)
    }

    # ---------------------------------------------------------
    # VARIÁVEIS DINÂMICAS DE INTERFACE (Preenchidas via load_theme)
    # ---------------------------------------------------------
    BG_MAIN = None  # Fundo das janelas raiz e Repositórios
    BG_PANEL = None  # Fundo de painéis de leitura (Editor, Find)
    BG_TOPBAR = None  # Fundo do menu superior
    BG_SIDEBAR = None  # Fundo da árvore lateral e terminal
    TEXT_NORMAL = None  # Cor do texto principal de leitura
    TEXT_MUTED = None  # Cor para legendas e textos secundários
    BORDER = None  # Cor dos traços de divisão
    BTN_HOVER = None  # Cor de fundo ao passar o mouse em menus transparentes
    BTN_TRANSPARENT_TEXT = None  # Cor do texto de botões sem fundo
    SCROLL_BTN = None  # Cor da barra de rolagem
    SCROLL_HOVER = None  # Cor da barra de rolagem ao arrastar

    # Botões de Ação Principal (Verde, Azul ou Mistos, definidos pelo tema)
    BTN_PRIMARY = None
    BTN_PRIMARY_HOVER = None

    @classmethod
    def load_theme(cls, theme_name="black"):
        """
        Carrega a paleta de cores estruturais baseada no tema escolhido.
        As tuplas representam (Light Mode, Dark Mode).
        O CustomTkinter lê automaticamente a posição 0 para Light e 1 para Dark.
        """
        if theme_name == "green":
            # PALETA LATHON GREEN (Focada em tons pastéis esverdeados para descanso visual)
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
            # PALETA THON BLUE (Inspirada em temas noturnos premium de IDEs)
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

        else:
            # PALETA BLACK/CLASSIC (Padrão nativo e neutro)
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

        # ---------------------------------------------------------
        # CORES INVARIÁVEIS (Mantém a cor independente do tema)
        # ---------------------------------------------------------
        cls.BTN_DANGER = "#ff5555"
        cls.BTN_DANGER_HOVER = "#502020"

        # Sintaxe do Editor de Código (Contraste testado para leitura prolongada)
        cls.SYNTAX_CMD = ("#0000ff", "#569cd6")  # Comandos iniciados em barra (\textbf)
        cls.SYNTAX_COMMENT = ("#008000", "#6a9955")  # Comentários iniciados por %
        cls.SYNTAX_LABEL = ("#a31515", "#ce9178")  # Ambientes e referências (\begin{figure})
        cls.SYNTAX_FILE = ("#795e26", "#dcdcaa")  # Nomes de arquivos referenciados
        cls.SYNTAX_ERROR = ("#d32f2f", "#ff6b6b")  # Erros capturados pelo corretor ortográfico

        # Destaque de Capítulos e Buscas (Find/Replace)
        cls.HIGHLIGHT_ALL = ("#f2f2a4", "#5c5c42")
        cls.HIGHLIGHT_CURRENT = ("#ffcc00", "#ffaa00")

        # Paleta de Anotações do Revisor (Markers)
        cls.MARKER_YELLOW = "#ffeb3b"
        cls.MARKER_GREEN = "#81c784"
        cls.MARKER_BLUE = "#64b5f6"
        cls.MARKER_RED = "#e57373"
        cls.MARKER_PALETTE = [(cls.MARKER_YELLOW, "Amarelo"), (cls.MARKER_GREEN, "Verde"), (cls.MARKER_BLUE, "Azul"),
                              (cls.MARKER_RED, "Vermelho")]

        # Tooltip para exibir os comentários das marcações
        cls.MARKER_TOOLTIP_BG = "#ffffe0"
        cls.MARKER_TOOLTIP_FG = "black"


# Carregamento seguro da paleta original durante o Start-up
Colors.load_theme("black")


# ==========================================
# 🔤 2. FONTES PADRONIZADAS
# ==========================================
class Fonts:
    """Centraliza todas as fontes usadas no sistema para manter a consistência."""
    UI = ("Segoe UI", 12)
    UI_BOLD = ("Segoe UI", 12, "bold")
    UI_TITLE = ("Segoe UI", 16, "bold")
    UI_LOGO_BIG = ("Segoe UI", 60, "bold")
    UI_MODAL_TITLE = ("Segoe UI", 24, "bold")

    MONO = ("Consolas", 12)  # Fonte padrão monospace do Editor
    LOG = ("Consolas", 10)  # Fonte padrão monospace do Terminal
    LOG_BOLD = ("Consolas", 10, "bold")


# ==========================================
# 🖼️ 3. GERENCIADOR DE ÍCONES (.png e .ico)
# ==========================================
class Icons:
    """
    Controlador de Cache de Imagens.
    Carrega imagens do disco apenas uma vez na vida útil do programa.
    Evita vazamento de memória e lentidão ao renderizar dezenas de botões na tela.
    """
    _cache_ctk = {}  # Cache exclusivo para instâncias do CustomTkinter
    _cache_tk = {}  # Cache exclusivo para instâncias do Tkinter nativo (ex: Árvore)

    @staticmethod
    def get_ctk_image(filename, size=(18, 18)):
        """Retorna uma imagem otimizada para componentes CustomTkinter (ex: CTkButton)."""

        # MUDANÇA AQUI: A chave do cache agora é o nome + tamanho!
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
        """Define o ícone principal da janela do aplicativo na barra de tarefas do Windows."""
        try:
            path = resource_path("icones/lathon.ico")
            window.iconbitmap(path)
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível carregar o ícone principal 'lathon.ico' - {e}")

    @staticmethod
    def get_treeview_icon(filename, size=(16, 16)):
        """Retorna uma imagem PhotoImage convertida para compatibilidade com a Treeview (Tkinter nativo)."""
        if filename not in Icons._cache_tk:
            path = resource_path(f"icones/{filename}")
            try:
                # O Lanczos garante altíssima qualidade ao redimensionar imagens pequenas
                pil_img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
                Icons._cache_tk[filename] = ImageTk.PhotoImage(pil_img)
            except Exception:
                # Fallback: se não achar a imagem, gera um bloco invisível para não quebrar o layout
                empty = Image.new('RGBA', size, (0, 0, 0, 0))
                Icons._cache_tk[filename] = ImageTk.PhotoImage(empty)
        return Icons._cache_tk[filename]


# ==========================================
# 🧩 4. COMPONENTES REUTILIZÁVEIS
# ==========================================
def create_lathon_logo(parent, font_size=16):
    """
    Constrói a Logo colorida do LaThon (Verde e Azul).
    Extraído para uma função global para facilitar a inserção em Topbars, Rodapés e Modais.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(frame, text="La", font=("Segoe UI", font_size, "bold"), text_color=Colors.LA).pack(side="left")
    ctk.CTkLabel(frame, text="Thon", font=("Segoe UI", font_size, "bold"), text_color=Colors.THON).pack(side="left")
    return frame