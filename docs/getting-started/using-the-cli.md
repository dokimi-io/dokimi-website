# Using the CLI

```console
$ dokimi validate test.yaml          # parse and check; no cluster involved
$ dokimi submit test.yaml --dry-run  # render the plan and the manifests
$ dokimi submit test.yaml            # create the run and stream its log
$ dokimi attach <run-id>             # resume streaming a run that is already going
$ dokimi image                       # show which orchestrator image a run would use
```

## `validate`

Parses the definition and reports what it says. It contacts nothing, so it works without a
cluster or credentials. The summary shows the **parsed** values: `1G` coming back as `1G` confirms
that a decimal prefix was read as intended.

A malformed definition exits `3`. [Test definitions](../concepts/test-definitions.md) describes
what is accepted.

## `submit`

Validates locally first, so an invalid definition never reaches the cluster. Then it creates the
run's objects and streams the Job's log until the run ends, and exits with the run's own exit
code.

| Flag | |
| --- | --- |
| `--dry-run` | render and stop. Contacts nothing, unless given `--kubeconfig` or `--context` |
| `--no-follow` | submit and return, instead of streaming |
| `--run-id` | use a specific run id instead of generating one |
| `--namespace`, `-n` | use another namespace than the test type's |
| `--orchestrator-image` | use another image for the Job |
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

## `image`

Shows which orchestrator image a run would use, and where that reference came from:

| Source, highest first | How | Scope |
| --- | --- | --- |
| Run override | `--orchestrator-image <reference>` | one run |
| Installation override | `DOKIMI_IMAGE` | one installation |
| Release default | built into a released CLI, by digest | the released build |

There is no release yet, so a source install has no release default.

## Cleaning up

Automatic cleanup is planned for the first release. Until then, deleting a run's owner object
removes everything the run created. The cluster's garbage collector follows the owner
references:

```console
$ kubectl delete configmap run-20260924-200229-ca532a-owner -n dokimi-iperf2
```

Or by label:

```console
$ kubectl delete job,configmap -n dokimi-iperf2 -l dokimi.io/run-id=20260924-200229-ca532a
```
