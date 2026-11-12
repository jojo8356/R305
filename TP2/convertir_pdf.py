#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from urllib.parse import unquote, urlparse
from xml.etree.ElementTree import Element, SubElement, register_namespace, tostring
from zoneinfo import ZoneInfo

try:
    from markdown_it import MarkdownIt
    from pydyf import Stream as PDFStream
    from pydyf import String as PDFString
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import TextLexer, get_lexer_by_name
    from pygments.style import Style
    from pygments.token import (
        Comment,
        Error,
        Generic,
        Keyword,
        Name,
        Number,
        Operator,
        String,
    )
    from weasyprint import HTML, default_url_fetcher
except (ImportError, OSError) as exc:
    raise SystemExit(
        "Dépendances manquantes. Lancez : python3 -m pip install -r requirements-pdf.txt\n"
        f"Détail : {exc}"
    ) from exc

BASE = Path(__file__).resolve().parent
CSS_PRIMER = BASE / "assets" / "primer-markdown.css"
PDF_TITLE = "TP2"
PDF_AUTHOR = "Johan Polsinelli"
PDF_SUBJECT = "Mémoire virtuelle, processus et signaux sous Linux"
PDF_KEYWORDS = "TP2, R3.05, Linux, C, mémoire virtuelle, processus, signaux, Valgrind"
PDF_PRODUCER = "Unknown"
PDF_CREATOR = "Johan Polsinelli"
XMP_NAMESPACES = {
    "x": "adobe:ns:meta/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "pdf": "http://ns.adobe.com/pdf/1.3/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
}


class GitHubLightCode(Style):
    background_color = "#f6f8fa"
    default_style = ""
    styles: ClassVar[dict] = {
        Comment: "italic #6e7781",
        Keyword: "#cf222e",
        Keyword.Type: "#cf222e",
        Name.Function: "#8250df",
        Name.Class: "#8250df",
        Name.Builtin: "#953800",
        Name.Decorator: "#8250df",
        Name.Variable: "#953800",
        Number: "#0550ae",
        String: "#0a3069",
        Operator: "#cf222e",
        Error: "bg:#ffebe9 #cf222e",
        Generic.Heading: "bold #0550ae",
    }


TOKENS_AND_PRINT_CSS = """
:root {
    --fontStack-sansSerif: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
        "DejaVu Sans", Helvetica, Arial, sans-serif;
    --fgColor-default: #1f2328;
    --color-fg-default: #1f2328;
    --fgColor-muted: #59636e;
    --color-fg-muted: #59636e;
    --fgColor-accent: #0969da;
    --color-accent-fg: #0969da;
    --bgColor-default: #ffffff;
    --color-canvas-default: #ffffff;
    --bgColor-muted: #f6f8fa;
    --color-canvas-subtle: #f6f8fa;
    --bgColor-neutral-muted: #afb8c133;
    --color-neutral-muted: #afb8c133;
    --borderColor-default: #d1d9e0;
    --color-border-default: #d1d9e0;
    --borderColor-muted: #d8dee4;
    --color-border-muted: #d8dee4;
    --borderColor-accent-emphasis: #0969da;
    --fgColor-danger: #d1242f;
    --base-size-4: 4px;
    --base-size-8: 8px;
    --base-size-16: 16px;
    --base-size-24: 24px;
    --base-text-weight-semibold: 600;
}
@page {
    size: A4;
    margin: 18mm 17mm 19mm;
    @bottom-right {
        content: "Page " counter(page) " / " counter(pages);
        color: #59636e;
        font-family: "DejaVu Sans", sans-serif;
        font-size: 9px;
    }
}
html, body { background: #ffffff; color: #1f2328; }
body { margin: 0; }
.markdown-body {
    max-width: 100%;
    padding: 0;
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
    color: #1f2328;
    background: #ffffff;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3 { break-after: avoid; }
.markdown-body h1 { margin-top: 0; }
.markdown-body p, .markdown-body li { orphans: 2; widows: 2; }
.markdown-body p:has(+ pre) { break-after: avoid; }
.markdown-body p:has(+ pre.code-long) { break-before: page; }
.markdown-body pre, .markdown-body pre > code {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
}
.markdown-body pre {
    overflow: visible;
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 10.5px;
    line-height: 1.4;
    padding: 11px 13px;
    background: #f6f8fa;
    border: 1px solid #d1d9e0;
    border-radius: 6px;
    break-inside: avoid;
    page-break-inside: avoid;
    box-decoration-break: clone;
}
.markdown-body pre.code-long {
    break-before: page;
    break-inside: auto;
    page-break-inside: auto;
}
.markdown-body p:has(+ pre.code-long) + pre.code-long { break-before: auto; }
.markdown-body pre code { background: transparent; }
.markdown-body table { display: table; width: 100%; overflow: visible; }
.markdown-body tr { break-inside: avoid; }
.markdown-body img { max-width: 100%; }
.markdown-body a { color: #0969da; }
"""


def fenced_code(tokens, index, _options, _env) -> str:
    token = tokens[index]
    language = token.info.strip().split(maxsplit=1)[0].lower() if token.info.strip() else "text"
    language = re.sub(r"[^a-z0-9_+.-]", "", language) or "text"
    try:
        lexer = get_lexer_by_name(language, stripnl=False)
    except (ValueError, KeyError):
        lexer = TextLexer(stripnl=False)
    formatter = HtmlFormatter(style=GitHubLightCode, nowrap=True)
    colored = highlight(token.content, lexer, formatter)
    classe = "highlight code-long" if len(token.content.splitlines()) >= 60 else "highlight"
    return (
        f'<pre class="{classe}"><code class="language-{html.escape(language)}">'
        f"{colored}</code></pre>\n"
    )


def limited_fetcher(root: Path):
    root = root.resolve()

    def fetch(url: str):
        parsed = urlparse(url)
        if parsed.scheme != "file":
            raise ValueError(f"Ressource distante interdite dans le PDF : {url}")
        target = Path(unquote(parsed.path)).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Ressource hors du dossier du document : {url}")
        return default_url_fetcher(url)

    return fetch


def make_html(
    md_path: Path,
    *,
    title: str = PDF_TITLE,
    author: str = PDF_AUTHOR,
    subject: str = PDF_SUBJECT,
    keywords: str = PDF_KEYWORDS,
    created_at: str | None = None,
) -> str:
    markdown = md_path.read_text(encoding="utf-8")
    created_at = created_at or datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec="seconds")
    parser = MarkdownIt("default", {"html": False, "linkify": False})
    parser.renderer.rules["fence"] = fenced_code
    content = parser.render(markdown)
    css = CSS_PRIMER.read_text(encoding="utf-8")
    css_code = HtmlFormatter(style=GitHubLightCode).get_style_defs(".highlight")
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        f'<title>{html.escape(title)}</title>'
        f'<meta name="author" content="{html.escape(author, quote=True)}">'
        f'<meta name="description" content="{html.escape(subject, quote=True)}">'
        f'<meta name="keywords" content="{html.escape(keywords, quote=True)}">'
        f'<meta name="generator" content="{html.escape(PDF_CREATOR, quote=True)}">'
        f'<meta name="dcterms.created" content="{html.escape(created_at, quote=True)}">'
        f'<meta name="dcterms.modified" content="{html.escape(created_at, quote=True)}">'
        f"<style>{css}\n{css_code}\n{TOKENS_AND_PRINT_CSS}</style>"
        f'</head><body><article class="markdown-body">{content}</article></body></html>'
    )


def ajouter_metadonnees_xmp(document, pdf, producer: str) -> None:
    pdf.info["Producer"] = PDFString(producer)
    metadata = document.metadata
    for prefix, namespace in XMP_NAMESPACES.items():
        register_namespace(prefix, namespace)

    def tag(prefix: str, name: str) -> str:
        return f"{{{XMP_NAMESPACES[prefix]}}}{name}"

    xmp = Element(tag("x", "xmpmeta"))
    rdf = SubElement(xmp, tag("rdf", "RDF"))
    description = SubElement(rdf, tag("rdf", "Description"), {tag("rdf", "about"): ""})
    xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"

    if metadata.title:
        titles = SubElement(SubElement(description, tag("dc", "title")), tag("rdf", "Alt"))
        SubElement(titles, tag("rdf", "li"), {xml_lang: "x-default"}).text = metadata.title
    if metadata.authors:
        authors = SubElement(SubElement(description, tag("dc", "creator")), tag("rdf", "Seq"))
        for author in metadata.authors:
            SubElement(authors, tag("rdf", "li")).text = author
    if metadata.description:
        subjects = SubElement(SubElement(description, tag("dc", "description")), tag("rdf", "Alt"))
        SubElement(subjects, tag("rdf", "li"), {xml_lang: "x-default"}).text = metadata.description
    if metadata.keywords:
        SubElement(description, tag("pdf", "Keywords")).text = ", ".join(metadata.keywords)
        keywords = SubElement(SubElement(description, tag("dc", "subject")), tag("rdf", "Bag"))
        for keyword in metadata.keywords:
            SubElement(keywords, tag("rdf", "li")).text = keyword

    SubElement(description, tag("dc", "format")).text = "application/pdf"
    types = SubElement(SubElement(description, tag("dc", "type")), tag("rdf", "Bag"))
    SubElement(types, tag("rdf", "li")).text = "Text"
    languages = SubElement(SubElement(description, tag("dc", "language")), tag("rdf", "Bag"))
    SubElement(languages, tag("rdf", "li")).text = metadata.lang or "fr"
    SubElement(description, tag("pdf", "Producer")).text = producer
    if metadata.generator:
        SubElement(description, tag("xmp", "CreatorTool")).text = metadata.generator
    for name, value in (
        ("CreateDate", metadata.created),
        ("ModifyDate", metadata.modified),
        ("MetadataDate", metadata.modified),
    ):
        if value:
            SubElement(description, tag("xmp", name)).text = value

    packet = (
        b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        + tostring(xmp, encoding="utf-8")
        + b'\n<?xpacket end="w"?>'
    )
    stream = PDFStream([packet], {"Type": "/Metadata", "Subtype": "/XML"}, False)
    pdf.add_object(stream)
    pdf.catalog["Metadata"] = stream.reference


def run_linter(output: Path) -> None:
    linter = BASE / "lint_programmes.py"
    if not linter.is_file():
        raise FileNotFoundError(f"Linter introuvable : {linter}")
    command = [sys.executable, str(linter), "--root", str(BASE), "--output", str(output)]
    result = subprocess.run(command, check=False, text=True)
    if result.returncode != 0:
        logging.getLogger(__name__).warning(
            "Le linter a renvoyé %s ; le PDF sera tout de même créé.", result.returncode
        )


def main(argv: list[str] | None = None) -> int:
    command = argparse.ArgumentParser(
        description="Convertit un Markdown en PDF avec le style Markdown officiel GitHub Primer."
    )
    command.add_argument("--source", type=Path, default=BASE / "reponses.md")
    command.add_argument("--sortie", type=Path, default=None)
    command.add_argument("--rapport-lint", type=Path, default=BASE / "rapport_lint.md")
    command.add_argument("--titre-pdf", default=PDF_TITLE)
    command.add_argument("--auteur-pdf", default=PDF_AUTHOR)
    command.add_argument("--sujet-pdf", default=PDF_SUBJECT)
    command.add_argument("--mots-cles-pdf", default=PDF_KEYWORDS)
    command.add_argument("--producteur-pdf", default=PDF_PRODUCER)
    command.add_argument("--sans-lint", action="store_true", help="Convertir sans refaire le lint.")
    args = command.parse_args(argv)
    source = args.source.expanduser().resolve()
    sortie = (args.sortie or source.with_suffix(".pdf")).expanduser().resolve()
    if not source.is_file():
        command.error(f"Fichier Markdown introuvable : {source}")
    if not CSS_PRIMER.is_file():
        command.error(f"CSS officiel Primer introuvable : {CSS_PRIMER}")
    if source == sortie:
        command.error("Le PDF ne peut pas écraser le Markdown.")

    if not args.sans_lint:
        run_linter(args.rapport_lint.expanduser().resolve())
    document = HTML(
        string=make_html(
            source,
            title=args.titre_pdf,
            author=args.auteur_pdf,
            subject=args.sujet_pdf,
            keywords=args.mots_cles_pdf,
        ),
        base_url=str(source.parent),
        url_fetcher=limited_fetcher(source.parent),
    ).render()
    sortie.parent.mkdir(parents=True, exist_ok=True)
    temporaire = sortie.with_name(sortie.stem + ".tmp.pdf")

    def finaliser(pdf_document, pdf) -> None:
        ajouter_metadonnees_xmp(pdf_document, pdf, args.producteur_pdf)

    try:
        document.write_pdf(target=str(temporaire), finisher=finaliser)
        temporaire.replace(sortie)
    finally:
        temporaire.unlink(missing_ok=True)
    print(f"PDF créé : {sortie} ({len(document.pages)} pages)")
    if not args.sans_lint:
        print(f"Rapport du linter : {args.rapport_lint.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
