---
template: home.html
title: dokimi
hide:
  - navigation
  - toc
---

!!! warning "dokimi is in active development"

    The first release, **0.1**, is coming soon. Until then, a run parses its test definition,
    resolves its two nodes against your cluster, claims the cluster for itself, starts its own
    Prometheus, checks that the cluster can run the test, runs the `iperf2` test through Robot
    Framework, and reads the measurement. Robot's report comes back to your machine. What it does
    not do yet is check the measurement against your pass criteria, so a run ends without a
    verdict. Everything marked
    <span class="dk-status dk-status--works">works today</span> on this site really does.
    Everything else is marked as planned.

## What dokimi does today

<div class="grid cards" markdown>

-   :material-file-document-edit-outline:{ .lg .middle } **A test definition in YAML or Robot**

    ---

    Write a test as a YAML document or as a Robot Framework suite. Both formats describe the same
    things, and both are strict: anything dokimi does not understand is refused, with the line
    and the reason.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Test definitions](concepts/test-definitions.md)

-   :material-check-decagram-outline:{ .lg .middle } **Pass criteria you can read**

    ---

    `Throughput Should Be At Least 950 megabits per second`. Criteria are part of the test
    definition, with the unit written out. Every run evaluates them against what each pair
    measured and lists each one with its value. A pair that couldn't be measured is an error,
    never a pass.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Pass criteria](concepts/pass-criteria.md)

-   :material-kubernetes:{ .lg .middle } **Runs in the cluster, as a one-shot Job**

    ---

    The CLI submits a one-shot Kubernetes Job and streams its log. Close your laptop and the run
    carries on; reattach later from any machine. No controller stays behind between runs. What
    stays is each run's own Prometheus, kept so the run's history outlives it, until you remove it.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: How it works](how-it-works.md)

-   :material-robot-outline:{ .lg .middle } **Robot Framework runs the test**

    ---

    Whichever format you wrote, the run renders it to a Robot suite and runs it. The suite
    deploys the client and server pods, waits until both are ready, and runs `iperf2`. Robot's
    `log.html` and `report.html` come back to your machine, next to the exact suite that ran.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: How it works](how-it-works.md#where-robot-framework-fits)

-   :material-eye-check-outline:{ .lg .middle } **Look before it creates anything**

    ---

    `--dry-run` renders every manifest a run would create and creates none of them. Given a
    kubeconfig, it also checks your node names, read-only. A missing, cordoned or tainted node is
    reported with the fix.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Using the CLI](getting-started/using-the-cli.md)

-   :material-shield-check-outline:{ .lg .middle } **Touches only what it created**

    ---

    Every object a run creates carries the run's labels, and every lookup and delete is scoped
    by them. Anything without those labels is never modified. A deadline stops an orphaned run on
    its own. And a cluster runs one run at a time: a second run is refused while the first holds
    it.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Runs and exit codes](concepts/runs.md)

-   :material-console-line:{ .lg .middle } **Exit codes made for CI**

    ---

    Six codes, from `0` for a passing run to `5` for an internal error. A run that ends without
    a verdict exits `5`, so it can never be mistaken for a run that passed.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Exit codes](concepts/runs.md#exit-codes)

</div>

## What the first release adds

<span class="dk-status dk-status--planned">planned for 0.1</span>

The first release completes one path end to end. It already runs one `iperf2` UDP test between
two nodes you name, next to a managed Prometheus, checks the cluster first, reads the measurement,
evaluates the pass criteria against it and records where everything ran. What it adds is the rest
of that path: dokimi writes the results as CSV and JSONL, and cleans up after itself. The run's
exit code is then its verdict.

[See the roadmap](roadmap.md){ .md-button }
