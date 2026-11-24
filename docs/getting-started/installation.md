# Installation

The CLI runs on your machine or in CI. The orchestrator runs inside the cluster as a one-shot
Job, and you never install that: the CLI submits it.

## What you need

| | |
| --- | --- |
| Python | **3.14 or newer**. `uv` fetches it if your system has none |
| `uv` | **0.12.18 or newer**. This is enforced, because 0.12.18 fixes a path-traversal weakness during wheel installation |
| Kubernetes | **1.35 or newer**, with credentials that can create Jobs and ConfigMaps in the run's namespace, and, once, an administrator to apply `deploy/rbac.yaml`, which creates that namespace and the `dokimi` lock namespace |
| A container registry | only if your cluster cannot reach `ghcr.io`, or `quay.io` for Prometheus and node-exporter |

Robot Framework is **not** required on your machine. It runs inside the cluster.

## Supported platforms

| Platform | Status |
| --- | --- |
| macOS, Apple silicon | supported and tested |
| Linux, x86_64 | supported and tested |
| macOS, Intel · Linux, arm64 | supported, not yet tested |
| Windows, through WSL2 | supported and tested. WSL2 takes the Linux path |
| Windows, natively | not supported |

On WSL2, clone the repository inside the Linux filesystem (`~/…`), not under `/mnt/c/…`, where
every file shows as mode `0777` and file access is much slower. It was tested with the Docker
engine installed in the Linux distribution; Docker Desktop's WSL2 integration is expected to work,
but was not tested.

## Install `uv`

```console
$ curl -LsSf https://astral.sh/uv/install.sh | sh    # macOS, Linux
$ brew install uv                                    # or with Homebrew
```

## Install dokimi

Install the CLI from PyPI, as a tool of its own:

```console
$ uv tool install --python 3.14 'dokimi-io[robot]'
$ dokimi --version
dokimi 0.1.0
```

On PyPI it is called **`dokimi-io`**, because `dokimi` there is an unrelated project; the command
it installs is `dokimi`. `[robot]` adds Robot Framework, which reading a `.robot` test needs; a
test written in YAML runs without it. `--python 3.14` makes uv use, or download, a Python that
dokimi runs on: without it, uv takes the first Python it finds, and refuses when that one is
older. `pipx install --python python3.14 'dokimi-io[robot]'` works too, and each
[release](https://github.com/dokimi-io/dokimi/releases/tag/v0.1.0) also carries the wheel itself.

The release knows the `orchestrator` and `iperf2` images built with it, by digest, so a run needs
no image of yours. The release page lists them.

### From source

For development, or to try changes that aren't released yet, install from the repository:

```console
$ git clone https://github.com/dokimi-io/dokimi.git
$ cd dokimi
$ uv sync --locked --extra robot
$ uv run dokimi --version
```

To get a `dokimi` command on your `PATH` instead of one behind `uv run`:

```console
$ uv tool install '.[robot]'
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

Tab completion for bash, zsh and fish comes with the CLI: `dokimi completion <shell>` prints the
script. [Using the CLI](using-the-cli.md#completion) says how to load it.

## Cluster credentials

The CLI picks cluster credentials in this order:

1. `--kubeconfig` and `--context`, if either is given, and then only those;
2. otherwise, in-cluster service-account credentials, when it runs inside a pod;
3. otherwise, `$KUBECONFIG`, or `~/.kube/config`.

The second entry is why the same command works unchanged in a CI job that runs inside the
cluster it tests.

## Once per cluster: `deploy/rbac.yaml`

A run never creates a namespace, so submitting needs permissions only inside the run's
namespace. The Job a run submits authenticates as its own service account, not as you, and three
of the things it does are cluster-wide:

- it reads the cluster's **nodes**, to plan;
- it **lists ConfigMaps in every namespace**, to check that no other run is active, and takes a
  `Lease` in the `dokimi` namespace while it claims the cluster. Kubernetes cannot restrict a
  `list` by label, so this grant can read every ConfigMap in the cluster, including its data.
  That is the price of one run at a time per cluster;
- it **lists Services in every namespace**, to find a node-exporter or kube-state-metrics the
  cluster already runs, so that its Prometheus scrapes those, and the run does not deploy a
  second node-exporter.

The run's Prometheus runs as a second service account, `dokimi-prometheus`, which can read
pods, Services and endpoint slices in every namespace, to discover what it scrapes. It is
read-only.

So an administrator applies this once per cluster:

```console
$ kubectl apply -f deploy/rbac.yaml
```

It creates the `dokimi-iperf2` namespace for runs, the `dokimi` namespace for the run-start lock,
a `dokimi` service account, and the grants it needs, each commented with the phase that needs
it. Runs then pass `--service-account dokimi`.

Inside `dokimi-iperf2`, the grants let the Job:

- write its claim onto its own owner ConfigMap and read its own Job;
- create the ConfigMap, Deployment and Service of its Prometheus. No grant lets the Job delete
  them, because they are kept after the run;
- create, read, list and delete DaemonSets, for the node-exporter it deploys when the cluster
  has none and removes when it ends;
- create, read, list and delete Pods, for the client and server pod each test runs in, removed
  when the run ends, unless a run that didn't pass keeps them. There is no grant for
  `pods/exec`: a test is started over the network, not by running a command inside a pod.

The Job deletes nothing else. A run's owner, definition and Job go after the run, removed by
whoever fetched its reports, or by `dokimi cleanup`, with their own credentials.

### What you need yourself

You, or the CI job that submits, need only namespaced permissions in the run's namespace:

| Command | Needs |
| --- | --- |
| `submit`, `preflight` | `create` on Jobs and ConfigMaps; `get` on Pods and their `log`, and `list` on Jobs and Pods, to follow the run; and, once the reports are fetched, `get` and `delete` on ConfigMaps and `list` and `delete` on Jobs, to remove the run |
| `attach` | the same, without `create`; `get` on ConfigMaps also finds the run's results directory |
| `cleanup` | `get` on ConfigMaps, and `list` and `delete` on ConfigMaps, Pods, Services, ServiceAccounts, Jobs, Deployments, DaemonSets and StatefulSets |
| `prometheus` | `list` on Deployments and Pods and `get` on ConfigMaps, to find the run's Prometheus, and `create` on `pods/portforward`, to reach it |

A missing `delete` after a fetch is only a warning: the cluster removes the Job an hour after the
run ended, and `dokimi cleanup` removes the rest.

### Network paths a test needs

If a NetworkPolicy applies in `dokimi-iperf2`, it has to allow three paths:

- **from the Job to each client pod, on 5101/TCP.** That is how a test is started: the Job
  connects and sends the server's address;
- **from the client pod to the server pod, on 5001**, over the test's protocol, UDP or TCP;
- **from the Job to each test pod's exporter, on 9101/TCP.** That is how the result is read. A
  cluster that blocks it fails every test as `metrics_missing`.

Test traffic uses the pod network and IPv4, so a pod network without IPv4 cannot run a test. The
run checks the first two paths, the address family and the cluster's DNS before any test, with
[`dokimi preflight`](using-the-cli.md#preflight)'s checks. The third it cannot check in advance.

The run's own Prometheus adds three more: from the Job to the Prometheus on 9090/TCP, from the
Prometheus to each test pod's exporter on 9101/TCP, and from the Prometheus to the node-exporter
on 9137/TCP on each node's address, if the run deployed one.

## The images a run uses

A run uses four images, called components:

| Component | What it is | Default in the release | Default in a source install |
| --- | --- | --- | --- |
| `orchestrator` | the run's own Job | `ghcr.io/dokimi-io/orchestrator`, pinned by digest | none |
| `iperf2` | the test workload, client and server | `ghcr.io/dokimi-io/iperf2`, pinned by digest | none |
| `prometheus` | the run's Prometheus | `quay.io/prometheus/prometheus`, pinned by digest | the same |
| `node-exporter` | the node-exporter a run deploys when the cluster has none | `quay.io/prometheus/node-exporter`, pinned by digest | the same |

A released CLI ships with the digests of the `orchestrator` and `iperf2` images built from its
own commit. **A source install has no default for those two**, since only a release knows which
images it was built with, and `submit` refuses, before it creates anything, instead of guessing:

```console
$ dokimi submit test.yaml
dokimi: this is a development build with no published orchestrator image, so there is no
default to run. Choose one with --image orchestrator=<reference> or DOKIMI_ORCHESTRATOR_IMAGE
```

Each component is chosen the same way, highest first:

| Source | How | Scope |
| --- | --- | --- |
| Run override | `--image <component>=<reference>`, repeatable | one run |
| Installation override | `DOKIMI_<COMPONENT>_IMAGE`, for example `DOKIMI_IPERF2_IMAGE` or `DOKIMI_NODE_EXPORTER_IMAGE`, on the machine that submits | one installation |
| Release default | built into a released CLI, by digest | the released build |

`--orchestrator-image` and `DOKIMI_IMAGE` are the earlier names for the orchestrator, and still
work. Images are chosen when you submit, never in the test definition: the same test runs
unchanged in every cluster, while each site can pull from its own mirror. `submit` writes every
image into the Job, so `--dry-run` shows exactly what will run, and `dokimi image` lists every
component and where its reference came from.

With a source install, build the `orchestrator` and `iperf2` images yourself and point dokimi at
them. [Your first run](first-run.md) shows how.

## The cluster's name

Every result is labelled with the cluster it was measured on, so that history from two clusters
is never mixed up. dokimi doesn't guess that name, not from the kubeconfig context and not from
the cluster. You give it, and there is no default:

| Source | How | Scope |
| --- | --- | --- |
| Run override | `--cluster lab-fra-1`, on `submit` or `preflight` | one run |
| Installation override | `DOKIMI_CLUSTER=lab-fra-1`, on the machine that submits | one installation |

Without either, `submit` refuses before it creates anything, a dry run included. The name is a
DNS label: lowercase letters, digits and hyphens, starting and ending with a letter or digit, at
most 63 characters. Anything else is refused rather than rewritten. `submit` writes the name into
the Job, and `--dry-run` shows it.

It only names the cluster. The [cluster credentials](#cluster-credentials) choose which cluster
a run goes to, so `--cluster prod` with a staging context runs on staging, labelled `prod`. Pick
one name per cluster and keep it.
