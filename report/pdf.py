import tempfile

from fpdf import FPDF

from report.models import ReportOutput

FONT_DIR = "/usr/share/fonts/truetype/dejavu"

PAGE_W = 210
PAGE_H = 297
M_L = 15
M_R = 15
M_T = 22
M_B = 18
CW = PAGE_W - M_L - M_R

C = {
    "bg": (245, 246, 249),
    "card": (255, 255, 255),
    "border": (225, 231, 242),
    "divider": (220, 226, 238),
    "text": (18, 28, 46),
    "text2": (54, 67, 88),
    "muted": (98, 112, 132),
    "muted2": (152, 163, 178),
    "navy": (12, 21, 38),
    "navy2": (22, 38, 64),
    "gold": (192, 151, 52),
    "teal": (28, 174, 166),
    "seo": (14, 181, 126),
    "geo": (212, 142, 20),
    "aeo": (120, 82, 218),
    "score_high": (14, 181, 126),
    "score_med": (212, 138, 24),
    "score_low": (220, 58, 78),
}

DIM_COLORS = {
    "SEO": ("seo", "seo"),
    "GEO": ("geo", "geo"),
    "AEO": ("aeo", "aeo"),
}


def _score_color(s: float):
    if s >= 66:
        return C["score_high"]
    if s >= 33:
        return C["score_med"]
    return C["score_low"]


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", (PAGE_W, PAGE_H))
        self.set_margins(M_L, M_T, M_R)
        self.set_auto_page_break(True, M_B)
        try:
            self.add_font("DejaVu", "", f"{FONT_DIR}/DejaVuSans.ttf")
            self.add_font("DejaVu", "B", f"{FONT_DIR}/DejaVuSans-Bold.ttf")
        except RuntimeError:
            self.add_font("Helvetica", "", "", uni=True)
            self.add_font("Helvetica", "B", "", uni=True)
        self._company_name = ""

    def _rr(self, x, y, w, h, style="F", r=4):
        self.rect(x, y, w, h, style, round_corners=True, corner_radius=r)

    def _ensure_space(self, h):
        if self.get_y() + h > PAGE_H - M_B - 2:
            self.add_page()

    def _card(self, x, y, w, h, bg=None, r=5):
        if bg is None:
            bg = C["card"]
        self.set_fill_color(*C["card"])
        self.set_draw_color(*C["border"])
        self.set_line_width(0.18)
        self.rect(x, y, w, h, "DF")

    def header(self):
        if self.page_no() <= 1:
            return
        self.set_fill_color(*C["navy"])
        self.rect(0, 0, PAGE_W, 10.5, "F")
        self.set_fill_color(*C["gold"])
        self.rect(0, 10.5, PAGE_W, 0.7, "F")
        self.set_xy(M_L, 2.5)
        self.set_font("DejaVu", "B", 7.2)
        self.set_text_color(*C["gold"])
        self.cell(50, 6, "COMPLIANCE REPORT")
        self.set_font("DejaVu", "", 7)
        self.set_text_color(170, 186, 210)
        name = self._company_name[:52] if self._company_name else ""
        self.cell(0, 6, f"{name}  \u00b7  SEO / GEO / AEO", align="R")
        self.set_y(M_T)

    def footer(self):
        self.set_y(-(M_B - 2))
        self.set_draw_color(*C["divider"])
        self.set_line_width(0.2)
        self.line(M_L, self.get_y(), PAGE_W - M_R, self.get_y())
        self.set_font("DejaVu", "", 6.8)
        self.set_text_color(*C["muted2"])
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", align="C")

    def cover_page(self, report: ReportOutput):
        self._company_name = report.company_name
        self.add_page()
        self.set_fill_color(*C["navy"])
        self.rect(0, 0, PAGE_W, 128, "F")
        self.set_fill_color(*C["gold"])
        self.rect(0, 128, PAGE_W, 1.8, "F")

        self.set_xy(M_L, 18)
        self.set_font("DejaVu", "B", 7.5)
        self.set_text_color(*C["gold"])
        self.cell(0, 5, "C O M P L I A N C E   R E P O R T", align="C")

        self.set_xy(M_L, 30)
        self.set_font("DejaVu", "B", 26)
        self.set_text_color(255, 255, 255)
        self.multi_cell(CW, 11, report.company_name[:50], align="C")

        y = self.get_y() + 3
        self.set_xy(M_L, y)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(185, 200, 225)
        self.cell(0, 7, "SEO / GEO / AEO  Readiness Report", align="C")

        score = report.platforms[0].readiness_score if report.platforms else 0
        avg_score = round(sum(p.readiness_score for p in report.platforms) / len(report.platforms), 1) if report.platforms else 0
        sc = _score_color(avg_score)

        cw2, ch2 = 88, 60
        cx = (PAGE_W - cw2) / 2
        cy = 140
        self.set_fill_color(*C["card"])
        self.set_draw_color(*C["border"])
        self.rect(cx, cy, cw2, ch2, "DF")

        self.set_fill_color(*sc)
        self.rect(cx, cy, cw2, 3.5, "F")

        self.set_xy(cx, cy + 10)
        self.set_font("DejaVu", "B", 44)
        self.set_text_color(*sc)
        self.cell(cw2, 18, f"{avg_score:.0f}", align="C")

        self.set_xy(cx, cy + 30)
        self.set_font("DejaVu", "", 10)
        self.set_text_color(*C["muted"])
        self.cell(cw2, 6, "/ 100", align="C")

        bi, bw_in, by = 12, cw2 - 24, cy + 40
        self.set_fill_color(*C["divider"])
        self._rr(cx + bi, by, bw_in, 4.5, "F", 2.25)
        pct = min(avg_score / 100, 1.0)
        if pct > 0:
            self.set_fill_color(*sc)
            self._rr(cx + bi, by, bw_in * pct, 4.5, "F", 2.25)

        self.set_xy(cx, cy + 49)
        self.set_font("DejaVu", "B", 7.2)
        self.set_text_color(*C["muted"])
        self.cell(cw2, 5, "OVERALL COMPLIANCE SCORE", align="C")

        tile_y = 145
        tile_w = (CW - 12) / 3
        dim_order = ["SEO", "GEO", "AEO"]
        dim_map = {p.platform: p for p in report.platforms}

        for idx, label in enumerate(dim_order):
            pr = dim_map.get(label)
            val = pr.readiness_score if pr else 0
            col = C[DIM_COLORS.get(label, ("navy", "navy2"))[0]]
            tx = M_L + idx * (tile_w + 6)
            self._card(tx, tile_y + 68, tile_w, 48, r=6)
            self.set_fill_color(*col)
            self.rect(tx, tile_y + 68, tile_w, 3.5, "F")
            self.set_xy(tx + 6, tile_y + 80)
            self.set_font("DejaVu", "B", 7.5)
            self.set_text_color(*C["muted"])
            self.cell(tile_w - 12, 4, f"{label}  READINESS")
            self.set_xy(tx + 6, tile_y + 87)
            self.set_font("DejaVu", "B", 28)
            self.set_text_color(*col)
            self.cell(tile_w - 12, 14, f"{val:.0f}", align="R")
            self.set_xy(tx + 6, tile_y + 103)
            self.set_font("DejaVu", "", 7.5)
            self.set_text_color(*C["muted"])
            self.cell(tile_w - 12, 4, "out of 100", align="R")

    def section_title(self, title, subtitle=""):
        self._ensure_space(30)
        y0 = self.get_y() + 3
        self.set_fill_color(*C["navy"])
        self.rect(M_L, y0, 3.2, 13, "F")
        self.set_xy(M_L + 9, y0 + 0.8)
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(*C["text"])
        self.cell(CW - 12, 7, title)
        if subtitle:
            self.set_xy(M_L + 9, y0 + 8.5)
            self.set_font("DejaVu", "", 8.5)
            self.set_text_color(*C["muted"])
            self.cell(CW - 12, 5, subtitle)
        rule_y = y0 + 16
        self.set_draw_color(*C["divider"])
        self.set_line_width(0.22)
        self.line(M_L, rule_y, PAGE_W - M_R, rule_y)
        self.set_y(rule_y + 6)

    def body_text(self, text):
        self.set_font("DejaVu", "", 9.2)
        self.set_text_color(*C["text"])
        self.set_x(M_L)
        self.multi_cell(CW, 5.0, text, align="L")
        self.ln(4)

    def bullet_list(self, items):
        self.set_font("DejaVu", "", 9.2)
        self.set_text_color(*C["text"])
        for item in items:
            self._ensure_space(10)
            self.set_x(M_L + 4)
            self.set_text_color(*C["gold"])
            self.cell(4, 4.8, "\u203a")
            self.set_text_color(*C["text"])
            self.multi_cell(CW - 8, 4.8, f" {item}", align="L")
            self.ln(1.5)
        self.ln(2)

    def score_bar(self, score):
        self._ensure_space(22)
        bar_w = CW - 28
        pct = min(score / 100, 1.0)
        by = self.get_y()
        sc = _score_color(score)
        self.set_fill_color(*C["divider"])
        self._rr(M_L, by, bar_w, 7, "F", 3.5)
        if pct > 0:
            self.set_fill_color(*sc)
            self._rr(M_L, by, bar_w * pct, 5.5, "F", 3.5)
        label = f"{score:.0f} / 100"
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*sc)
        self.set_xy(M_L + bar_w + 4, by - 1)
        self.cell(22, 9, label)
        self.set_y(by + 14)

    def dimension_section(self, title, report):
        key = title.split()[0].lower()
        col_key = DIM_COLORS.get(title.split()[0] if title.split()[0] in DIM_COLORS else "SEO", ("navy", "navy2"))[0]
        accent = C.get(col_key, C["navy"])
        self.add_page()
        self.section_title(title)
        self.body_text(report.reasoning)
        self.score_bar(report.readiness_score)
        if report.recommendations:
            self.section_title("Recommendations")
            self.bullet_list(report.recommendations)

    def action_plan_section(self, report):
        self.add_page()
        self.section_title("Action Plan", subtitle="Prioritised recommendations across all dimensions")
        dim_cfg = {
            "SEO": C["seo"],
            "GEO": C["geo"],
            "AEO": C["aeo"],
        }
        items = []
        for pr in report.platforms:
            for rec in pr.recommendations:
                items.append((pr.platform, rec))
        for i, (dim, rec) in enumerate(items, 1):
            col = dim_cfg.get(dim, C["navy"])
            self._ensure_space(22)
            y0 = self.get_y()
            self._card(M_L, y0, CW, 22, r=5)
            self.set_fill_color(*col)
            self.rect(M_L, y0, 1.2, 22, "F")
            self.set_fill_color(*C["navy"])
            self._rr(M_L + 5, y0 + 6.5, 9, 9, "F", 4.5)
            self.set_xy(M_L + 5, y0 + 7)
            self.set_font("DejaVu", "B", 7.5)
            self.set_text_color(255, 255, 255)
            self.cell(9, 8, str(i), align="C")
            self.set_fill_color(*col)
            self._rr(M_L + 18, y0 + 7.5, 14, 7, "F", 3.5)
            self.set_xy(M_L + 18, y0 + 8)
            self.set_font("DejaVu", "B", 7)
            self.set_text_color(255, 255, 255)
            self.cell(14, 6, dim, align="C")
            self.set_xy(M_L + 37, y0 + 7)
            self.set_font("DejaVu", "", 9.2)
            self.set_text_color(*C["text"])
            self.cell(CW - 42, 5, rec[:80])
            self.set_y(y0 + 26)


def generate_pdf(report: ReportOutput, output_path: str) -> str:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.cover_page(report)
    pdf.add_page()
    pdf.section_title("Executive Summary")
    pdf.body_text(
        f"This report evaluates {report.company_name} ({report.domain_url}) "
        f"across three modern compliance dimensions: Search Engine Optimization (SEO), "
        f"Generative Engine Optimization (GEO), and Answer Engine Optimization (AEO)."
    )
    for pr in report.platforms:
        pdf.dimension_section(f"{pr.platform} Assessment", pr)
    pdf.action_plan_section(report)
    pdf.output(output_path)
    return output_path


def save_pdf_to_temp(report: ReportOutput) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = tmp.name
    generate_pdf(report, pdf_path)
    return pdf_path
