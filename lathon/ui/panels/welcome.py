import customtkinter as ctk
from pathlib import Path

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

        logo_frame = ctk.CTkFrame(self.center_container, fg_color="transparent")
        logo_frame.pack(pady=(0, 20))
        ctk.CTkLabel(logo_frame, text="La", font=("Segoe UI", 60, "bold"), text_color="#2ea043").pack(side="left")
        ctk.CTkLabel(logo_frame, text="Thon", font=("Segoe UI", 60, "bold"), text_color="#41a5ee").pack(side="left")

        ctk.CTkButton(self.center_container, text="✨  Criar Novo Projeto", command=self._show_create_options,
                      width=300, height=45, font=("Segoe UI", 14, "bold"), fg_color="#238636",
                      hover_color="#2ea043", corner_radius=8).pack(pady=8)

        ctk.CTkButton(self.center_container, text="📂  Abrir Projeto Existente", command=self.app._open_project_flow,
                      width=300, height=45, font=("Segoe UI", 14, "bold"), fg_color=("gray85", "gray20"),
                      text_color=("black", "white"), border_width=2, border_color=("gray70", "gray50"),
                      hover_color=("gray75", "gray25"), corner_radius=8).pack(pady=8)

        # AGORA CHAMA O CONFIG MANAGER
        recents = self.app.config.get_recents()
        if recents:
            ctk.CTkFrame(self.center_container, height=1, width=200, fg_color=("gray70", "gray30")).pack(pady=(25, 10))
            ctk.CTkLabel(self.center_container, text="Recentes", text_color="gray50", font=("Segoe UI", 11, "bold")).pack(pady=(0, 5))
            scroll_recents = ctk.CTkScrollableFrame(self.center_container, width=320, height=120, fg_color="transparent")
            scroll_recents.pack()

            for path_str in recents:
                p = Path(path_str)
                if p.exists():
                    ctk.CTkButton(scroll_recents, text=f"📄 {p.name}", anchor="w", font=("Segoe UI", 12), height=30,
                                  fg_color="transparent", text_color=("gray20", "gray80"), hover_color=("gray85", "gray25"),
                                  command=lambda x=p: self.app.load_project_folder(x)).pack(fill="x", pady=1)

        ctk.CTkLabel(self.center_container, text="v1.0.1 - Public Edition", text_color="gray40", font=("Segoe UI", 10)).pack(pady=(20, 0))

    def _show_create_options(self):
        for widget in self.center_container.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.center_container, text="Novo Projeto", font=("Segoe UI", 24, "bold")).pack(pady=(0, 30))
        ctk.CTkButton(self.center_container, text="📄  Começar do Zero", command=lambda: self.app._finish_create_project("blank"),
                      width=300, height=45, font=("Segoe UI", 14), corner_radius=8, fg_color=("#3B8ED0", "#1f538d"), hover_color=("#36719F", "#14375e")).pack(pady=10)
        ctk.CTkButton(self.center_container, text="📦  Importar de .zip", command=lambda: self.app._finish_create_project("zip"),
                      width=300, height=45, font=("Segoe UI", 14), corner_radius=8, fg_color=("gray80", "gray30"), text_color=("black", "white"), hover_color=("gray70", "gray40")).pack(pady=10)
        ctk.CTkButton(self.center_container, text="← Voltar", command=self._show_main_menu, width=100, height=30, fg_color="transparent", text_color="gray", hover_color=("gray90", "gray20")).pack(pady=(30, 0))