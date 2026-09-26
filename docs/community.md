# Community

## Source code

dokimi is developed on GitHub, at
[github.com/dokimi-io/dokimi](https://github.com/dokimi-io/dokimi). The repository contains the
CLI, the orchestrator, the test environment, and the guides this site is based on.

## Questions, bugs and ideas

Open an issue on [GitHub](https://github.com/dokimi-io/dokimi/issues). If you'd like to change
something bigger, please open an issue before a pull request, so we can agree on the direction
first.

## Contributing

The repository's `docs/setup.md` covers a development environment, and the four checks CI runs:

```console
$ uv sync --locked --all-extras
$ uv run ruff check .
$ uv run ruff format --check .
$ uv run mypy
$ uv run pytest
```

None of them needs a cluster.

## License

dokimi is released under the [MIT License](https://github.com/dokimi-io/dokimi/blob/main/LICENSE).

## The mascot

The mascot is a **vaquita**, *Phocoena sinus*: the smallest porpoise in the world, found only in
the northern Gulf of California, and critically endangered. Like all porpoises, it finds its way
by sound: it sends out clicks and listens for what comes back. That is not so different from
testing a network.

**dokimi** is Greek for "test" or "trial" (δοκιμή), a small nod to Kubernetes, whose name is
Greek too.
