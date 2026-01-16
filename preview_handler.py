from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

try:
    import fitz  # PyMuPDF
    from PIL import Image

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PreviewHandler:
    def __init__(self, app: 'MiniOverleaf'):
        self.app = app
        self.pil_pdf_image = None
        self.pdf_preview_image = None
        self.current_pdf_path = None

    def sync_scroll_from_editor(self, fraction):
        """Recebe a posição (0.0 a 1.0) do editor e move o PDF."""
        if not PYMUPDF_AVAILABLE or not self.pdf_preview_image: return
        try:
            self.app.preview_frame._parent_canvas.yview_moveto(fraction)
        except:
            pass

    def show_image_in_editor_panel(self, image_path: Path):
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            pil_image = Image.open(image_path)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except:
            pass

    def show_pdf_in_editor_panel(self, pdf_path: Path):
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            doc = fitz.open(pdf_path)
            if not len(doc): return
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            doc.close()
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except:
            pass

    def _display_image_centered(self, pil_image, container, label):
        container.update_idletasks()
        w = container.winfo_width()
        if w <= 1: w = 400
        scale = w / pil_image.width
        new_w = int(pil_image.width * scale)
        new_h = int(pil_image.height * scale)
        img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(new_w, new_h))
        label.configure(image=img, text="")

    def show_pdf_preview(self, pdf_path: Path):
        if not PYMUPDF_AVAILABLE:
            self.app.preview_label.configure(image=None, text="Preview indisponível.")
            return

        self.current_pdf_path = pdf_path

        try:
            doc = fitz.open(pdf_path)
            page_images = []
            total_height, max_width = 0, 0

            # DPI Fixo de alta qualidade
            render_dpi = 130

            for page in doc:
                pix = page.get_pixmap(dpi=render_dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_images.append(img)
                total_height += img.height
                if img.width > max_width: max_width = img.width
            doc.close()

            if not page_images: return

            current_theme = ctk.get_appearance_mode()
            gap_color = (40, 40, 40) if current_theme == "Dark" else (220, 220, 220)

            spacing = 10
            final_height = total_height + (spacing * (len(page_images) - 1))

            composite_image = Image.new('RGB', (max_width, final_height), gap_color)

            y_offset = 0
            for img in page_images:
                x_offset = (max_width - img.width) // 2
                composite_image.paste(img, (x_offset, y_offset))
                y_offset += img.height + spacing

            # FIT WIDTH (Largura Total)
            self.app.preview_frame.update_idletasks()
            container_width = self.app.preview_frame.winfo_width()

            if container_width <= 20: container_width = 500
            available_width = container_width - 15

            scale_ratio = available_width / composite_image.width
            new_width = int(composite_image.width * scale_ratio)
            new_height = int(composite_image.height * scale_ratio)

            self.pil_pdf_image = composite_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            self.pdf_preview_image = ctk.CTkImage(
                light_image=self.pil_pdf_image,
                dark_image=self.pil_pdf_image,
                size=(new_width, new_height)
            )

            self.app.preview_label.configure(image=self.pdf_preview_image, text="")

        except Exception as e:
            self.app.log_line(f"Erro preview: {e}")