import customtkinter as ctk
from lathon.ui.design import Colors, Icons
from lathon.ui.widgets.tooltip import ToolTip


def create_icon_button(parent, icon_name, tooltip_text, command, is_danger=False, side="left", padx=2):
    """Fábrica genérica para criar botões de ícone com tooltip no padrão LaThon."""
    # Correção: Usar a cor escura de hover para não engolir o ícone vermelho
    hover = Colors.BTN_DANGER_HOVER if is_danger else Colors.BTN_HOVER

    btn = ctk.CTkButton(parent, text="", image=Icons.get_ctk_image(icon_name, size=(18, 18)), command=command, width=32,
                        height=32, fg_color="transparent", hover_color=hover, text_color=Colors.TEXT_NORMAL)
    btn.pack(side=side, padx=padx)
    ToolTip(btn, tooltip_text)
    return btn