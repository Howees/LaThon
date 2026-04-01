import customtkinter as ctk
from lathon.ui.design import Colors, Icons
from lathon.ui.widgets.tooltip import ToolTip


def create_icon_button(parent, icon_name, tooltip_text, command, is_danger=False, side="left", padx=2):
    """
    Constrói um botão de ícone padronizado com feedback visual e tooltip.

    Args:
        parent: Widget pai onde o botão será anexado.
        icon_name: Nome do arquivo de imagem (ex: 'save.png').
        tooltip_text: Texto exibido ao passar o mouse.
        command: Função a ser executada no clique.
        is_danger: Se True, aplica o tema de atenção (vermelho) no efeito hover.
        side: Direção do empacotamento (pack).
        padx: Espaçamento horizontal.
    """
    hover_color = Colors.BTN_DANGER_HOVER if is_danger else Colors.BTN_HOVER

    btn = ctk.CTkButton(
        parent,
        text="",
        image=Icons.get_ctk_image(icon_name, size=(18, 18)),
        command=command,
        width=32,
        height=32,
        fg_color="transparent",
        hover_color=hover_color,
        text_color=Colors.TEXT_NORMAL
    )
    btn.pack(side=side, padx=padx)

    ToolTip(btn, tooltip_text)

    return btn