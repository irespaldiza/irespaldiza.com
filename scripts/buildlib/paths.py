from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "build"
PUBLIC_DIR = ROOT / "docs"

PROFILE_PATH = ROOT / "content/data/profile.yml"
PRIVATE_PROFILE_PATH = ROOT / "private/profile.yml"
SKILLS_PATH = ROOT / "content/data/skills.yml"
EXPERIENCE_PATH = ROOT / "content/data/experience.yml"
COMMUNITY_PATH = ROOT / "content/data/community.yml"
PUBLICATIONS_PATH = ROOT / "content/data/publications.yml"
TRAINING_PATH = ROOT / "content/data/training.yml"
INDEX_SOURCE = ROOT / "content/pages/index.md"
RESUME_SOURCE = ROOT / "content/pages/resume.md"
COMMUNITY_SOURCE = ROOT / "content/pages/community.md"

RENDERED_INDEX = BUILD_DIR / "index.md"
RENDERED_RESUME = BUILD_DIR / "resume.md"
RENDERED_COMMUNITY = BUILD_DIR / "community.md"
PUBLIC_RESUME = BUILD_DIR / "resume.public.md"
PRIVATE_RESUME = BUILD_DIR / "resume.private.md"
PRIVATE_RESUME_HTML = BUILD_DIR / "resume.private.html"

INDEX_HTML = PUBLIC_DIR / "index.html"
COMMUNITY_HTML = PUBLIC_DIR / "community.html"
RESUME_HTML = PUBLIC_DIR / "resume.html"
RESUME_PDF = PUBLIC_DIR / "outputs/pdf/resume.pdf"
TALKS_DIR = PUBLIC_DIR / "talks"
ORGANIZING_DIR = PUBLIC_DIR / "organizing"
ASSETS_DIR = PUBLIC_DIR / "assets"
PUBLIC_FAVICON = PUBLIC_DIR / "favicon.ico"
PUBLIC_CNAME = PUBLIC_DIR / "CNAME"
PUBLIC_NOJEKYLL = PUBLIC_DIR / ".nojekyll"
