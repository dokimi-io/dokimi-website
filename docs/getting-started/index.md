# Getting started

!!! note "Before the first release"

    There is no release yet, so you install dokimi from source and build the orchestrator image
    yourself. A run currently stops right after planning and claiming the cluster, without a
    verdict. Getting that far already
    exercises the whole submission path against a real cluster.

1. **[Installation](installation.md):** what you need, and how to install the CLI.
2. **[Your first run](first-run.md):** a local multi-node cluster, the orchestrator image, and a
   first submitted run.
3. **[Using the CLI](using-the-cli.md):** every command and flag.

You need:

- **Python 3.14 or newer**, which `uv` fetches for you if you don't have it;
- **`uv` 0.12.18 or newer**;
- **Docker** (or another Docker-compatible runtime), for building the image and for the local
  cluster;
- for a real cluster: **Kubernetes 1.35 or newer**.
