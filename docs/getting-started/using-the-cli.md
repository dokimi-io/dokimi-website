# Using the CLI

```console
$ dokimi validate test.yaml          # parse and check; no cluster involved
$ dokimi convert test.yaml           # print the Robot suite a run executes
$ dokimi submit test.yaml --dry-run  # render the plan and the manifests
$ dokimi submit test.yaml            # create the run and stream its log
$ dokimi attach <run-id>             # resume streaming a run that is already going
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
| `--image <component>=<reference>` | choose an image for this run. Repeatable. The components are `orchestrator`, `iperf2`, `prometheus` and `node-exporter` |
| `--orchestrator-image` | the earlier name of `--image orchestrator=` |
| `--service-account` | run the Job as a specific service account |
| `--kubeconfig`, `--context` | pick cluster credentials |

### `--dry-run`

```console
$ dokimi submit test.yaml --dry-run > manifests.yaml
Planned matrix (1 test, sequential; nodes not checked)

  worker-01 -> worker-02
  ...
dry run: nothing was created.
```

Before the manifests, it prints the run id, the namespace, the images, each with where its
reference came from, and the Job's `Deadline`: how long the cluster lets the run take before it
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

The reports can be fetched for as long as the run's pod exists, so `submit --no-follow` extracts
nothing, and a later `dokimi attach <run-id>` does. A report that arrives incomplete, or fails
its checksum, is reported and nothing is extracted. None of this changes the run's exit code.

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

A run already removes its test pods, and the node-exporter it deployed, when it ends. Removing
the rest automatically is planned for the first release. Until then, deleting a run's owner
object removes everything the run created except its Prometheus, which is kept on purpose. The
cluster's garbage collector follows the owner references:

```console
$ kubectl delete configmap run-20260924-200229-ca532a-owner -n dokimi-iperf2
```

Or by label:

```console
$ kubectl delete job,configmap,daemonset -n dokimi-iperf2 \
    -l 'dokimi.io/run-id=20260924-200229-ca532a,app.kubernetes.io/component!=prometheus'
```

The `component!=prometheus` part matters. Without it, the command also deletes the Prometheus's
configuration and leaves the Prometheus itself running.

Fetch the run's reports with `dokimi attach` first if you still need them: they go with the
Job's pod.

To query a run's Prometheus from your machine, use the `port-forward` command the run printed in
phase 4, then open `http://localhost:9090`:

```console
$ kubectl port-forward -n dokimi-iperf2 service/run-20260924-200229-ca532a-prometheus 9090:9090
```

To remove a run's Prometheus, use the command the run printed next to it:

```console
$ kubectl delete deployment,service,configmap -n dokimi-iperf2 \
    -l dokimi.io/run-id=20260924-200229-ca532a,app.kubernetes.io/component=prometheus
```

Or remove every kept Prometheus at once:

```console
$ kubectl delete deployment,service,configmap -n dokimi-iperf2 \
    -l app.kubernetes.io/managed-by=dokimi,app.kubernetes.io/component=prometheus
```
