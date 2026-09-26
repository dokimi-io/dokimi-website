---
template: home.html
title: dokimi
hide:
  - navigation
  - toc
---

!!! warning "dokimi is in active development"

    The first release, **0.1**, is coming soon. Until then, a run parses its test definition,
    resolves its two nodes against your cluster, plans the test, and stops there without a
    verdict. Everything marked <span class="dk-status dk-status--works">works today</span> on
    this site really does. Everything else is marked as planned.

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
    definition, with the unit written out. They are validated today. Evaluating them against
    measurements comes with the first release.

    <span class="dk-status dk-status--works">validated today</span>
    <span class="dk-status dk-status--planned">evaluated from 0.1</span>
    [:octicons-arrow-right-24: Pass criteria](concepts/pass-criteria.md)

-   :material-kubernetes:{ .lg .middle } **Runs in the cluster, leaves nothing installed**

    ---

    The CLI submits a one-shot Kubernetes Job and streams its log. Close your laptop and the run
    carries on; reattach later from any machine. No controller stays behind between runs.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: How it works](how-it-works.md)

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
    its own.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Runs and exit codes](concepts/runs.md)

-   :material-console-line:{ .lg .middle } **Exit codes made for CI**

    ---

    Six codes, from `0` for a passing run to `5` for an internal error. A run that stops early
    exits `5`, so it can never be mistaken for a run that passed.

    <span class="dk-status dk-status--works">works today</span>
    [:octicons-arrow-right-24: Exit codes](concepts/runs.md#exit-codes)

</div>

## What the first release adds

<span class="dk-status dk-status--planned">planned for 0.1</span>

The first release completes one path end to end. It runs one `iperf2` UDP test between two
nodes you name. A managed Prometheus observes the measurement, and dokimi evaluates throughput
and packet-loss criteria against it. Then it writes the results as CSV and JSONL and cleans up
after itself.

[See the roadmap](roadmap.md){ .md-button }
