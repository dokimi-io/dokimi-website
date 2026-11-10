# dokimi-website

The source of [dokimi.io](https://dokimi.io), the website of
[dokimi](https://github.com/dokimi-io/dokimi), built with
[Zensical](https://zensical.org/), the successor to Material for MkDocs.

## Rule number one

**The site describes only what exists.** Anything not yet built is marked as planned, both in the
text and with a label:

```html
<span class="dk-status dk-status--works">works today</span>
<span class="dk-status dk-status--planned">planned</span>
```

When a feature lands in dokimi, update its page and its label in the same change. When in doubt,
the code repository's `docs/` and `README.md` are the source of truth.

## Working on the site

You need [`uv`](https://docs.astral.sh/uv/) 0.12.18 or newer.

```console
$ uv sync --locked
$ uv run zensical serve      # live preview on http://127.0.0.1:8000
$ uv run zensical build --strict
```

`--strict` is what CI runs, and it fails on broken links and missing pages, so run it before you
push.

## Layout

```text
docs/                   the pages, in Markdown
docs/assets/images/     the banner, the logo and the favicons
docs/stylesheets/       colours and the landing-page layout
overrides/main.html     the development notice at the top of every page
overrides/home.html     the landing page's hero section
mkdocs.yml              navigation, theme and Markdown extensions, which Zensical reads
```

The logo and favicon are circular crops of the mascot, a vaquita, taken from the first banner artwork.

## Deployment

Every push to `main` builds the site with `--strict` and deploys it to GitHub Pages. Pull requests
build it, without deploying.

GitHub Pages on the free plan needs a public repository. While this repository is private, the
deploy job is skipped and the build still runs. Going live, including pointing `dokimi.io` at
the site, is tracked as an issue.

## Dependencies

The site is built with Zensical, which the Material for MkDocs team wrote as its successor
when MkDocs 2.0 dropped the plugin system. It reads `mkdocs.yml` as it is. Two settings keep the
site as it looked under Material: `theme.variant: classic`, and the `zensical` namespace for
the icon shortcodes. Zensical 0.1 is a beta, so `pyproject.toml` caps it below 0.2, and
`uv.lock` pins the exact version.

Pages load no fonts or scripts from third-party servers: `theme.font` is off, so the system font
stack is used. The one outside request is the repository link in the header, which fetches the
star and fork counts from the GitHub API in the visitor's browser.

## License

[MIT](LICENSE), like dokimi itself.
