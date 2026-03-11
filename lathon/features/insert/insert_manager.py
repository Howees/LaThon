from lathon.features.insert.table_insert import TableInputDialog
from lathon.features.insert.figure_insert import FigureInputDialog
from lathon.features.insert.image_table_insert import ImageTableInputDialog
from lathon.features.insert.formula_insert import FormulaInputDialog

class InsertManager:
    """Gerencia a criação e inserção dos blocos de código gerados pelos Assistentes."""
    def __init__(self, app, editor):
        self.app = app
        self.editor = editor

    def open_table_wizard(self):
        res = TableInputDialog(self.app).get_data()
        if res:
            r, c, cap, lbl = res
            layout = "|" + "c|" * c
            latex = f"\\begin{{table}}[h]\n\t\\centering\n\t\\begin{{tabular}}{{{layout}}}\n\t\t\\hline\n"
            for _ in range(r):
                row_content = " & ".join([f"Conteúdo Coluna {i+1}" for i in range(c)])
                latex += f"\t\t{row_content} \\\\\n\t\t\\hline\n"
            latex += f"\t\\end{{tabular}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{table}}\n"
            self.editor.insert("insert", latex)

    def open_figure_wizard(self):
        res = FigureInputDialog(self.app).get_data()
        if res:
            path, w_percent, cap, lbl = res
            try: w_float = float(w_percent) / 100
            except ValueError: w_float = 0.8
            latex = f"\\begin{{figure}}[h]\n\t\\centering\n\t\\includegraphics[width={w_float}\\textwidth]{{{path}}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{figure}}\n"
            self.editor.insert("insert", latex)

    def open_image_table_wizard(self):
        res = ImageTableInputDialog(self.app).get_data()
        if res:
            r, img_percent, cap, lbl = res
            try: w_float = float(img_percent) / 100
            except ValueError: w_float = 0.4
            latex = f"\\begin{{table}}[h]\n\t\\centering\n\t\\begin{{tabular}}{{|m{{0.45\\textwidth}}|c|}}\n\t\t\\hline\n"
            latex += "\t\t\\textbf{Descrição} & \\textbf{Imagem} \\\\\n\t\t\\hline\n"
            for i in range(r):
                latex += f"\t\tDigite a descrição aqui & \\includegraphics[width={w_float}\\textwidth]{{SUA_FIGURA_AQUI}} \\\\\n\t\t\\hline\n"
            latex += f"\t\\end{{tabular}}\n\t\\caption{{{cap}}}\n\t\\label{{{lbl}}}\n\\end{{table}}\n"
            self.editor.insert("insert", latex)

    def open_formula_wizard(self):
        res = FormulaInputDialog(self.app).get_data()
        if res:
            mode, formula = res
            if not formula.strip(): return
            if mode == "inline":
                latex = f"${formula.strip()}$ "
            else:
                latex = f"\\begin{{equation}}\n\t{formula.strip()}\n\t\\label{{eq:}}\n\\end{{equation}}\n"
            self.editor.insert("insert", latex)