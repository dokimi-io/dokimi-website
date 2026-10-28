# Using the CLI

```console
$ dokimi validate test.yaml          # parse and check; no cluster involved
$ dokimi convert test.yaml           # print the Robot suite a run executes
$ dokimi submit test.yaml --dry-run  # render the plan and the manifests
$ dokimi submit test.yaml            # create the run and stream its log
$ dokimi preflight test.yaml         # check the cluster for that run, and run no test
$ dokimi attach <run-id>             # resume streaming a run that is already going
$ dokimi cleanup <run-id>            # remove what a run left in the cluster
$ dokimi image                       # show which images a run would use
```

## `validate`

Parses the definition and reports what it says. It contacts nothing, so it works without a
cluster or credentials. The summary shows the **parsed** values: `1G` coming back as `1G` confirms
that a decimal prefix was read as intended.

A malformed definition exits `3`. [Test definitions](../concepts/test-definitions.md) describes
what is accepted.

## `convert`

Prints a test definition in the other format, and touches nothing:

```console
$ dokimi convert test.yaml             # the Robot suite
$ dokimi convert suite.robot --to yaml # the YAML document
```

`--to robot`, the default, prints exactly the suite a run executes: the run renders it with the
same code, so what you see is what Robot Framework runs in the cluster.

## `submit`

Validates locally first, so an invalid definition never reaches the cluster. Then it creates the
run's objects and streams the Job's log until the run ends, and exits with the run's own exit
code. At the end it extracts the run's reports, as [`attach`](#attach) describes.

| Flag | |
| --- | --- |
| `--dry-run` | render and stop. Contacts nothing, unless given `--kubeconfig` or `--context` |
| `--no-follow` | submit and return, instead of streaming |
| `--run-id` | use a specific run id instead of generating one |
| `--namespace`, `-n` | use another namespace than the test type's. It must already exist: a run never creates one |
| `--cluster <name>` | the name the run's results are labelled with, instead of `DOKIMI_CLUSTER`; `preflight` takes it too. Required, one or the other: see [the cluster's name](installation.md#the-clusters-name) |
| `--image <component>=<reference>` | choose an image for this run. Repeatable. The components are `orchestrator`, `iperf2`, `prometheus` and `node-exporter` |
| `--orchestrator-image` | the earlier name of `--image orchestrator=` |
| `--service-account` | run the Job as a specific service account |
| `--retain` | when the run keeps its test pods and record for you to look at: `on-failure`, the default, `always` or `never`. See [What a run keeps](../concepts/runs.md#what-a-run-keeps) |
| `--kubeconfig`, `--context` | pick cluster credentials |

Once it has extracted the run's reports, `submit` removes the run's Job, which has nothing left
to give. A run that kept nothing goes completely, its owner and definition with it. One that
kept its evidence keeps it for [`dokimi cleanup`](#cleaning-up).

### `--dry-run`

```console
$ dokimi submit test.yaml --dry-run > manifests.yaml
Planned matrix (1 test, sequential; nodes not checked)

  worker-01 -> worker-02
  ...
dry run: nothing was created.
```

Before the manifests, it prints the run id, the namespace, the cluster's name, the images, each
with where its reference came from, and the Job's `Deadline`: how long the cluster lets the run take before it
stops it.

The manifests go to **stdout**, and everything meant for a person goes to **stderr**, so the
rendering can be saved or diffed on its own. A dry run renders with the same code a real
submission uses, so the two cannot drift apart.

A plain `--dry-run` contacts no cluster at all. Given `--kubeconfig` or `--context`, it also
reads the cluster's nodes and checks your node names against them, read-only. That is the way to
check a definition before submitting it.

### `--no-follow`

Submits and returns immediately, and prints how to pick the run up again. The exit code is `0` for
a successful submission. It says nothing about the run, which hasn't finished yet.

### Interrupting

++ctrl+c++ stops the log stream, not the run:

```text
stopped following run 20260924-200229-ca532a. The run is unaffected and continues in the
cluster; resume with: dokimi attach 20260924-200229-ca532a
```

## `preflight`

```console
$ dokimi preflight test.yaml --service-account dokimi
```

Checks that the cluster can run the definition's test, and runs no test. It submits the same
run `submit` would, and its Job stops after the checks, so it checks exactly what every run
checks first. It exits `0` if the cluster is ready, and `4` if not, naming the check:

```text
dokimi: cluster not ready (connectivity): the probe of pair-001 (worker-01 -> worker-02): no UDP to the server pod at 10.244.2.7:5001 arrived
```

| Check | What failed | Where to look |
| --- | --- | --- |
| `run_already_active` | another run holds the cluster | [One run at a time](../concepts/runs.md#one-run-at-a-time) |
| `prometheus_unreachable` | the run's Prometheus didn't answer a query within three minutes | its pod, and the Job's path to it on 9090/TCP |
| `node_count` | a node the test needs is gone, or no longer takes a test pod | `kubectl get nodes` |
| `scheduling` | a pod of the test couldn't be placed | its events: resources, taints, quotas |
| `image_pull` | a pod was placed, and couldn't get its image: three times, or at once for a reference no retry can fix | the image reference, the registry, the pull credentials |
| `connectivity` | the Job couldn't reach the client pod, or no traffic reached the server | NetworkPolicies, the CNI, an IPv4 pod network |
| `dns` | the pod network works, and `kubernetes.default.svc` didn't resolve in the client pod | the cluster's DNS |

The checks use the test's own two pods, on its two nodes and from its image. Instead of
measuring, the client sends one second of traffic at 10 Mbit/s and resolves a cluster name. The
pods are removed afterwards, so they never run next to a test.

It is not a preview: `submit --dry-run` creates nothing, while `preflight` creates real pods,
because whether they schedule and connect can only be seen by trying. It claims the cluster
while it runs, starts the run's Prometheus, which is kept like every run's, and removes
everything else it deployed, whether the checks passed or not. Whatever phase 10's snapshot
finds is in the log and in `diagnostics.json`, and doesn't change the exit code: a preflight
answers `0` or `4`. A passed check is a floor, not a guarantee: one pair, under no load, says
nothing about a larger test.

`preflight` takes the same flags as `submit`, except `--dry-run` and `--retain`.

## `attach`

```console
$ dokimi attach 20260924-200229-ca532a
```

Resumes streaming a run, and exits with the run's exit code. It needs the run id and cluster
access, and nothing else: no definition file, and no state from whoever submitted the run. So it
works the same for a person reattaching and for a CI job checking on a run it submitted
earlier.

A malformed run id is rejected before any lookup, so a typo reports "malformed run id" rather
than "no such run".

`attach`, like `submit`, extracts the run's reports. The Job writes them into its own log at the
end of the run, and the CLI takes them out of what it prints and puts them under the run id:

```text
results/20260924-200229-ca532a/
  log.html       Robot Framework's log of the run
  report.html    its report
  output.xml     every pair's results, merged
  suite.robot    the suite that ran
  pairs/         one output.xml per pair
```

The directory is the definition's `results.directory`, `./results` by default, which `attach`
reads from the definition the run was submitted with. A relative directory is relative to
wherever you run the command. `--results-directory <dir>` puts the reports somewhere else.

Like `submit`, `attach` then removes the run's Job, so **a run's reports can be fetched once,
within an hour after it ended**: the cluster removes a Job nobody fetched an hour after it
finished. `submit --no-follow` extracts nothing, and a later `dokimi attach <run-id>` does. A
report that arrives incomplete, or fails its checksum, is reported, nothing is extracted, and
the Job stays, so you can attach again. None of this changes the run's exit code.

## `image`

```console
$ dokimi image
orchestrator  ghcr.io/dokimi-io/orchestrator@sha256:ab...
  source: release-default
  digest: sha256:ab...
iperf2        ghcr.io/dokimi-io/iperf2@sha256:cd...
  source: release-default
  digest: sha256:cd...
...
```

Shows every image a run would use, `orchestrator`, `iperf2`, `prometheus` and `node-exporter`,
and where each reference came from. Each one is chosen the same way, highest first:

| Source, highest first | How | Scope |
| --- | --- | --- |
| Run override | `--image <component>=<reference>` | one run |
| Installation override | `DOKIMI_<COMPONENT>_IMAGE`, such as `DOKIMI_IPERF2_IMAGE` | one installation |
| Release default | built into a released CLI, by digest | the released build |

`--orchestrator-image` and `DOKIMI_IMAGE` are the orchestrator's earlier names, and still work.
There is no release yet, so a source install has no default for `orchestrator` and `iperf2`.
`dokimi image` lists them as having none, with how to choose one, and still exits `0`; `submit`
is what refuses.

## Cleaning up

A run cleans up after itself, and keeps what a failed run left for you to look at:
[What a run keeps](../concepts/runs.md#what-a-run-keeps) says what stays. `dokimi cleanup`
removes it:

```console
$ dokimi cleanup 20260924-200229-ca532a
run 20260924-200229-ca532a: removed 4 object(s)
  ConfigMap/run-20260924-200229-ca532a-definition
  Pod/run-20260924-200229-ca532a-pair-001-client
  Pod/run-20260924-200229-ca532a-pair-001-server
  ConfigMap/run-20260924-200229-ca532a-owner
  kept: ConfigMap/run-20260924-200229-ca532a-prometheus, Service/run-20260924-200229-ca532a-prometheus, Deployment/run-20260924-200229-ca532a-prometheus, the run's Prometheus and its history. Add --prometheus to remove it too
```

It finds everything the run created by its labels, and needs neither the run's own process nor
anything it remembered, so it also removes what a crashed run left. The test pods go first,
and it waits until they are gone, because a run's client may still be sending. Only then does
the rest go, the owner last.

| Flag | |
| --- | --- |
| `--older-than <age>` | every run that started more than this long ago, instead of one run: `90m`, `24h` |
| `--prometheus` | remove the run's Prometheus too, and the history it holds |
| `--force` | remove a run that still holds the cluster; only for one whose Job is gone |
| `--dry-run` | list what would be removed, and remove nothing |
| `--namespace`, `-n` | the test type's namespace, if not `dokimi-iperf2` |
| `--kubeconfig`, `--context` | pick cluster credentials |

Two runs are refused, because removing them now would take something from a running one:

- **a run that still holds the cluster**, since its Job may still be running it. `--force`
  removes it anyway, for a run whose Job is gone;
- **a run that left a node-exporter, while another run holds the cluster.** A later run reuses
  a node-exporter a crashed run left. Remove the crashed run once the other has ended.

With `--older-than`, such a run is skipped, and a closing line counts the runs skipped.
`cleanup` exits `0` once nothing is left that it was asked to remove, `4` when the run named by
its id was refused, and `5` when something could not be removed: a refused permission, a call
that timed out, or a test pod that didn't go. It then lists what, and the exact command to
retry, with the flags you gave.

### The Prometheus

**Every run leaves its Prometheus behind**, on purpose, so that the run's history outlives it.
It doesn't point at the run's owner, so `dokimi cleanup` removes it only with `--prometheus`.

To query a run's Prometheus from your machine, use the `port-forward` command the run printed in
phase 4, then open `http://localhost:9090`:

```console
$ kubectl port-forward -n dokimi-iperf2 service/run-20260924-200229-ca532a-prometheus 9090:9090
```

To remove a run's Prometheus, use `dokimi cleanup <run-id> --prometheus`, which also removes
whatever else of the run is left, or the command the run printed next to it:

```console
$ kubectl delete deployment,service,configmap -n dokimi-iperf2 \
    -l dokimi.io/run-id=20260924-200229-ca532a,app.kubernetes.io/component=prometheus
```

Or remove every kept Prometheus at once:

```console
$ kubectl delete deployment,service,configmap -n dokimi-iperf2 \
    -l app.kubernetes.io/managed-by=dokimi,app.kubernetes.io/component=prometheus
```
