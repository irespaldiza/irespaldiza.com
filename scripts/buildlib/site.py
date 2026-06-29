import shutil

from .paths import (
    ASSETS_DIR,
    PUBLIC_CNAME,
    PUBLIC_DIR,
    PUBLIC_FAVICON,
    PUBLIC_NOJEKYLL,
    ROOT,
)


def site_nav(prefix=""):
    return (
        "::: {.site-nav}\n"
        f"[Home]({prefix}index.html) "
        f"[Resume]({prefix}resume.html) "
        f"[PDF]({prefix}outputs/pdf/resume.pdf) "
        f"[Community]({prefix}community.html)\n"
        ":::"
    )


def page_context(context, prefix):
    page = dict(context)
    site = dict(context.get("site", {}))
    site["nav"] = site_nav(prefix)
    page["site"] = site
    return page


def prepare_public_site():
    shutil.rmtree(PUBLIC_DIR, ignore_errors=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", ASSETS_DIR, dirs_exist_ok=True)
    shutil.copy2(ROOT / "favicon.ico", PUBLIC_FAVICON)
    if (ROOT / "CNAME").exists():
        shutil.copy2(ROOT / "CNAME", PUBLIC_CNAME)
    PUBLIC_NOJEKYLL.write_text("", encoding="utf-8")
