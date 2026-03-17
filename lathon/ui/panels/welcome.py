import customtkinter as ctk
from pathlib import Path

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts, Icons, create_lathon_logo


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, fg_color="transparent")
        self.app = app_instance
        self.pack(fill="both", expand=True)

        self.center_container = ctk.CTkFrame(self, fg_color="transparent")
        self.center_container.place(relx=0.5, rely=0.5, anchor="center")
        self._show_main_menu()

    def _show_main_menu(self):
        for widget in self.center_container.winfo_children(): widget.destroy()

        # Usa o componente centralizado para a Logo (bem grande)
        logo = create_lathon_logo(self.center_container, font_size=60)
        logo.pack(pady=(0, 20))

        ctk.CTkButton(self.center_container, text=" Criar Novo Projeto",
                      image=Icons.get_ctk_image("new.png", size=(20, 20)),
                      command=self._show_create_options, width=300, height=45, font=(Fonts.UI[0], 14, "bold"),
                      fg_color=Colors.BTN_PRIMARY, hover_color=Colors.BTN_PRIMARY_HOVER, corner_radius=8).pack(pady=8)

        ctk.CTkButton(self.center_container, text=" Abrir Projeto Existente",
                      image=Icons.get_ctk_image("open.png", size=(20, 20)),
                      command=self.app._open_project_flow, width=300, height=45, font=(Fonts.UI[0], 14, "bold"),
                      fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL, border_width=2,
                      border_color=Colors.BORDER, hover_color=Colors.BTN_HOVER, corner_radius=8).pack(pady=8)

        recents = self.app.config.get_recents()
        if recents:
            ctk.CTkFrame(self.center_container, height=1, width=200, fg_color=Colors.BORDER).pack(pady=(25, 10))
            ctk.CTkLabel(self.center_container, text="Recentes", text_color=Colors.TEXT_MUTED, font=Fonts.UI_BOLD).pack(
                pady=(0, 5))
            scroll_recents = ctk.CTkScrollableFrame(self.center_container, width=320, height=120,
                                                    fg_color="transparent")
            scroll_recents.pack()

            for path_str in recents:
                p = Path(path_str)
                if p.exists():
                    ctk.CTkButton(scroll_recents, text=f" {p.name}", image=Icons.get_ctk_image("tex.png"), anchor="w",
                                  font=Fonts.UI, height=30, fg_color="transparent", text_color=Colors.TEXT_NORMAL,
                                  hover_color=Colors.BTN_HOVER,
                                  command=lambda x=p: self.app.load_project_folder(x)).pack(fill="x", pady=1)

        ctk.CTkLabel(self.center_container, text="v1.2 - Public Edition", text_color=Colors.TEXT_MUTED,
                     font=("Segoe UI", 10)).pack(pady=(20, 0))

    def _show_create_options(self):
        for widget in self.center_container.winfo_children(): widget.destroy()

        ctk.CTkLabel(self.center_container, text="Novo Projeto", font=Fonts.UI_MODAL_TITLE).pack(pady=(0, 30))

        ctk.CTkButton(self.center_container, text=" Começar do Zero",
                      image=Icons.get_ctk_image("file.png", size=(20, 20)),
                      command=lambda: self.app._finish_create_project("blank"), width=300, height=45,
                      font=(Fonts.UI[0], 14, "bold"),
                      corner_radius=8, fg_color=Colors.THON, hover_color="#2b7cb5").pack(
            pady=10)  # Azul um pouco mais escuro pro hover

        ctk.CTkButton(self.center_container, text=" Importar de .zip",
                      image=Icons.get_ctk_image("zip.png", size=(20, 20)),
                      command=lambda: self.app._finish_create_project("zip"), width=300, height=45,
                      font=(Fonts.UI[0], 14, "bold"),
                      corner_radius=8, fg_color=Colors.BG_MAIN, text_color=Colors.TEXT_NORMAL,
                      hover_color=Colors.BTN_HOVER).pack(pady=10)

        ctk.CTkButton(self.center_container, text="← Voltar", command=self._show_main_menu, width=100, height=30,
                      fg_color="transparent", text_color=Colors.TEXT_MUTED, hover_color=Colors.BTN_HOVER).pack(
            pady=(30, 0))