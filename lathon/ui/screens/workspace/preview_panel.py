"""
preview_panel.py

"""

from pathlib import Path
import tkinter as tk
import customtkinter as ctk

# --- DESIGN SYSTEM ---
from lathon.ui.design import Colors, Fonts

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageTk

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class PreviewPanel(ctk.CTkFrame):
    """
    Gerencia o visualizador interno de PDF e Imagens do LaThon.
    Suporta zoom interativo, rolagem dinâmica (panning), extração/cópia de texto
    e navegação bidirecional (SyncTeX) entre o PDF gerado e o código-fonte LaTeX.
    """

    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color=Colors.BG_SIDEBAR, corner_radius=0, **kwargs)
        self.app = app

        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # ==========================================
        # 1. BARRA DE FERRAMENTAS DO VISUALIZADOR
        # ==========================================
        self.toolbar = ctk.CTkFrame(self, height=35, fg_color=Colors.BG_PANEL, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        nav_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        nav_frame.pack(side="left", padx=10, pady=5)

        btn_conf = {
            "width": 24, "height": 24, "fg_color": "transparent",
            "text_color": Colors.TEXT_NORMAL, "hover_color": Colors.BTN_HOVER,
            "font": Fonts.UI_BOLD
        }

        self.btn_prev = ctk.CTkButton(nav_frame, text="ʌ", command=self.prev_page, **btn_conf)
        self.btn_prev.pack(side="left")

        self.page_label = ctk.CTkLabel(nav_frame, text="0 / 0", width=50, font=Fonts.UI)
        self.page_label.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(nav_frame, text="v", command=self.next_page, **btn_conf)
        self.btn_next.pack(side="left")

        zoom_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        zoom_frame.pack(side="right", padx=10, pady=5)

        self.btn_zoom_out = ctk.CTkButton(zoom_frame, text="-", command=self.zoom_out, **btn_conf)
        self.btn_zoom_out.pack(side="left")

        self.zoom_label = ctk.CTkLabel(zoom_frame, text="100%", width=60, font=Fonts.UI)
        self.zoom_label.pack(side="left", padx=5)

        self.btn_zoom_in = ctk.CTkButton(zoom_frame, text="+", command=self.zoom_in, **btn_conf)
        self.btn_zoom_in.pack(side="left")

        # ==========================================
        # 2. ÁREA DE EXIBIÇÃO E SCROLLBARS (CANVAS)
        # ==========================================
        bg_color = Colors.BG_SIDEBAR[1] if ctk.get_appearance_mode() == "Dark" else Colors.BG_SIDEBAR[0]

        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew")

        self.v_scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.v_scrollbar.grid(row=1, column=1, sticky="ns")

        self.h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.h_scrollbar.grid(row=2, column=0, sticky="ew")

        self.canvas.configure(yscrollcommand=self._on_v_scroll_update, xscrollcommand=self.h_scrollbar.set)

        self.message_id = self.canvas.create_text(
            150, 50, text="Abra um projeto para ver o preview.",
            fill=Colors.TEXT_MUTED[0], font=("Segoe UI", 12)
        )

        # ==========================================
        # ESTADO INTERNO DO VISUALIZADOR
        # ==========================================
        self.current_pdf_path = None
        self.raw_pil_pages = []  # Armazena as páginas em alta resolução
        self.tk_images = []  # Cache de imagens renderizadas no Canvas
        self.page_metadata = []  # Metadados de coordenadas e escala para cada página (crítico para o SyncTeX)
        self.text_cache = {}  # Cache de palavras extraídas pelo PyMuPDF
        self._resize_timer = None

        self.zoom_level = 1.0
        self.fit_to_width = True

        self.sel_start_word = None
        self.selected_text = ""

        # ==========================================
        # MAPEAMENTO DE EVENTOS
        # ==========================================
        self.bind("<Configure>", self.on_resize)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self.canvas.bind("<Motion>", self._on_mouse_move)

        self.canvas.bind("<Double-Button-1>", self._on_pdf_double_click)

        self.bind("<Control-c>", self._copy_selected_text)
        self.canvas.bind("<Control-c>", self._copy_selected_text)
        self.bind("<Control-C>", self._copy_selected_text)

        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_release)

        self.canvas.bind("<ButtonPress-2>", self._on_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_pan_motion)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_release)

    def _set_appearance_mode(self, mode_string):
        """Atualiza a cor de fundo do Canvas nativo ao alternar entre Light/Dark mode."""
        super()._set_appearance_mode(mode_string)
        if hasattr(self, 'canvas'):
            is_dark = mode_string.lower() == "dark"
            new_bg = Colors.BG_SIDEBAR[1] if is_dark else Colors.BG_SIDEBAR[0]
            self.canvas.configure(bg=new_bg)

    def show_image_in_editor_panel(self, image_path: Path):
        """Renderiza uma imagem rasterizada (PNG, JPG) diretamente no visualizador central."""
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            pil_image = Image.open(image_path)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except:
            pass

    def show_pdf_in_editor_panel(self, pdf_path: Path):
        """Extrai e renderiza a primeira página de um PDF avulso no visualizador central."""
        if not PYMUPDF_AVAILABLE: return
        self.app._switch_center_view('image')
        try:
            doc = fitz.open(pdf_path)
            if not len(doc): return
            pix = doc[0].get_pixmap(dpi=150)
            doc.close()
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self._display_image_centered(pil_image, self.app.image_viewer_container, self.app.image_viewer_label)
        except:
            pass

    def _display_image_centered(self, pil_image, container, label):
        """Utilitário para ajustar a escala e centralizar imagens no container."""
        container.update_idletasks()
        w = container.winfo_width()
        scale = (w if w > 1 else 400) / pil_image.width
        img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image,
                           size=(int(pil_image.width * scale), int(pil_image.height * scale)))
        label.configure(image=img, text="")

    def show_pdf_preview(self, pdf_path: Path):
        """Processa um documento PDF completo e carrega suas páginas para exibição."""
        if not PYMUPDF_AVAILABLE: return
        self.current_pdf_path = pdf_path
        self.text_cache = {}

        try:
            doc = fitz.open(pdf_path)
            self.raw_pil_pages = []

            for page_index in range(len(doc)):
                page = doc[page_index]
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Extrai as coordenadas de todas as palavras para permitir seleção e cópia
                self.text_cache[page_index + 1] = page.get_text("words")

                self.raw_pil_pages.append({
                    "image": img,
                    "pdf_width": page.rect.width,
                    "pdf_height": page.rect.height,
                    "page_num": page_index + 1
                })
            doc.close()

            self._apply_resize()
            self._update_page_counter()
        except Exception as e:
            self.app.log_line(f"Erro preview: {e}")

    def clear_image(self):
        """Reseta o visualizador ao fechar projetos."""
        self.canvas.delete("all")
        self.raw_pil_pages = []
        self.tk_images = []
        self.page_metadata = []
        self.text_cache = {}
        self.current_pdf_path = None
        self.page_label.configure(text="0 / 0")
        self.message_id = self.canvas.create_text(
            150, 50, text="Nenhum projeto aberto.",
            fill=Colors.TEXT_MUTED[0], font=("Segoe UI", 12)
        )

    # ==========================================
    # LÓGICA DE NAVEGAÇÃO, SCROLL E ZOOM
    # ==========================================
    def _on_ctrl_mousewheel(self, event):
        step = 0.05 if event.delta > 0 else -0.05
        self.adjust_zoom(step)

    def zoom_in(self):
        self.adjust_zoom(0.2)

    def zoom_out(self):
        self.adjust_zoom(-0.2)

    def adjust_zoom(self, step):
        self.fit_to_width = False
        self.zoom_level = max(0.6, min(2.0, self.zoom_level + step))
        self._apply_resize()

    def on_resize(self, event):
        """Impede recalculo excessivo agrupando os eventos de resize da janela."""
        if not self.raw_pil_pages or not self.fit_to_width: return
        if self._resize_timer: self.app.after_cancel(self._resize_timer)
        self._resize_timer = self.app.after(200, self._apply_resize)

    def _apply_resize(self):
        """Renderiza as páginas no Canvas aplicando a escala correta de zoom ou de largura da janela."""
        if not self.raw_pil_pages: return
        self.canvas.delete("all")
        self.tk_images = []
        self.page_metadata = []

        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()

        # Fallback de geometria durante a renderização inicial
        if canvas_w <= 20: canvas_w = 500
        if canvas_h <= 20: canvas_h = 700

        if self.fit_to_width:
            self.zoom_level = 1.0

        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")

        y_offset = 10
        bg_color = Colors.BG_SIDEBAR[1] if ctk.get_appearance_mode() == "Dark" else Colors.BG_SIDEBAR[0]
        self.canvas.configure(bg=bg_color)
        max_rendered_width = canvas_w

        for data in self.raw_pil_pages:
            orig_img = data["image"]

            scale_w = (canvas_w - 40) / orig_img.width
            scale_h = (canvas_h - 40) / orig_img.height
            base_scale = min(scale_w, scale_h)

            final_scale = base_scale * self.zoom_level
            new_width = int(orig_img.width * final_scale)
            new_height = int(orig_img.height * final_scale)

            if new_width <= 0 or new_height <= 0: continue
            if new_width > max_rendered_width: max_rendered_width = new_width

            resized_pil = orig_img.resize((new_width, new_height), Image.Resampling.BILINEAR)
            tk_img = ImageTk.PhotoImage(resized_pil)
            self.tk_images.append(tk_img)

            x_offset = max(0, (canvas_w - new_width) // 2)
            self.canvas.create_image(x_offset, y_offset, image=tk_img, anchor="nw")

            # Salva fatores matemáticos para o sistema de coordenadas do SyncTeX e da seleção de texto
            escala_para_pdf = data["pdf_width"] / new_width
            self.page_metadata.append({
                "page_num": data["page_num"],
                "y_start": y_offset,
                "y_end": y_offset + new_height,
                "x_start": x_offset,
                "x_end": x_offset + new_width,
                "scale_factor": escala_para_pdf
            })
            y_offset += new_height + 15

        self.canvas.configure(scrollregion=(0, 0, max_rendered_width, y_offset))
        self._update_page_counter()

    # ==========================================
    # EVENTOS DE MOUSE, SELEÇÃO E NAVEGAÇÃO
    # ==========================================
    def _on_mouse_move(self, event):
        """Modifica o cursor para 'texto' quando passa sobre palavras do PDF."""
        if not self.page_metadata: return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        over_text = False
        for meta in self.page_metadata:
            if meta["y_start"] <= canvas_y <= meta["y_end"]:
                pdf_x = (canvas_x - meta["x_start"]) * meta["scale_factor"]
                pdf_y = (canvas_y - meta["y_start"]) * meta["scale_factor"]

                words = self.text_cache.get(meta["page_num"], [])
                for w in words:
                    if w[0] - 2 <= pdf_x <= w[2] + 2 and w[1] - 2 <= pdf_y <= w[3] + 2:
                        over_text = True
                        break
                break

        self.canvas.configure(cursor="xterm" if over_text else "")

    def _on_pan_start(self, event):
        """Inicia a movimentação livre do PDF clicando e segurando o botão do meio/scroll."""
        self.canvas.configure(cursor="fleur")
        self.canvas.scan_mark(event.x, event.y)

    def _on_pan_motion(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._update_page_counter()

    def _on_pan_release(self, event):
        self.canvas.configure(cursor="")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_v_scroll_update(self, *args):
        self.v_scrollbar.set(*args)
        self._update_page_counter()

    def _update_page_counter(self):
        """Calcula a página atualmente visível com base na posição da scrollbar."""
        if not self.page_metadata: return
        top_y = self.canvas.canvasy(0)
        center_y = top_y + (self.canvas.winfo_height() / 3)
        current_page = 1
        for meta in self.page_metadata:
            if meta["y_start"] <= center_y <= meta["y_end"]:
                current_page = meta["page_num"]
                break
        self.page_label.configure(text=f"{current_page} / {len(self.page_metadata)}")

    def next_page(self):
        if not self.page_metadata: return
        top_y = self.canvas.canvasy(0)
        for meta in self.page_metadata:
            if meta["y_start"] > top_y + 10:
                self._scroll_to_y(meta["y_start"] - 10)
                break

    def prev_page(self):
        if not self.page_metadata: return
        top_y = self.canvas.canvasy(0)
        for meta in reversed(self.page_metadata):
            if meta["y_end"] < top_y + 10:
                self._scroll_to_y(meta["y_start"] - 10)
                break

    def _scroll_to_y(self, target_y):
        scroll_region = self.canvas.bbox("all")
        if not scroll_region: return
        total_height = scroll_region[3]
        fraction = target_y / total_height
        self.canvas.yview_moveto(max(0.0, min(1.0, fraction)))

    # ==========================================
    # CÓPIA E SELEÇÃO DE TEXTO DO PDF
    # ==========================================
    def _get_word_index_at_pos(self, canvas_x, canvas_y, max_dist=15):
        """Converte as coordenadas visuais da tela para buscar palavras embutidas no arquivo PDF."""
        for meta in self.page_metadata:
            if meta["y_start"] <= canvas_y <= meta["y_end"]:
                pdf_x = (canvas_x - meta["x_start"]) * meta["scale_factor"]
                pdf_y = (canvas_y - meta["y_start"]) * meta["scale_factor"]

                words = self.text_cache.get(meta["page_num"], [])
                if not words: return meta, None

                # Busca exata
                for idx, w in enumerate(words):
                    if w[0] - 2 <= pdf_x <= w[2] + 2 and w[1] - 2 <= pdf_y <= w[3] + 2:
                        return meta, idx

                # Busca por aproximação (fallback para precisão do mouse)
                min_dist = float('inf')
                best_idx = None
                for idx, w in enumerate(words):
                    dx = max(0, w[0] - pdf_x, pdf_x - w[2])
                    dy = max(0, w[1] - pdf_y, pdf_y - w[3])
                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = idx

                if min_dist < max_dist: return meta, best_idx
                return meta, None
        return None, None

    def _highlight_and_extract(self, meta, start_idx, end_idx):
        """Desenha a marcação azul de seleção e agrupa os fragmentos de texto correspondentes."""
        self.canvas.delete("selection_highlight")
        page_num = meta["page_num"]
        words = self.text_cache.get(page_num, [])
        if not words: return ""

        i1, i2 = min(start_idx, end_idx), max(start_idx, end_idx)
        extracted_text = ""
        last_block, last_line = -1, -1

        for i in range(i1, i2 + 1):
            w = words[i]
            x0 = (w[0] / meta["scale_factor"]) + meta["x_start"]
            y0 = (w[1] / meta["scale_factor"]) + meta["y_start"]
            x1 = (w[2] / meta["scale_factor"]) + meta["x_start"]
            y1 = (w[3] / meta["scale_factor"]) + meta["y_start"]
            self.canvas.create_rectangle(
                x0, y0, x1, y1, fill="#aaddff", outline="",
                tags="selection_highlight", stipple="gray50"
            )

            text, block_no, line_no = w[4], w[5], w[6]
            if i > i1:
                if block_no != last_block or line_no != last_line:
                    extracted_text += "\n"
                else:
                    extracted_text += " "
            extracted_text += text
            last_block, last_line = block_no, line_no

        return extracted_text

    def _on_drag_start(self, event):
        self.canvas.focus_set()
        self.canvas.delete("selection_highlight")
        self.selected_text = ""

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        meta, idx = self._get_word_index_at_pos(canvas_x, canvas_y)
        self.sel_start_word = (meta, idx) if meta and idx is not None else None

    def _on_drag_motion(self, event):
        if not self.sel_start_word: return
        start_meta, start_idx = self.sel_start_word

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        curr_meta, curr_idx = self._get_word_index_at_pos(canvas_x, canvas_y)

        if curr_meta and curr_meta["page_num"] == start_meta["page_num"] and curr_idx is not None:
            self._highlight_and_extract(start_meta, start_idx, curr_idx)

    def _on_drag_release(self, event):
        if not self.sel_start_word: return
        start_meta, start_idx = self.sel_start_word

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        curr_meta, curr_idx = self._get_word_index_at_pos(canvas_x, canvas_y)

        if curr_meta and curr_meta["page_num"] == start_meta["page_num"] and curr_idx is not None:
            if start_idx != curr_idx:
                self.selected_text = self._highlight_and_extract(start_meta, start_idx, curr_idx)
            else:
                self.canvas.delete("selection_highlight")
                self.selected_text = ""

        self.sel_start_word = None

    def _copy_selected_text(self, event=None):
        if self.selected_text:
            self.clipboard_clear()
            self.clipboard_append(self.selected_text)
            self.app.log_line(f"[Aviso] Texto copiado ({len(self.selected_text)} caracteres).")

    # ==========================================
    # SYNCTEX: BUSCA INVERSA (PDF -> CÓDIGO FONTE)
    # ==========================================
    def _on_pdf_double_click(self, event):
        """
        Gatilho do SyncTeX. Recebe o clique duplo no PDF, identifica as coordenadas
        e se comunica com o compilador externo para rastrear a respectiva linha de código.
        """
        import subprocess, re, os, unicodedata
        from pathlib import Path

        if not self.page_metadata or not self.current_pdf_path or not self.app.project_dir:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Identificação da página atual
        target_meta = None
        for meta in self.page_metadata:
            if meta["y_start"] <= canvas_y <= meta["y_end"]:
                target_meta = meta
                break
        if not target_meta:
            return

        # Busca por palavras renderizadas no local exato do clique
        meta, idx = self._get_word_index_at_pos(canvas_x, canvas_y, max_dist=15)
        clicked_on_text = (meta is not None and idx is not None)

        target_word_clean = ""
        pdf_prev_words = []
        pdf_next_words = []

        if clicked_on_text:
            words_on_page = self.text_cache.get(meta["page_num"], [])

            # Une caracteres e fragmentos adjacentes que foram separados incorretamente durante a geração do PDF
            start_idx = idx
            end_idx = idx

            while start_idx > 0:
                prev_w = words_on_page[start_idx - 1]
                curr_w = words_on_page[start_idx]

                if abs(prev_w[3] - curr_w[3]) < 5:
                    gap = curr_w[0] - prev_w[2]
                    if -2 <= gap <= 1.5:
                        start_idx -= 1
                        continue
                elif prev_w[4].endswith('-') and curr_w[1] >= prev_w[3] - 5:
                    start_idx -= 1
                    continue
                break

            while end_idx < len(words_on_page) - 1:
                curr_w = words_on_page[end_idx]
                next_w = words_on_page[end_idx + 1]

                if abs(curr_w[3] - next_w[3]) < 5:
                    gap = next_w[0] - curr_w[2]
                    if -2 <= gap <= 1.5:
                        end_idx += 1
                        continue
                elif curr_w[4].endswith('-') and next_w[1] >= curr_w[3] - 5:
                    end_idx += 1
                    continue
                break

            self.selected_text = self._highlight_and_extract(meta, start_idx, end_idx)

            # Normalização de texto para uso posterior na busca contextual (Fallback)
            def clean_word(w):
                if not w: return ""
                s = ''.join(c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn')
                return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

            for i in range(start_idx, end_idx + 1):
                target_word_clean += clean_word(words_on_page[i][4])

            is_small_word = len(target_word_clean) < 3

            if (not target_word_clean or target_word_clean.isdigit() or not re.search(r'[a-zA-Z]', target_word_clean)):
                return

            def get_valid_pdf_words(start_i, step, count):
                res = []
                curr = start_i + step
                while 0 <= curr < len(words_on_page) and len(res) < count:
                    w = clean_word(words_on_page[curr][4])
                    if w: res.append(w)
                    curr += step
                return res

            pdf_prev_words = get_valid_pdf_words(start_idx, -1, 10)
            pdf_next_words = get_valid_pdf_words(end_idx, 1, 10)

        else:
            self.canvas.delete("selection_highlight")
            self.selected_text = ""

        is_figure_mode = not clicked_on_text

        # Conversão de escala de tela (Pixels) para Escala do Editor (Pontos)
        pdf_x = (canvas_x - target_meta["x_start"]) * target_meta["scale_factor"]
        pdf_y = (canvas_y - target_meta["y_start"]) * target_meta["scale_factor"]

        tex_factor = 72.27 / 72.0
        pdf_x *= tex_factor
        pdf_y *= tex_factor

        page_num = target_meta["page_num"]

        try:
            # Comando de comunicação com a engine SyncTeX externa
            synctex_cmd = 'synctex'
            if hasattr(self.app, 'latex_compiler') and self.app.latex_compiler:
                exe_path = Path(self.app.latex_compiler).parent / "synctex.exe"
                if exe_path.exists():
                    synctex_cmd = str(exe_path)

            cmd = [synctex_cmd, 'edit', '-o', f"{page_num}:{pdf_x}:{pdf_y}:{self.current_pdf_path}"]
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore',
                                    creationflags=flags)

            lines_found = re.findall(r'Line:(\d+)', result.stdout)
            files_found = re.findall(r'Input:(.+?)\n', result.stdout + "\n")

            valid_results = [(int(l), f.strip()) for l, f in zip(lines_found, files_found) if int(l) > 0]

            if not valid_results:
                return

            line_num, input_file = valid_results[0]

            # Navegação segura contra pastas com nomes especiais ou acentos não suportados pelo CLI
            def open_sync_file(file_path_str):
                if not file_path_str: return False
                p = Path(file_path_str)

                if not p.is_absolute():
                    p = self.app.project_dir / p

                if not p.exists():
                    raw_stem = Path(file_path_str).stem
                    clean_stem = re.sub(r'[^a-zA-Z0-9]', '', raw_stem).lower()

                    if clean_stem:
                        for f in self.app.project_dir.rglob("*.tex"):
                            f_clean = re.sub(r'[^a-zA-Z0-9]', '', f.stem).lower()
                            if clean_stem in f_clean or f_clean in clean_stem:
                                p = f
                                break

                if p.exists() and p.suffix.lower() == '.tex':
                    if not self.app.active_file or p.resolve() != self.app.active_file.resolve():
                        self.app._open_file(p)
                    return True
                return False

            open_sync_file(input_file)
            total_lines = int(self.app.editor.index('end-1c').split('.')[0])

            if line_num >= total_lines - 1 and len(valid_results) > 1:
                line_num, input_file = valid_results[1]
                open_sync_file(input_file)
                total_lines = int(self.app.editor.index('end-1c').split('.')[0])

            self.app._switch_center_view('editor')
            self.app.editor.tag_remove("sel", "1.0", "end")

            # Avaliação de intenção de clique: Verifica se o usuário de fato queria focar na imagem
            # ou se clicou em uma legenda próxima.
            if not clicked_on_text:
                sync_line_text = self.app.editor.get(f"{line_num}.0", f"{line_num}.end").lower()
                if any(tag in sync_line_text for tag in
                       ["\\includegraphics", "\\begin{figure}", "\\caption", "\\begin{table}"]):
                    is_figure_mode = True

            # Recorte local para aumentar a performance da busca de equivalência (Fallback)
            start_search_line = max(1, line_num - 300)
            end_search_line = min(total_lines, line_num + 300)
            chunk_text = self.app.editor.get(f"{start_search_line}.0", f"{end_search_line}.end")

            # Lógica otimizada para identificar o bloco de código correspondente à figura
            if is_figure_mode:
                lines = chunk_text.splitlines()
                best_line = None
                best_score = float('inf')

                for i, line in enumerate(lines):
                    l = line.lower()
                    if any(tag in l for tag in ["\\includegraphics", "\\begin{figure}", "\\caption", "\\begin{table}"]):
                        real_line = start_search_line + i
                        dist = abs(real_line - line_num)
                        if dist < best_score:
                            best_score = dist
                            best_line = real_line

                if best_line:
                    pos = f"{best_line}.0"
                    self.app.editor.see(pos)
                    self.app.editor.mark_set("insert", pos)
                    self.app.editor.tag_add("sel", f"{best_line}.0", f"{best_line}.0 lineend")
                    self.app.editor.focus_set()
                return

            # Lógica de equivalência para texto. Garante alta precisão ao focar no alvo usando as palavras vizinhas.
            editor_words = []
            for m in re.finditer(r'[a-zA-ZÀ-ÿ0-9]+', chunk_text):
                if m.start() > 0 and chunk_text[m.start() - 1] == '\\':
                    continue

                cln = clean_word(m.group())
                if cln:
                    editor_words.append({
                        'word_clean': cln,
                        'start': m.start(),
                        'end': m.end()
                    })

            best_match_idx = -1
            best_score = -float('inf')

            MIN_SCORE = 3000 if is_small_word else 2000

            for i, ew in enumerate(editor_words):
                is_match = (ew['word_clean'] == target_word_clean) or \
                           (len(ew['word_clean']) > 1 and len(target_word_clean) > 1 and \
                            (ew['word_clean'] in target_word_clean or target_word_clean in ew['word_clean']))

                if not is_match:
                    continue

                score = 0
                hits = 0

                editor_prev_words = [w['word_clean'] for w in editor_words[max(0, i - 15):i]]
                editor_next_words = [w['word_clean'] for w in editor_words[i + 1:min(len(editor_words), i + 16)]]

                weight = 2000 if is_small_word else 1000

                for pw in pdf_prev_words:
                    if pw in editor_prev_words:
                        score += weight
                        hits += 1

                for nw in pdf_next_words:
                    if nw in editor_next_words:
                        score += weight
                        hits += 1

                if is_small_word and hits < 2:
                    continue

                lines_before = chunk_text[:ew['start']].count('\n')
                match_line_num = start_search_line + lines_before
                dist = abs(match_line_num - line_num)
                score -= dist

                if score > best_score:
                    best_score = score
                    best_match_idx = i

            if best_match_idx != -1 and best_score >= MIN_SCORE:
                ew = editor_words[best_match_idx]

                lines_before_start = chunk_text[:ew['start']].count('\n')
                last_newline_start = chunk_text.rfind('\n', 0, ew['start'])
                col_start = ew['start'] - (last_newline_start + 1)
                final_line_start = start_search_line + lines_before_start

                lines_before_end = chunk_text[:ew['end']].count('\n')
                last_newline_end = chunk_text.rfind('\n', 0, ew['end'])
                col_end = ew['end'] - (last_newline_end + 1)
                final_line_end = start_search_line + lines_before_end

                start_pos = f"{final_line_start}.{col_start}"
                end_pos = f"{final_line_end}.{col_end}"

                self.app.editor.see(start_pos)
                self.app.editor.mark_set("insert", start_pos)
                self.app.editor.tag_add("sel", start_pos, end_pos)
                self.app.editor.focus_set()
            else:
                self.app.editor.see(f"{line_num}.0")
                self.app.editor.mark_set("insert", f"{line_num}.0")
                self.app.editor.focus_set()

        except Exception as e:
            self.app.log_line(f"Erro SyncTeX: {e}")