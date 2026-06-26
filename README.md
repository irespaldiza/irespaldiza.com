# Professional Career Repository

This repository is the canonical source of truth for my professional career material.

It is designed to produce:

- PDF resumes
- Personal website content
- LinkedIn profile content
- Speaker bios
- Private company-specific resumes and cover letters outside version control

The source format is Markdown. Generated or adapted outputs should be derived from the files in `content/`, not edited as the source of truth.

This repository may be public. It must not include company-specific application material, cover letters, interview-process notes or tailored resumes for a specific employer. Those files belong in a local ignored directory such as `private/`.

Private contact details, such as email or phone number, also belong outside version control in `private/profile.yml`.

The website implementation is intentionally replaceable. GitHub Pages can serve the generated `site/` directory directly, or use another build pipeline later, as long as the Markdown content remains canonical.

## Structure

- `content/pages/index.md` - editable source for the public about page.
- `content/pages/resume.md` - editable composition for the resume.
- `content/data/profile.yml` - shared personal/profile metadata used across generated outputs.
- `private/profile.yml` - local-only private contact metadata. This file is ignored by git.
- `content/data/skills.yml` - competencies, technologies, focus areas and languages.
- `content/data/experience.yml` - structured professional experience.
- `content/data/community.yml` - structured community information.
- `content/data/publications.yml` - structured publication information.
- `content/data/training.yml` - structured training information.
- `content/data/positioning.yml` - target roles and high-level positioning.
- `content/data/backlog.yml` - career data TODOs not yet assigned to a public output.
- `content/sections/` - reusable Markdown prose sections.
- `outputs/` - public-safe generated or adapted deliverables.
- `private/` - local-only company-specific resumes, cover letters and application notes. This directory is ignored by git.
- `site/` - generated GitHub Pages website output directory.
- `templates/` - Pandoc templates for generated HTML outputs.
- `assets/css/` - website styling.
- `scripts/build.py` - expands shared profile variables and reusable Markdown sections, creates public Markdown, and calls Pandoc/Chrome.
- `Dockerfile` - containerized build environment for the same Python entrypoint.

## Build

The build logic lives in `scripts/build.py`.
Docker is the default execution environment for `make all`, `make site`, `make pdf` and `make clean`.
Local targets exist as `make local-site`, `make local-pdf`, `make local-all` and `make local-clean`.

```sh
make all
```

Local build:

```sh
make local-all
```

Containerized build:

```sh
make docker-all
```

Generated outputs:

- `site/index.html` - public about page.
- `site/resume.html` - public web resume.
- `site/community.html` - public community page.
- `site/talks/` - public talk pages.
- `site/organizing/` - public organizing pages.
- `site/outputs/pdf/resume.pdf` - generated PDF resume.

The current PDF pipeline generates `resume.html` first and then prints it to PDF with headless Chrome, so the PDF uses the same CSS as the web resume.

## Editable Files

Edit these files:

- `content/pages/index.md` - public about page composition.
- `content/pages/resume.md` - resume composition.
- `content/data/profile.yml` - name, title, contact placeholders, shared title and tagline.
- `private/profile.yml` - email, phone or other private contact details for private outputs.
- `content/data/skills.yml` - skills, technologies and languages.
- `content/data/experience.yml` - roles, dates, responsibilities and achievements.
- `content/data/community.yml` - community entries.
- `content/data/publications.yml` - publication entries.
- `content/data/training.yml` - training entries.
- `content/data/positioning.yml` - target roles and positioning.
- `content/data/backlog.yml` - unstructured TODOs and missing evidence to collect.
- `content/sections/` - reusable prose fragments.
- `assets/css/site.css` - about page styling.
- `assets/css/resume.css` - resume HTML and PDF styling.

Do not edit these generated files by hand:

- `site/`
- `build/`

Pipeline files should only be edited when changing how generation works:

- `Makefile`
- `templates/`
- `scripts/build.py`

## Reuse Model

Markdown sources can use shared profile fields:

```md
{{profile.name}}
{{profile.title}}
{{resume.tagline}}
```

Markdown sources can include reusable sections:

```md
{{> content/sections/professional-summary.md}}
```

Markdown sources can also use generated sections from structured YAML:

```md
{{skills.competencies}}
{{skills.technologies}}
{{resume.experience}}
```

The build renders these into `build/` first, then Pandoc generates the public HTML files. The resume PDF is generated from `resume.html` with headless Chrome. The Docker build path runs the same Python script inside a container with Pandoc and Chromium installed.

## Editing Rules

- Do not invent responsibilities, achievements or metrics.
- Add `TODO:` entries when information is missing.
- Keep experience bullets focused on ownership, architecture, decision making, leadership and impact.
- Keep technology lists out of experience sections unless a specific technology is central to the achievement.
- Keep Markdown as the canonical format.
- Never commit tailored resumes, cover letters, target-company notes or interview-process information.

## Next Data Needed

- Exact dates, titles and scope for Okteto, Paradigma Digital and BBVA.
- Platform scale: clusters, teams, environments, regions, workloads, users, developers or services supported.
- Concrete achievements with evidence: reliability, deployment frequency, developer experience, cost, security or scalability outcomes.
- Community talks, conference names, dates and topics.
- Languages and proficiency levels.
