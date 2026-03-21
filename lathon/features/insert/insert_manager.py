from tkinter import messagebox
from lathon.features.insert.table_insert import TableInputDialog, ImageTableInputDialog
from lathon.features.insert.figure_insert import FigureInputDialog
from lathon.features.insert.formula_insert import FormulaInputDialog


class InsertManager:
    """Gerencia a criação e inserção dos blocos de código gerados pelos Assistentes."""

    def __init__(self, app, editor):
        self.app = app
        self.editor = editor

    def _ensure_package(self, package_name):
        """Verifica se o pacote já existe no documento e injeta automaticamente se faltar."""
        content = self.editor.get("1.0", "end")
        if f"\\usepackage{{{package_name}}}" in content or f"{{{package_name}}}" in content:
            return

        idx = self.editor._textbox.search(r"\begin{document}", "1.0", stopindex="end")
        if idx:
            self.editor.insert(idx, f"\\usepackage{{{package_name}}}\n")
            return

        idx_doc = self.editor._textbox.search(r"\documentclass", "1.0", stopindex="end")
        if idx_doc:
            self.editor.insert(f"{idx_doc} lineend", f"\n\\usepackage{{{package_name}}}")
            return

        messagebox.showinfo("Dependência Detectada",
                            f"O seu código gerado requer o pacote '{package_name}'.\n\n"
                            f"Por favor, verifique se o comando "
                            f"'\\usepackage{{{package_name}}}' está no preâmbulo do seu arquivo principal (main.tex).")

    def open_table_wizard(self):
        res = TableInputDialog(self.app).get_data()
        if res:
            matrix, col_widths, cap, lbl, valign, halign, border_style = res
            if not matrix: return

            self._ensure_package("array")

            needs_booktabs = border_style in ["Booktabs", "Booktabs Duplo", "Zebrada", "Zebrada + Cabeçalho",
                                              "Cabeçalho Destacado"]
            needs_xcolor = "Zebrada" in border_style or "Cabeçalho" in border_style

            if needs_booktabs: self._ensure_package("booktabs")
            if needs_xcolor: self._ensure_package("[table]{xcolor}")

            r = len(matrix)
            c = len(matrix[0]) if r > 0 else 0
            is_resized = any(w != 50 for w in col_widths)

            v_map = {"Topo": "p", "Meio": "m", "Base": "b"}
            h_map = {"Esquerda": "\\raggedright", "Centro": "\\centering", "Direita": "\\raggedleft"}

            v_col = v_map.get(valign, "m")
            h_cmd = h_map.get(halign, "\\centering")

            # --- Lógica de Bordas Verticais (Layout) ---
            col_sep = "|" if border_style in ["Grade", "Zebrada + Grade"] else (
                "||" if border_style == "Grade Dupla" else "")

            if is_resized:
                layout_parts = [f"{v_col}{{{(w / 800.0):.2f}\\textwidth}}" for w in col_widths]
            else:
                layout_parts = [{"Esquerda": "l", "Centro": "c", "Direita": "r"}.get(halign, "c")] * c

            layout = col_sep + col_sep.join(layout_parts) + col_sep if col_sep else "".join(layout_parts)

            # --- Lógica de Linha Superior ---
            top_line = ""
            if border_style in ["Grade", "Horizontais", "Zebrada + Grade"]:
                top_line = "\\hline\n"
            elif border_style in ["Grade Dupla", "Horizontais Duplas"]:
                top_line = "\\hline\\hline\n"
            elif needs_booktabs:
                top_line = "\\toprule\n"

            latex = f"\\begin{{table}}[h]\n\t\\centering\n"
            if "Zebrada" in border_style: latex += "\t\\rowcolors{2}{gray!15}{white}\n"
            latex += f"\t\\begin{{tabular}}{{{layout}}}\n\t\t{top_line}"

            for i, row in enumerate(matrix):
                if "Cabeçalho" in border_style and i == 0: latex += "\t\t\\rowcolor{blue!15}\n"

                parts = []
                for c_idx, cell in enumerate(row):
                    val = str(cell) if cell else ""
                    if is_resized:
                        val = val.replace('\n', ' \\newline ') if val else '~'
                    else:
                        val = val.replace('\n', ' ') if val else ' '
                        if not val.strip(): val = "~"

                    if is_resized:
                        parts.append(f"{h_cmd}\\arraybackslash " + val)
                    else:
                        parts.append(val)

                row_content = " & ".join(parts)
                end_cmd = " \\tabularnewline\n" if is_resized else " \\\\\n"

                current_row_sep = ""
                if border_style in ["Grade", "Horizontais", "Zebrada + Grade"]:
                    current_row_sep = "\t\t\\hline\n"
                elif border_style in ["Grade Dupla", "Horizontais Duplas"]:
                    current_row_sep = "\t\t\\hline\\hline\n"
                elif border_style == "Booktabs Duplo" and i == 0:
                    current_row_sep = "\t\t\\midrule\\midrule\n"
                elif needs_booktabs and i == 0:
                    current_row_sep = "\t\t\\midrule\n"

                latex += f"\t\t{row_content}{end_cmd}{current_row_sep}"

            # --- Lógica de Linha Inferior ---
            if needs_booktabs: latex += f"\t\t\\bottomrule\n"

            latex += f"\t\\end{{tabular}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{table}}\n"
            self.editor.insert("insert", latex)

    def open_image_table_wizard(self):
        res = ImageTableInputDialog(self.app).get_data()
        if res:
            matrix, col_widths, cap, lbl, valign, halign, border_style = res
            if not matrix: return

            self._ensure_package("array")
            self._ensure_package("graphicx")  # <- MUDANÇA: Garante pacote de imagens

            needs_booktabs = border_style in ["Booktabs", "Booktabs Duplo", "Zebrada", "Zebrada + Cabeçalho",
                                              "Cabeçalho Destacado"]
            needs_xcolor = "Zebrada" in border_style or "Cabeçalho" in border_style

            if needs_booktabs: self._ensure_package("booktabs")
            if needs_xcolor: self._ensure_package("[table]{xcolor}")

            r = len(matrix)
            c = len(matrix[0]) if r > 0 else 0

            v_map = {"Topo": "p", "Meio": "m", "Base": "b"}
            h_map = {"Esquerda": "\\raggedright", "Centro": "\\centering", "Direita": "\\raggedleft"}

            v_col = v_map.get(valign, "m")
            h_cmd = h_map.get(halign, "\\centering")

            col_sep = "|" if border_style in ["Grade", "Zebrada + Grade"] else (
                "||" if border_style == "Grade Dupla" else "")

            top_line = ""
            if border_style in ["Grade", "Horizontais", "Zebrada + Grade"]:
                top_line = "\\hline\n"
            elif border_style in ["Grade Dupla", "Horizontais Duplas"]:
                top_line = "\\hline\\hline\n"
            elif needs_booktabs:
                top_line = "\\toprule\n"

            layout_parts = [f"{v_col}{{{(w / 800.0):.2f}\\textwidth}}" for w in col_widths]
            layout = col_sep + col_sep.join(layout_parts) + col_sep if col_sep else "".join(layout_parts)

            latex = f"\\begin{{table}}[h]\n\t\\centering\n"
            if "Zebrada" in border_style: latex += "\t\\rowcolors{2}{gray!15}{white}\n"
            latex += f"\t\\begin{{tabular}}{{{layout}}}\n\t\t{top_line}"

            for i, row in enumerate(matrix):
                if "Cabeçalho" in border_style and i == 0: latex += "\t\t\\rowcolor{blue!15}\n"

                parts = []
                for c_idx, cell in enumerate(row):
                    if cell["type"] == "text":
                        val = cell["value"] if cell["value"] else ""
                        val = val.replace('\n', ' \\newline ') if val else '~'
                        parts.append(f"{h_cmd}\\arraybackslash " + val)
                    else:
                        path = cell["value"]
                        clean_path = path.replace("\\", "/") if path else "SUA_FIGURA_AQUI"
                        parts.append(f"{h_cmd}\\arraybackslash \\includegraphics[width=1\\linewidth]{{{clean_path}}}")

                row_content = " & ".join(parts)

                current_row_sep = ""
                if border_style in ["Grade", "Horizontais", "Zebrada + Grade"]:
                    current_row_sep = "\t\t\\hline\n"
                elif border_style in ["Grade Dupla", "Horizontais Duplas"]:
                    current_row_sep = "\t\t\\hline\\hline\n"
                elif border_style == "Booktabs Duplo" and i == 0:
                    current_row_sep = "\t\t\\midrule\\midrule\n"
                elif needs_booktabs and i == 0:
                    current_row_sep = "\t\t\\midrule\n"

                latex += f"\t\t{row_content} \\tabularnewline\n{current_row_sep}"

            if needs_booktabs: latex += f"\t\t\\bottomrule\n"

            latex += f"\t\\end{{tabular}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{table}}\n"
            self.editor.insert("insert", latex)

    def open_figure_wizard(self):
        res = FigureInputDialog(self.app).get_data()
        if res:
            path, w_percent, cap, lbl = res
            try:
                w_float = float(w_percent) / 100
            except ValueError:
                w_float = 0.8

            self._ensure_package("graphicx")  # <- MUDANÇA: Garante pacote de imagens

            latex = f"\\begin{{figure}}[h]\n\t\\centering\n\t\\includegraphics[width={w_float}\\textwidth]{{{path}}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{figure}}\n"
            self.editor.insert("insert", latex)

    def open_formula_wizard(self):
        res = FormulaInputDialog(self.app).get_data()
        if res:
            mode, formula = res
            if not formula.strip(): return

            # MUDANÇA: Listas super atualizadas com todas as abas!
            amsmath_triggers = ["pmatrix", "bmatrix", "vmatrix", "cases", "\\binom", "\\frac", "\\int", "\\sum",
                                "\\lim", "\\partial", "\\prod"]
            amssymb_triggers = ["\\infty", "\\approx", "\\neq", "\\leq", "\\geq", "\\pm", "\\times", "\\div",
                                "\\rightarrow", "\\leftarrow", "\\in", "\\notin", "\\subset", "\\cup", "\\cap",
                                "\\emptyset", "\\forall", "\\exists"]

            if any(x in formula for x in amsmath_triggers):
                self._ensure_package("amsmath")
            if any(x in formula for x in amssymb_triggers):
                self._ensure_package("amssymb")

            if mode == "inline":
                latex = f"${formula.strip()}$ "
            else:
                latex = f"\\begin{{equation}}\n\t{formula.strip()}\n\t\\label{{eq:}}\n\\end{{equation}}\n"
            self.editor.insert("insert", latex)