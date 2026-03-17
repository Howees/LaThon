from pathlib import Path
import customtkinter as ctk

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors

try:
    import fitz  # PyMuPDF
    from PIL import Image
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class PreviewPanel(ctk.CTkFrame):
    """Componente Visual: O Painel Direito que exibe o PDF compilado."""

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=Colors.BG_SIDEBAR, corner_radius=0, **kwargs)
        self.app = app

        # --- CONSTRUÇÃO DA INTERFACE ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll_conf = {"scrollbar_button_color": Colors.SCROLL_BTN, "scrollbar_button_hover_color": Colors.SCROLL_HOVER}
        self.preview_frame = ctk.CTkScrollableFrame(self, label_text="", fg_color="transparent", **scroll_conf)
        self.preview_frame.grid(row=0, column=0, sticky="nsew")

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Abra um projeto para ver o preview.")
        self.preview_label.pack(expand=True)

        # --- LÓGICA E ESTADO ---
        self.pil_pdf_image = None
        self.pdf_preview_image = None
        self.current_pdf_path = None
        self.original_composite_image = None
        self._resize_timer = None

        self.bind("<Configure>", self.on_resize)

    def show_image_in_editor_panel(self, image_path: Path):
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            pil_image = Image.open(image_path)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except: pass

    def show_pdf_in_editor_panel(self, pdf_path: Path):
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            doc = fitz.open(pdf_path)
            if not len(doc): return
            pix = doc[0].get_pixmap(dpi=150)
            doc.close()
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except: pass

    def _display_image_centered(self, pil_image, container, label):
        container.update_idletasks()
        w = container.winfo_width()
        scale = (w if w > 1 else 400) / pil_image.width
        img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image,
                           size=(int(pil_image.width * scale), int(pil_image.height * scale)))
        label.configure(image=img, text="")

    def show_pdf_preview(self, pdf_path: Path):
        if not PYMUPDF_AVAILABLE:
            empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
            self.preview_label.configure(image=empty_img, text="Preview indisponível.")
            return

        self.current_pdf_path = pdf_path
        try:
            doc = fitz.open(pdf_path)
            page_images = []
            total_height, max_width = 0, 0

            for page in doc:
                pix = page.get_pixmap(dpi=130)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_images.append(img)
                total_height += img.height
                if img.width > max_width: max_width = img.width
            doc.close()

            if not page_images: return

            gap_color = (40, 40, 40) if ctk.get_appearance_mode() == "Dark" else (220, 220, 220)
            self.original_composite_image = Image.new('RGB', (max_width, total_height + (10 * (len(page_images) - 1))),
                                                      gap_color)

            y_offset = 0
            for img in page_images:
                self.original_composite_image.paste(img, ((max_width - img.width) // 2, y_offset))
                y_offset += img.height + 10

            self._apply_resize()
        except Exception as e:
            self.app.log_line(f"Erro preview: {e}")

    def clear_image(self):
        empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
        self.preview_label.configure(image=empty_img, text="Nenhum projeto aberto.")

        self.pil_pdf_image = None
        self.pdf_preview_image = None
        self.original_composite_image = None
        self.current_pdf_path = None

    def on_resize(self, event):
        if event.widget != self: return
        if getattr(self, 'original_composite_image', None) is None: return
        if self._resize_timer: self.app.after_cancel(self._resize_timer)
        self._resize_timer = self.app.after(100, self._apply_resize)

    def _apply_resize(self):
        if getattr(self, 'original_composite_image', None) is None: return
        self.update_idletasks()
        container_width = self.winfo_width() if self.winfo_width() > 20 else 500

        scale_ratio = (container_width - 30) / self.original_composite_image.width
        new_width, new_height = int(self.original_composite_image.width * scale_ratio), int(
            self.original_composite_image.height * scale_ratio)
        if new_width <= 0 or new_height <= 0: return

        self.pil_pdf_image = self.original_composite_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.pdf_preview_image = ctk.CTkImage(light_image=self.pil_pdf_image, dark_image=self.pil_pdf_image,
                                              size=(new_width, new_height))
        self.preview_label.configure(image=self.pdf_preview_image, text="")