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
both. Your cluster cannot pull a local build from a registry, so they are loaded straight into
the nodes. One command does all of it:

```console
$ out=$(test-env/test-env.sh images) && eval "$out"
```

It builds `orchestrator:dev` and `iperf2:dev` from your checkout, loads both into every node, and
sets `DOKIMI_ORCHESTRATOR_IMAGE` and `DOKIMI_IPERF2_IMAGE` to them. It also names the cluster
`test-env` (`DOKIMI_CLUSTER`): every run needs a name for the cluster it runs on, and there is
no default. Run it again after changing the code, to rebuild what the cluster runs.

Use it as written, not as `eval "$(test-env/test-env.sh images)"`: if a build fails, that `eval`
runs an empty string and succeeds, and the next run quietly uses the previous build.

Without the images, `submit` refuses before it creates anything, and says which image is
missing. Without a cluster name, it refuses too.
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
- check the cluster with the test's own two pods: they are scheduled, pull their image, send a
  second of traffic and resolve a cluster name, and are removed again;
- render the Robot suite and run it: the client and server pods are deployed on your two
  nodes, and `iperf2` runs between them for the definition's duration, plus a warm-up pass;
- read the result directly from the pods' exporters, and check that Prometheus holds it too;
- record where every pod ran and how it ended, then say that the rest is not built yet, and
  remove the test pods and the node-exporter.

It exits with code `5`. Robot's report lands in `results/<run-id>/`, under the directory you
ran `submit` from: `log.html`, `report.html`, `output.xml` and the `suite.robot` that ran, plus
`measurement.json` with what was measured and `diagnostics.json` with where everything ran.
Open `log.html` to see each step. The test fails there, because every pass criterion fails and
says it was not checked.

To check the cluster without running a test, `uv run dokimi preflight kind-pair.yaml
--service-account dokimi` runs only the checks, and exits `0` if the cluster is ready.

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
