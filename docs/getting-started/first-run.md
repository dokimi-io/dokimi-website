# Your first run

This walkthrough starts a local cluster with one control plane and three workers, builds the
two images a run needs, and submits a first run. Everything happens inside your clone of the
repository. Your default kubeconfig is never touched.

!!! info "What you will see"

    A run currently parses its definition, resolves its two nodes, claims the cluster, starts its
    own Prometheus, and runs the `iperf2` test through Robot Framework. Robot's report comes back
    to your machine. Then the run exits with code `5`, without a verdict, because measuring and
    evaluating the result are still being built. That is expected.
    [How it works](../how-it-works.md#the-phases-of-a-run) shows the phases.

## 1. Start a local cluster

The repository has its own test environment in `test-env/`. It installs pinned versions of its
tools into the repository, not system-wide:

```console
$ test-env/install-tools.sh .test-env/bin
$ export PATH="$PWD/.test-env/bin:$PATH"
$ test-env/test-env.sh up kind-kindnet
$ test-env/test-env.sh check
$ export KUBECONFIG=.test-env/kubeconfig
```

`kind-kindnet` is the fastest profile. Six others pair kind or k3d with Calico, Cilium or flannel,
for when behaviour specific to one CNI matters:

| Profile | Tool | CNI |
| --- | --- | --- |
| `kind-kindnet` | kind | kindnet |
| `kind-calico` | kind | Calico |
| `kind-cilium` | kind | Cilium |
| `kind-flannel` | kind | flannel |
| `k3d-flannel` | k3d | flannel |
| `k3d-calico` | k3d | Calico |
| `k3d-cilium` | k3d | Cilium |

`check` verifies that the cluster provides what a run needs.

## 2. Build the images

A source install has no default for the orchestrator image or the `iperf2` test image, so build
both. Your cluster cannot pull a local build from a registry, so load them straight into the
nodes, and tell dokimi to use them:

```console
$ docker build -f images/orchestrator/Dockerfile -t orchestrator:dev .
$ docker build -f images/iperf2/Dockerfile -t iperf2:dev .
$ test-env/test-env.sh load orchestrator:dev
$ test-env/test-env.sh load iperf2:dev
$ export DOKIMI_ORCHESTRATOR_IMAGE=orchestrator:dev DOKIMI_IPERF2_IMAGE=iperf2:dev
```

Without them, `submit` refuses before it creates anything, and says which image is missing.
`dokimi image` shows every image a run would use. The Prometheus and node-exporter images are
pulled from `quay.io`, so the cluster needs to reach it.

## 3. Create the namespaces and grant the run what it needs

```console
$ kubectl apply -f deploy/rbac.yaml
```

## 4. Point the example at your nodes

The example names `worker-01` and `worker-02`, which this cluster does not have. List the nodes it
does have, and point a copy of the example at two of them:

```console
$ test-env/test-env.sh nodes
dokimi-worker
dokimi-worker2
dokimi-worker3
$ sed -e 's/worker-01/dokimi-worker/' -e 's/worker-02/dokimi-worker2/' \
    examples/worker-01-to-worker-02-udp.yaml > kind-pair.yaml
```

## 5. Check the plan, then submit

```console
$ uv run dokimi submit kind-pair.yaml --dry-run --kubeconfig .test-env/kubeconfig > /dev/null
$ uv run dokimi submit kind-pair.yaml --service-account dokimi
```

The first command resolves both nodes read-only and prints the plan. It creates nothing. The
second submits the run and streams its log. In it you see the run:

- claim the cluster, start its Prometheus and a node-exporter, and check that the Prometheus
  answers. It prints the `kubectl port-forward` command that reaches the Prometheus from your
  machine;
- render the Robot suite and run it: the client and server pods are deployed on your two
  nodes, and `iperf2` runs between them for the definition's duration, plus a warm-up pass;
- say that the rest is not built yet, then remove the test pods and the node-exporter.

It exits with code `5`. Robot's report lands in `results/<run-id>/`, under the directory you
ran `submit` from: `log.html`, `report.html`, `output.xml` and the `suite.robot` that ran. Open
`log.html` to see each step. The test fails there, because every pass criterion fails and says
it was not checked.

The Prometheus is kept after the run; [Using the CLI](using-the-cli.md#cleaning-up) shows how
to remove it.

Worth trying once, to see the errors a first run can hit: point the definition at
`dokimi-control-plane` (it is tainted), `kubectl cordon` a worker, or leave off
`--service-account`. Each fails with a message that names its fix.

!!! warning "What this cluster can and cannot tell you"

    All the nodes of this cluster share one machine's network stack. Traffic between them is
    limited by the host's CPU and memory, not by a network card or a real CNI datapath. It is
    the right place to check that dokimi **orchestrates** a run correctly. It says **nothing**
    about the network performance of real hardware.

## 6. Tear it down

```console
$ test-env/test-env.sh down
```

`down` deletes the cluster, then fails if any container, volume or network labelled with it
remains.
