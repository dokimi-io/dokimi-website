# Installation

The CLI runs on your machine or in CI. The orchestrator runs inside the cluster as a one-shot
Job, and you never install that: the CLI submits it.

## What you need

| | |
| --- | --- |
| Python | **3.14 or newer**. `uv` fetches it if your system has none |
| `uv` | **0.12.18 or newer**. This is enforced, because 0.12.18 fixes a path-traversal weakness during wheel installation |
| Kubernetes | **1.35 or newer**, with credentials that can create Jobs and ConfigMaps in the run's namespace, and, once, an administrator to apply `deploy/rbac.yaml` |
| A container registry | only if your cluster cannot reach `ghcr.io` |

Robot Framework is **not** required on your machine. It runs inside the cluster.

## Supported platforms

| Platform | Status |
| --- | --- |
| macOS, Apple silicon | supported and tested |
| Linux, x86_64 | supported and tested |
| macOS, Intel · Linux, arm64 | supported, not yet tested |
| Windows, through WSL2 | supported, not yet tested. WSL2 takes the Linux path |
| Windows, natively | not supported |

On WSL2, clone the repository inside the Linux filesystem (`~/…`), not under `/mnt/c/…`, where
executable bits are lost.

## Install `uv`

```console
$ curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS, Linux
$ brew install uv                                    # or with Homebrew
```

## Install dokimi from source

dokimi is not on PyPI yet. Install it from the repository:

```console
$ git clone https://github.com/dokimi-io/dokimi.git
$ cd dokimi
$ uv sync --locked
$ uv run dokimi --version
```

To get a `dokimi` command on your `PATH` instead of one behind `uv run`:

```console
$ uv tool install .
```

## Check the installation

```console
$ dokimi validate examples/worker-01-to-worker-02-udp.yaml
examples/worker-01-to-worker-02-udp.yaml is valid.

  name        worker-01-to-worker-02-udp
  pair        worker-01 -> worker-02
  test        iperf2 over udp
  ...
```

`validate` contacts nothing, so it works before you have a cluster.

## Cluster credentials

The CLI picks cluster credentials in this order:

1. `--kubeconfig` and `--context`, if either is given, and then only those;
2. otherwise, in-cluster service-account credentials, when it runs inside a pod;
3. otherwise, `$KUBECONFIG`, or `~/.kube/config`.

The second entry is why the same command works unchanged in a CI job that runs inside the
cluster it tests.

## Once per cluster: `deploy/rbac.yaml`

The Job a run submits authenticates as its own service account, not as you. To plan, it reads
the cluster's nodes, which is a cluster-wide permission. So an administrator applies this once
per cluster:

```console
$ kubectl apply -f deploy/rbac.yaml
```

It creates the `dokimi-iperf2` namespace, a `dokimi` service account in it, and a read-only
ClusterRole that allows `get` and `list` on nodes, and nothing else. Runs then pass
`--service-account dokimi`.

## The orchestrator image

A run is a reference to a container image. Once releases exist, the CLI will ship with the digest
of the image built from its own commit. **There is no release yet, so a source install has no
default image**, and `submit` says so instead of guessing:

```console
$ dokimi submit test.yaml
dokimi: this is a development build with no published orchestrator image, so
there is no default to submit. Pass an explicit reference or set DOKIMI_IMAGE.
```

Build the image yourself and point dokimi at it. [Your first run](first-run.md) shows how.
