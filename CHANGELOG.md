# Weekly catalog changelog

Changes to Awesome Local AI, not upstream software releases. Weeks start on
Monday in UTC. Contributors update the current week's section with their
catalog PR; there is no automatic publishing or merging of these notes.

## Week of 2026-10-12

### Added

- [YYLO](https://github.com/yylo-dev/yylo), a terminal orchestrator for coding agents with typed tasks, skills installs, and receipt-backed merge gates, with Pi as a supported subagent.
- [Orkas](https://github.com/Orkas-AI/Orkas), a local-first desktop client for coordinating specialist agents with supported providers and compatible local model endpoints.
- [DGX Spark Networking](https://github.com/christopherowen/dgx-spark-networking), RoCE collectives, NCCL profiles, and fabric diagnostics for multi-node inference.
- [Contemplative Agent](https://github.com/shimo4228/contemplative-agent), an autonomous agent on a local Ollama model with a human approval gate for changes to its prompts.
- [Sqwakie](https://github.com/alexcarney460-hue/walkie), pooled llama.cpp RPC runs of one open-weight model across opted-in team machines, with an OpenAI-compatible API on localhost.

### Updated

- YYLO's entry distinguishes unreleased source from stable packages, Advanced from Simple initialization, and default skill downloads.
- Task-based browsing now distinguishes autonomous agents from coding agents.
- Routine health refreshes can merge after scoped-data and CI checks; flagged snapshots and project submissions still need human review.
- Health automation waits for its dispatched CI run before merging instead of relying on bot-triggered follow-up events.

## Week of 2026-10-05

### Added

- The initial [24-project catalog](https://github.com/SeraphimSerapis/awesome-local-ai/commit/ac787fd0911e4f2503d92d703acd9d724bea5b9a), with task-based discovery and separate cloud integrations.
- [TandemLLM](https://github.com/0xBakeer/TandemLLM), a Spark-focused inference engine.
- [Spark Tools](https://github.com/knapcio/spark-tools), inference simulation and validation tools.
- [Spark Bench](https://github.com/Weschera/spark-bench), model and serving-recipe evaluation.
- [Inference Atlas](https://github.com/0xBakeer/inference-atlas), community inference measurements, local benchmarking, and terminal install recipes.
- [DGX Spark Fan Control](https://github.com/christopherowen/dgx-spark-fan-control), minimum fan-speed floors and performance curves.
- [DGX Spark Memory Saver](https://github.com/christopherowen/dgx-spark-memory-saver), a version-qualified UVM allocation patch.
- Weekly repository observations with check dates, last-push dates, and archived/disabled flags.

### Updated

- README entries now show when documentation was reviewed and when repository metadata was checked.
- Contribution instructions cover weekly notes and separate automated observations from documentation review.
