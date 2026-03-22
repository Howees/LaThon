import customtkinter as ctk
from lathon.ui.widgets.base_modal import BaseModal

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

class LayoutConfigDialog(BaseModal):
    def __init__(self, master_app):
        super().__init__(master_app, "Configuração de Tela", 450, 300)
        ctk.CTkLabel(self.border_frame, text="Configuração de Tela", font=Fonts.UI_TITLE).pack(pady=15)

        cfg = self.app.config.get_layout()
        self.left_val, self.center_val, self.pdf_val = cfg.get("left", 15), cfg.get("center", 50), cfg.get("pdf", 35)

        self.slider_left = self._create_row("Arquivos", self.left_val, 'left')
        self.slider_center = self._create_row("Editor", self.center_val, 'center')
        self.slider_pdf = self._create_row("PDF", self.pdf_val, 'pdf')

        self.lbl_total = ctk.CTkLabel(self.border_frame, text="", font=Fonts.UI_BOLD)
        self.lbl_total.pack(pady=10)

        btn_f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        btn_f.pack(pady=10)
        ctk.CTkButton(btn_f, text="Cancelar", width=80, fg_color="transparent", border_width=1, text_color=Colors.TEXT_NORMAL, command=self._close_dialog).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="Salvar e Aplicar", width=140, command=self._apply).pack(side="left", padx=5)
        self._update_labels()

    def _create_row(self, name, val, source):
        f = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        f.pack(pady=10, fill="x", padx=20)
        lbl = ctk.CTkLabel(f, text=f"{name} ({val}%)", width=110, anchor="w")
        lbl.pack(side="left")
        slider = ctk.CTkSlider(f, from_=5, to=80, command=lambda v: self._sync_sliders(source, v))
        slider.set(val)
        slider.pack(side="left", fill="x", expand=True)
        setattr(self, f"lbl_{source}", lbl)
        return slider

    def _sync_sliders(self, source, value):
        v = int(value)
        if source == 'left':
            self.left_val = v
            rem = 100 - self.left_val
            self.center_val = int(rem * (self.center_val / max(1, self.center_val + self.pdf_val)))
            self.pdf_val = rem - self.center_val
        elif source == 'center':
            self.center_val = v
            rem = 100 - self.center_val
            self.left_val = int(rem * (self.left_val / max(1, self.left_val + self.pdf_val)))
            self.pdf_val = rem - self.left_val
        elif source == 'pdf':
            self.pdf_val = v
            rem = 100 - self.pdf_val
            self.left_val = int(rem * (self.left_val / max(1, self.left_val + self.center_val)))
            self.center_val = rem - self.left_val

        self.slider_left.set(self.left_val)
        self.slider_center.set(self.center_val)
        self.slider_pdf.set(self.pdf_val)
        self._update_labels()

    def _update_labels(self):
        self.lbl_left.configure(text=f"Arquivos ({self.left_val}%)")
        self.lbl_center.configure(text=f"Editor ({self.center_val}%)")
        self.lbl_pdf.configure(text=f"PDF ({self.pdf_val}%)")
        self.lbl_total.configure(text="Total: 100% (Ajuste Automático)", text_color=Colors.LA)

    def _apply(self):
        self.app.preferences_manager.apply_layout_weights(self.left_val, self.center_val, self.pdf_val)
        self._close_dialog()