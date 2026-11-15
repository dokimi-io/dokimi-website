# Design notes

Short notes on why dokimi behaves the way it does. Each one starts from something you will notice
when you use it, and says what it buys you and what it costs.

| Note | What you notice |
| --- | --- |
| [A run is a one-shot Job](one-shot-job.md) | Nothing to install in the cluster, and closing your terminal doesn't stop a run |
| [One run at a time](one-run-at-a-time.md) | A second run is refused while another one holds the cluster |
| [Unknown input is refused](strict-input.md) | A typo in a field or keyword stops the run before anything is created |
| [No data is never a pass](no-data-is-not-a-pass.md) | A run that couldn't check something never exits `0` |
