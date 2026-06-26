---
title: "{{profile.name}}"
description: "{{profile.site_description}}"
stylesheet: assets/css/site.css
body_class: page
---

::: {.header}
::: {.intro}
# {{profile.name}}

{{profile.title}}
:::

::: {.links}
[Resume](resume.html) [PDF](outputs/pdf/resume.pdf)
[Community](community.html)
:::
:::

::: {.about}
## About me

::: {.text}
{{> content/sections/about.md}}
:::
:::

::: {.details}
## Focus

{{skills.focus}}
:::
