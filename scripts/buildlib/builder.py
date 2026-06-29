import re
import shutil

from .collection_pages import build_organizing_pages, build_talk_pages
from .commands import run
from .context import build_context
from .markdown import render_source
from .paths import (
    BUILD_DIR,
    COMMUNITY_HTML,
    COMMUNITY_SOURCE,
    INDEX_HTML,
    INDEX_SOURCE,
    ORGANIZING_DIR,
    PRIVATE_RESUME,
    PRIVATE_RESUME_HTML,
    PUBLIC_DIR,
    PUBLIC_RESUME,
    RENDERED_COMMUNITY,
    RENDERED_INDEX,
    RENDERED_RESUME,
    RESUME_HTML,
    RESUME_PDF,
    RESUME_SOURCE,
    ROOT,
    TALKS_DIR,
)
from .pdf import html_to_pdf
from .resume import build_resume_html, public_resume
from .site import page_context, prepare_public_site


def build_site():
    context = build_context()

    prepare_public_site()

    render_source(INDEX_SOURCE, RENDERED_INDEX, page_context(context, ""))
    render_source(RESUME_SOURCE, RENDERED_RESUME, page_context(context, ""))
    render_source(COMMUNITY_SOURCE, RENDERED_COMMUNITY, page_context(context, ""))
    public_resume(RENDERED_RESUME, PUBLIC_RESUME)
    build_talk_pages(context)
    build_organizing_pages(context)

    run(
        [
            "pandoc",
            str(RENDERED_INDEX.relative_to(ROOT)),
            "--standalone",
            "--template",
            "templates/page.html",
            "--wrap=none",
            "--output",
            str(INDEX_HTML.relative_to(ROOT)),
        ]
    )

    run(
        [
            "pandoc",
            str(RENDERED_COMMUNITY.relative_to(ROOT)),
            "--standalone",
            "--template",
            "templates/page.html",
            "--wrap=none",
            "--output",
            str(COMMUNITY_HTML.relative_to(ROOT)),
        ]
    )

    build_resume_html(PUBLIC_RESUME, RESUME_HTML, "assets/css/resume.css")


def build_pdf():
    build_site()
    private_context = build_context(include_private=True)
    render_source(
        RESUME_SOURCE,
        RENDERED_RESUME,
        page_context(private_context, ""),
    )
    public_resume(RENDERED_RESUME, PRIVATE_RESUME)
    website = private_context["profile"].get("public_contact", {}).get("website", "")
    pdf_base_url = (
        website
        if re.match(r"^https?://", website)
        else f"https://{website}"
    )
    build_resume_html(
        PRIVATE_RESUME,
        PRIVATE_RESUME_HTML,
        "../assets/css/resume.css",
        pdf_base_url,
    )
    html_to_pdf(PRIVATE_RESUME_HTML, RESUME_PDF)


def clean():
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    shutil.rmtree(PUBLIC_DIR, ignore_errors=True)
    shutil.rmtree(TALKS_DIR, ignore_errors=True)
    shutil.rmtree(ORGANIZING_DIR, ignore_errors=True)
    for path in (ROOT / "index.html", ROOT / "resume.html", ROOT / "community.html"):
        path.unlink(missing_ok=True)
    for path in ROOT.glob("talks/*.html"):
        path.unlink(missing_ok=True)
    for path in ROOT.glob("organizing/*.html"):
        path.unlink(missing_ok=True)
    (ROOT / "outputs/pdf/resume.pdf").unlink(missing_ok=True)
