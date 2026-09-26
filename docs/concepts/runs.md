# Runs and exit codes

## Run ids

Every run has an id like `20260924-143012-k3f9x2`: the UTC start time to the second, then six
characters of `[0-9a-z]`.

- It is **fixed width**, so run ids sort by start time, in a log, a label or a file alike.
- It uses only lowercase letters, digits and hyphens, so it is spelled the same way in labels,
  object names and result files, with no escaping anywhere.

`attach` refuses anything that doesn't match, including a run id in capitals.

## What a run creates

A submission creates three objects, in this order:

| Object | What it is for |
| --- | --- |
| `run-<id>-owner` (ConfigMap) | the run's owner. Everything else the run creates points at it |
| `run-<id>-definition` (ConfigMap) | your test definition, mounted into the Job |
| `run-<id>` (Job) | the run itself |

They live in the test type's namespace, `dokimi-iperf2`, which every run of that type shares. It
is not created per run, which would need cluster-wide permissions on every run.

The definition travels with the run in a ConfigMap instead of being read from your disk. That is
what makes the Job self-contained, and why `attach` needs nothing local.

If the submission fails partway, for example because the Job is refused, the owner is deleted
again and takes everything already created with it.

## Staying inside its own objects

Every object carries two labels:

```yaml
app.kubernetes.io/managed-by: dokimi
dokimi.io/run-id: 20260924-143012-k3f9x2
```

Nothing without those labels is ever modified or deleted, and every lookup and delete is scoped
by a label selector, not by name alone.

The Job also carries:

- **`activeDeadlineSeconds`**, derived from the test duration plus a margin. If a run is
  orphaned, the deadline stops it on its own. Labels make cleanup possible; the deadline makes it
  unnecessary.
- **`backoffLimit: 0` and `restartPolicy: Never`.** The exit code is the verdict, so a controller
  that retried a non-zero exit would re-run the whole test on a plain failure.

## Exit codes

The exit codes are meant for automation, so they are a fixed contract:

| Code | Meaning |
| --- | --- |
| `0` | the run completed, and it passed |
| `1` | the run completed, and at least one test failed |
| `2` | at least one test errored, or something went wrong after the run |
| `3` | invalid request: a bad definition, run id or flag, found before anything was created |
| `4` | the cluster was not ready for a run (preflight) |
| `5` | internal or unexpected error |
| `130` | you pressed ++ctrl+c++ |

**The highest applicable code wins.** A run with both failures and errors exits `2`: an error
means part of the test was not measured, and an incomplete picture matters more than any one
finding.

A few more rules:

- A container that exits with a code outside this table, such as `137` after an out-of-memory
  kill, becomes `5`, and the message gives the raw code.
- A run stopped by its deadline exits `5`, with a message saying so.
- A crash in the CLI itself exits `5` with a traceback, not Python's default `1`, which would
  read as a failed test.
- Robot Framework's own exit code is never passed through. It counts failed tests, which
  collides with this table.

!!! note "Today"

    Codes `0` to `2` are verdicts, and a run cannot reach a verdict yet: it stops after planning
    and exits `5`. A node that is missing, cordoned or tainted stops it earlier, in planning,
    with `3`.
