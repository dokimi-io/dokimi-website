# Your first run

This walkthrough starts a local cluster with one control plane and three workers, builds the
orchestrator image, and submits a first run. Everything happens inside your clone of the
repository. Your default kubeconfig is never touched.

!!! info "What you will see"

    A run currently parses its definition, resolves its two nodes, plans the test and claims the
    cluster, then stops with exit code `5`, because the rest of the phases are still being built. That is
    expected. [How it works](../how-it-works.md#the-phases-of-a-run) shows the phases.

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

## 2. Build the orchestrator image

Your cluster cannot pull a local build from a registry, so load it straight into the nodes:

```console
$ docker build -f images/orchestrator/Dockerfile -t orchestrator:dev .
$ test-env/test-env.sh load orchestrator:dev
$ export DOKIMI_IMAGE=orchestrator:dev
```

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
second submits the run and streams its log until the run stops, right after it claims the
cluster.

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
