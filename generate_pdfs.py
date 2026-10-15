"""
PDF generator for NextReel documentation using fpdf2 + system Arial font.
Run: python generate_pdfs.py
"""
import re
import os
from fpdf import FPDF

ARIAL = "C:/Windows/Fonts/arial.ttf"
ARIAL_B = "C:/Windows/Fonts/arialbd.ttf"
ARIAL_I = "C:/Windows/Fonts/ariali.ttf"
ARIAL_BI = "C:/Windows/Fonts/arialbi.ttf"

BRAND_RED   = (229, 57, 53)
DARK_BG     = (18, 18, 28)
LIGHT_GREY  = (245, 245, 245)
MID_GREY    = (200, 200, 200)
DARK_TEXT   = (30, 30, 30)
MID_TEXT    = (90, 90, 90)
CODE_BG     = (240, 240, 245)


class DocPDF(FPDF):
    def __init__(self, doc_title="NextReel Documentation"):
        super().__init__()
        self.doc_title = doc_title
        self.add_font("Arial",  "",  ARIAL,    uni=True)
        self.add_font("Arial",  "B", ARIAL_B,  uni=True)
        self.add_font("Arial",  "I", ARIAL_I,  uni=True)
        self.add_font("Arial",  "BI",ARIAL_BI, uni=True)
        self.set_auto_page_break(auto=True, margin=20)

    # ── Header / Footer ──────────────────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "B", 8)
        self.set_text_color(*MID_TEXT)
        self.cell(0, 8, self.doc_title, align="L")
        self.set_font("Arial", "", 8)
        self.cell(0, 8, f"Page {self.page_no()-1}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*MID_GREY)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 7)
        self.set_text_color(*MID_TEXT)
        self.cell(0, 6, "NextReel — Final Semester Project  |  Confidential", align="C")

    # ── Cover Page ───────────────────────────────────────────────
    def cover(self, title, subtitle=""):
        self.add_page()
        # dark banner
        self.set_fill_color(*DARK_BG)
        self.rect(0, 0, self.w, 80, "F")
        # brand line
        self.set_font("Arial", "B", 26)
        self.set_text_color(*BRAND_RED)
        self.set_y(22)
        self.cell(0, 12, "▶  NextReel", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Arial", "", 11)
        self.set_text_color(220, 220, 220)
        self.cell(0, 7, "Movie Recommendation System", align="C", new_x="LMARGIN", new_y="NEXT")

        self.set_y(95)
        self.set_font("Arial", "B", 22)
        self.set_text_color(*DARK_TEXT)
        self.multi_cell(0, 11, title, align="C")
        self.ln(4)

        if subtitle:
            self.set_font("Arial", "I", 12)
            self.set_text_color(*MID_TEXT)
            self.multi_cell(0, 8, subtitle, align="C")
            self.ln(8)

        self.set_font("Arial", "", 10)
        self.set_text_color(*MID_TEXT)
        self.cell(0, 7, "Academic Year 2024/2025", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, "Final Semester Project", align="C", new_x="LMARGIN", new_y="NEXT")

        # accent line
        self.ln(10)
        self.set_draw_color(*BRAND_RED)
        self.set_line_width(0.8)
        self.line(self.l_margin + 30, self.get_y(), self.w - self.r_margin - 30, self.get_y())

    # ── Markdown → PDF ───────────────────────────────────────────
    def render_markdown(self, md_text):
        """Parse simplified markdown and render to PDF pages."""
        lines = md_text.splitlines()
        in_code = False
        code_buf = []
        toc_printed = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # ── Code block fence ──
            if line.startswith("```"):
                if not in_code:
                    in_code = True
                    code_buf = []
                else:
                    self._render_code_block(code_buf)
                    in_code = False
                    code_buf = []
                i += 1
                continue

            if in_code:
                code_buf.append(line)
                i += 1
                continue

            # ── Heading 1 ──
            if line.startswith("# ") and not line.startswith("## "):
                self.add_page()
                text = line[2:].strip()
                self.set_fill_color(*BRAND_RED)
                self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, 12, "F")
                self.set_font("Arial", "B", 15)
                self.set_text_color(255, 255, 255)
                self.set_x(self.l_margin)
                self.cell(0, 12, text, new_x="LMARGIN", new_y="NEXT")
                self.ln(4)
                self.set_text_color(*DARK_TEXT)

            # ── Heading 2 ──
            elif line.startswith("## "):
                text = line[3:].strip()
                self.ln(4)
                self.set_font("Arial", "B", 13)
                self.set_text_color(*BRAND_RED)
                self.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
                self.set_draw_color(*BRAND_RED)
                self.set_line_width(0.3)
                self.line(self.l_margin, self.get_y(), self.l_margin + 60, self.get_y())
                self.ln(3)
                self.set_text_color(*DARK_TEXT)

            # ── Heading 3 ──
            elif line.startswith("### "):
                text = line[4:].strip()
                self.ln(3)
                self.set_font("Arial", "B", 11)
                self.set_text_color(50, 50, 120)
                self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
                self.ln(1)
                self.set_text_color(*DARK_TEXT)

            # ── Heading 4 ──
            elif line.startswith("#### "):
                text = line[5:].strip()
                self.ln(2)
                self.set_font("Arial", "BI", 10)
                self.set_text_color(*DARK_TEXT)
                self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")

            # ── Horizontal rule ──
            elif line.strip() in ("---", "***", "___"):
                self.ln(2)
                self.set_draw_color(*MID_GREY)
                self.set_line_width(0.2)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.ln(3)

            # ── Table row ──
            elif line.startswith("|"):
                rows = self._collect_table(lines, i)
                self._render_table(rows)
                i += len(rows) + 1   # +1 for separator row
                continue

            # ── Bullet ──
            elif line.startswith(("- ", "* ", "+ ")):
                text = line[2:].strip()
                self._render_bullet(text, indent=0)

            elif re.match(r"^\s{2,4}[-*+] ", line):
                text = re.sub(r"^\s+[-*+] ", "", line).strip()
                self._render_bullet(text, indent=5)

            # ── Numbered list ──
            elif re.match(r"^\d+\. ", line):
                text = re.sub(r"^\d+\. ", "", line).strip()
                self._render_bullet(text, indent=0, bullet="•")

            # ── Blockquote ──
            elif line.startswith("> "):
                text = line[2:].strip()
                self.set_fill_color(*LIGHT_GREY)
                self.set_font("Arial", "I", 10)
                self.set_text_color(*MID_TEXT)
                self.set_x(self.l_margin + 5)
                self.multi_cell(self.w - self.l_margin - self.r_margin - 5, 6, text, fill=True)
                self.set_text_color(*DARK_TEXT)
                self.ln(1)

            # ── Blank line ──
            elif line.strip() == "":
                self.ln(2)

            # ── Normal paragraph ──
            else:
                self.set_font("Arial", "", 10)
                self.set_text_color(*DARK_TEXT)
                clean = self._strip_inline(line)
                self.multi_cell(0, 6, clean)
                self.ln(1)

            i += 1

    # ── Helpers ──────────────────────────────────────────────────
    def _strip_inline(self, text):
        """Remove bold/italic/code markdown markers for plain rendering."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*",     r"\1", text)
        text = re.sub(r"__(.+?)__",     r"\1", text)
        text = re.sub(r"_(.+?)_",       r"\1", text)
        text = re.sub(r"`(.+?)`",       r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        return text

    def _render_bullet(self, text, indent=0, bullet="•"):
        self.set_font("Arial", "", 10)
        self.set_text_color(*DARK_TEXT)
        clean = self._strip_inline(text)
        x0 = self.l_margin + indent
        self.set_x(x0)
        self.cell(5, 6, bullet)
        self.set_x(x0 + 5)
        self.multi_cell(self.w - x0 - self.r_margin - 5, 6, clean)
        self.ln(0.5)

    def _render_code_block(self, lines_buf):
        self.ln(2)
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(*MID_GREY)
        self.set_line_width(0.2)
        self.set_font("Arial", "", 8.5)
        self.set_text_color(30, 30, 100)
        text = "\n".join(lines_buf)
        # draw background rect
        line_h = 5
        n_lines = max(len(lines_buf), 1)
        rect_h = n_lines * line_h + 4
        self.rect(self.l_margin, self.get_y(), self.w - self.l_margin - self.r_margin, rect_h, "FD")
        saved_y = self.get_y() + 2
        self.set_xy(self.l_margin + 2, saved_y)
        for ln in lines_buf:
            self.set_x(self.l_margin + 2)
            self.cell(0, line_h, ln[:120], new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_text_color(*DARK_TEXT)

    def _collect_table(self, lines, start):
        rows = []
        i = start
        while i < len(lines) and lines[i].startswith("|"):
            row = [c.strip() for c in lines[i].split("|")[1:-1]]
            if not all(re.match(r"^[-:]+$", c) for c in row):
                rows.append(row)
            i += 1
        return rows

    def _render_table(self, rows):
        if not rows:
            return
        self.ln(2)
        col_count = len(rows[0])
        usable = self.w - self.l_margin - self.r_margin
        col_w = usable / col_count
        row_h = 7

        for ri, row in enumerate(rows):
            if ri == 0:
                self.set_fill_color(*DARK_BG)
                self.set_text_color(255, 255, 255)
                self.set_font("Arial", "B", 9)
            else:
                self.set_fill_color(250, 250, 255) if ri % 2 == 0 else self.set_fill_color(255, 255, 255)
                self.set_text_color(*DARK_TEXT)
                self.set_font("Arial", "", 9)

            self.set_x(self.l_margin)
            for ci, cell in enumerate(row):
                fill = (ri == 0) or (ri % 2 == 0)
                self.cell(col_w, row_h, self._strip_inline(cell)[:50], border=1, fill=fill)
            self.ln()

        self.ln(3)
        self.set_text_color(*DARK_TEXT)


# ── Build each PDF ─────────────────────────────────────────────────────────

def build_pdf(md_path, pdf_path, title, subtitle=""):
    print(f"  Building {pdf_path} ...")
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    # Replace em-dash and other special chars that may trip rendering
    content = content.replace("\u2014", "-").replace("\u2013", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')

    pdf = DocPDF(doc_title=title)
    pdf.cover(title, subtitle)
    pdf.add_page()
    pdf.render_markdown(content)
    pdf.output(pdf_path)
    size = os.path.getsize(pdf_path) // 1024
    print(f"    Done — {size} KB")


if __name__ == "__main__":
    base = "e:/Projects/Manoj/NextReel"

    docs = [
        (
            f"{base}/USER_GUIDE.md",
            f"{base}/NextReel_User_Guide.pdf",
            "NextReel User Guide",
            "Complete guide for end users of the NextReel movie recommendation platform",
        ),
        (
            f"{base}/ADMIN_GUIDE.md",
            f"{base}/NextReel_Admin_Guide.pdf",
            "NextReel Administrator Guide",
            "Technical setup, configuration, and management guide for system administrators",
        ),
        (
            f"{base}/PROJECT_DOCUMENTATION.md",
            f"{base}/NextReel_Project_Documentation.pdf",
            "NextReel — Full Project Documentation",
            "Complete academic documentation including architecture, algorithms, and defense Q&A",
        ),
    ]

    for md, pdf, title, subtitle in docs:
        build_pdf(md, pdf, title, subtitle)

    print("\nAll PDFs generated successfully!")
    print(f"Location: {base}/")
    for _, pdf, _, _ in docs:
        print(f"  {os.path.basename(pdf)}")
