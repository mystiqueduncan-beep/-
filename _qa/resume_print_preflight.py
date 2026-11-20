"""Preflight the actual printed A4 résumé before merging its HTML changes.

Uses the same exporter as the downloadable PDF, checks page-level content
and printable text bounds, and writes review PNGs as CI artifacts.
"""
from pathlib import Path
import fitz
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "resume.pdf"
OUT = ROOT / "_qa" / "resume-preview"

def main():
    assert PDF.is_file() and PDF.stat().st_size > 20000, "PDF not rendered"
    reader = PdfReader(str(PDF))
    assert len(reader.pages) == 2, f"Expected two A4 pages, got {len(reader.pages)}"
    doc = fitz.open(str(PDF))
    assert len(doc) == 2
    page_terms = (
        ("黃博詩", "mystiqueduncan@gmail.com", "萬能科技大學", "核心管理能力"),
        ("Tomod's", "築心動物醫院", "Levi's"),
    )
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (page, expected) in enumerate(zip(doc, page_terms), 1):
        box = page.rect
        assert abs(box.width - 595.28) < 1 and abs(box.height - 841.89) < 1, (i, box)
        text = page.get_text()
        compressed = "".join(text.split())
        for term in expected:
            assert "".join(term.split()) in compressed, (i, term, text[:500])
        words = page.get_text("words")
        assert words, (i, "empty text page")
        outside = [w[:5] for w in words if w[0] < 4 or w[1] < 4 or w[2] > box.width-4 or w[3] > box.height-4]
        assert not outside, (i, "printed words outside A4", outside[:8])
        page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False).save(str(OUT / f"resume-page-{i}.png"))
        print(f"PAGE {i}: A4; words={len(words)}; page terms verified; no words clipped by paper edge")
    print("Two-page A4 résumé preflight passed; visual PNG evidence generated.")

if __name__ == "__main__":
    main()
