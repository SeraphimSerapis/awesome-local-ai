# Awesome Local AI

Tools for running, using, evaluating, and maintaining AI on your own hardware.
Browse by task, or ask your agent to find tools that fit your machine and workflow.

Local includes personal computers and self-hosted clusters. A project can support
cloud providers too, but its core listing must have a documented local use case.
Optional cloud integrations live in a separate section.

## Start here

- [Find tools by task](#find-tools-by-task)
- [Browse by category](#browse-by-category)
- [Weekly catalog changelog](CHANGELOG.md)
- [Understand review and activity dates](docs/maintenance.md)
- [Submit or update a project](CONTRIBUTING.md)
- [Let an agent help you choose](AGENTS.md)
- [Read the catalog format](docs/catalog-format.md)

Try asking your agent:

> Read this repository and help me choose a local coding setup for my Mac.
> Ask about my hardware and requirements first. Compare relevant tools, cite
> their documentation, and explain what is documented versus untested.
> Recommend a setup without installing anything.

Each entry links to structured metadata and evidence. Compatibility is based on
upstream documentation, not a runtime certification. Hardware tags are a starting
point; read each project's requirements for model, memory, OS, and driver limits.
Local-capable does not automatically mean offline, private, or safe to run.

Documentation-review dates reflect a human reading the cited sources. Repository
checks report GitHub metadata separately: reachability, last observed push, and
archived/disabled flags. Recent pushes do not prove maintenance or quality, and
inactivity does not prove abandonment. See [maintenance](docs/maintenance.md).

<!-- catalog:start -->

## Find tools by task

| I want to... | Start here |
| --- | --- |
| Run a model on my hardware | [boots / ai-bootstrap](https://github.com/kindlingai/boots), [DwarfStar / ds4](https://github.com/antirez/ds4), [mentat](https://github.com/kindlingai/mentat), [mlx-serve](https://github.com/ddalcu/mlx-serve), [oMLX](https://github.com/jundot/omlx), [spark-vllm-docker](https://github.com/eugr/spark-vllm-docker), [SparkPilot](https://github.com/ashhart/SparkPilot), [sparkrun](https://github.com/spark-arena/sparkrun), [Splash](https://github.com/incoai/splash), [Sqwakie](https://github.com/alexcarney460-hue/walkie), [Strata](https://github.com/Niko1221/Strata), [TandemLLM](https://github.com/0xBakeer/TandemLLM), [TensorFold](https://github.com/ashhart/TensorFold) |
| Connect a coding agent to a local model | [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness), [DwarfStar / ds4](https://github.com/antirez/ds4), [mlx-serve](https://github.com/ddalcu/mlx-serve), [Oh My Pi](https://github.com/can1357/oh-my-pi), [oMLX](https://github.com/jundot/omlx), [Pi](https://github.com/earendil-works/pi), [Splash](https://github.com/incoai/splash), [Strata](https://github.com/Niko1221/Strata), [TandemLLM](https://github.com/0xBakeer/TandemLLM), [TensorFold](https://github.com/ashhart/TensorFold), [YYLO](https://github.com/yylo-dev/yylo) |
| Run autonomous agents with local models | [Contemplative Agent](https://github.com/shimo4228/contemplative-agent) |
| Test tool-calling quality | [Inference Atlas](https://github.com/0xBakeer/inference-atlas), [Spark Bench](https://github.com/Weschera/spark-bench), [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) |
| Compare inference speed | [Inference Atlas](https://github.com/0xBakeer/inference-atlas), [llama-benchy](https://github.com/eugr/llama-benchy), [RigMark](https://github.com/alexellis/rigmark), [Spark Bench](https://github.com/Weschera/spark-bench), [Spark Tools](https://github.com/knapcio/spark-tools), [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) |
| Deploy or manage a cluster | [DGX Spark Networking](https://github.com/christopherowen/dgx-spark-networking), [kindling-spark-os](https://github.com/kindlingai/kindling-spark-os), [MCDMA](https://github.com/ashhart/MCDMA), [mentat](https://github.com/kindlingai/mentat), [spark-vllm-docker](https://github.com/eugr/spark-vllm-docker), [sparkrun](https://github.com/spark-arena/sparkrun), [Sqwakie](https://github.com/alexcarney460-hue/walkie) |
| Set up local AI | [boots / ai-bootstrap](https://github.com/kindlingai/boots), [kindling-spark-os](https://github.com/kindlingai/kindling-spark-os), [sparkrun](https://github.com/spark-arena/sparkrun) |
| Monitor my setup | [SparkDash](https://github.com/MiaAI-Lab/sparkDash) |
| Troubleshoot my setup | [DGX Spark Networking](https://github.com/christopherowen/dgx-spark-networking), [Spark Doctor](https://github.com/joeynyc/spark-doctor) |
| Tune thermals and memory | [DGX Spark Fan Control](https://github.com/christopherowen/dgx-spark-fan-control), [DGX Spark Memory Saver](https://github.com/christopherowen/dgx-spark-memory-saver) |
| Validate or simulate inference configurations | [Spark Tools](https://github.com/knapcio/spark-tools) |
| Chat with a local model | [DwarfStar / ds4](https://github.com/antirez/ds4), [mlx-serve](https://github.com/ddalcu/mlx-serve), [oMLX](https://github.com/jundot/omlx), [Orkas](https://github.com/Orkas-AI/Orkas), [SparkPilot](https://github.com/ashhart/SparkPilot), [Splash](https://github.com/incoai/splash), [Strata](https://github.com/Niko1221/Strata) |
| Add skills, extensions, or MCP tools | [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness), [gcloud MCP servers](https://github.com/googleapis/gcloud-mcp) (cloud), [Google Agent Skills](https://github.com/google/skills) (cloud), [Matt Pocock's skills](https://github.com/mattpocock/skills), [Oh My Pi](https://github.com/can1357/oh-my-pi), [Orkas](https://github.com/Orkas-AI/Orkas), [Pi](https://github.com/earendil-works/pi), [YYLO](https://github.com/yylo-dev/yylo) |
| Use optional cloud integrations | [gcloud MCP servers](https://github.com/googleapis/gcloud-mcp) (cloud), [Google Agent Skills](https://github.com/google/skills) (cloud) |

## Browse by category

- [Inference and serving](#inference)
- [Deployment and bootstrapping](#deployment)
- [Clustering and interconnects](#clustering)
- [Systems](#systems)
- [Agent harnesses](#harnesses)
- [Evaluation and benchmarking](#evaluation)
- [Monitoring and diagnostics](#monitoring)
- [Applications and model management](#applications)
- [Agent skills and extensions](#skills)
- [MCP servers](#mcp)
- [Cloud integrations](#cloud-integrations)

<a id="inference"></a>

### Inference and serving

- [DwarfStar / ds4](https://github.com/antirez/ds4): Run a focused native inference engine and coding agent for selected large models on consumer hardware.
  - Local workload. Platforms: macOS, Linux. Hardware: Apple Silicon, NVIDIA GPU, AMD GPU, DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/antirez/ds4/fc80bd695da76ee14bcb86820bf900a5cdfda806/LICENSE). [Metadata and evidence](data/projects/dwarfstar.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-08. Archived: no. Disabled: no.
  - Note: Beta-quality software with fast-changing model support; uses project-produced GGUF files, not arbitrary GGUF models.
  - Note: Metal primarily targets Macs with 96 GB or more; smaller machines and larger models may need SSD streaming.

- [mlx-serve](https://github.com/ddalcu/mlx-serve): Serve MLX and GGUF models on Apple Silicon through a native server with a companion model-management and chat app.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [MIT](https://raw.githubusercontent.com/ddalcu/mlx-serve/1b00c65a3cdf4a60a6e64709e150b75d4ecd8b02/LICENSE). [Metadata and evidence](data/projects/mlx-serve.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Requires macOS 26.2 or newer; confirm the selected model and modality against upstream documentation.

- [oMLX](https://github.com/jundot/omlx): Serve local MLX models with continuous batching, tiered memory/SSD caching, and menu-bar management.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/jundot/omlx/013bc3f3a48fa9a4b7dffbfeb6cdc7c1face1c5d/LICENSE). [Metadata and evidence](data/projects/omlx.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Requires Apple Silicon and macOS 15 or newer; source installs require Python 3.11-3.13.
  - Note: Some model families require custom Metal kernels; use the packaged app or follow the full Xcode build requirements.

- [Splash](https://github.com/incoai/splash): Serve supported models on Apple Silicon with speculative decoding, Metal kernels, and coding-agent integrations.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/incoai/splash/8a2b42069923d483151372b615f6182c72c2b6cd/LICENSE). [Metadata and evidence](data/projects/splash.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-14. Archived: no. Disabled: no.
  - Note: Requires Apple M3 or newer and macOS 26.4 or newer; memory requirements depend on model and quantization.
  - Note: Model and draft downloads need network access on first use.

- [Strata](https://github.com/Niko1221/Strata): Run supported Qwen models on Windows or Linux PCs with NVIDIA or AMD GPUs, with a local UI and model APIs.
  - Local workload. Platforms: Windows, Linux. Hardware: NVIDIA GPU, AMD GPU.
  - License: [MIT](https://raw.githubusercontent.com/Niko1221/Strata/61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406/LICENSE). [Metadata and evidence](data/projects/strata.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: The standard setup requires a supported GPU with at least 12 GB VRAM, at least 32 GB RAM, and about 80 GB free disk.
  - Note: Model support is specific; experimental hardware paths and AMD vision support have additional limits.

- [TandemLLM](https://github.com/0xBakeer/TandemLLM): Serve Qwen3.8-27B on a single DGX Spark with speculative decoding, conversation caches, and a local dashboard.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [AGPL-3.0-only](https://raw.githubusercontent.com/0xBakeer/TandemLLM/c11aecaa7ba767642409ff51d90d48c79c572d3a/LICENSE). [Metadata and evidence](data/projects/tandemllm.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Currently qualified for one DGX Spark and Qwen3.8-27B; other CUDA GPUs are best effort.
  - Note: Requires the documented Python 3.11, PyTorch/CUDA, and Triton stack; run one engine per board.
  - Note: Code is AGPL-3.0-only with a separate commercial option; documentation and model artifacts have separate licenses.

- [TensorFold](https://github.com/ashhart/TensorFold): Serve supported language models with a native inference engine using Metal or CUDA kernels.
  - Local workload. Platforms: macOS, Linux. Hardware: Apple Silicon, NVIDIA GPU, DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/ashhart/TensorFold/bec00ae6961a43a9ab73c4fa9338c167b3f82851/LICENSE). [Metadata and evidence](data/projects/tensorfold.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-16. Archived: no. Disabled: no.
  - Note: Model, checkpoint format, and hardware qualification are specific to each release; consult the qualification table.
  - Note: Experimental Living Weights modifies checkpoint files; teach a copy and keep the original.

<a id="deployment"></a>

### Deployment and bootstrapping

- [boots / ai-bootstrap](https://github.com/kindlingai/boots): Use a setup-focused agent to discover hardware and bootstrap local model servers with permission-based host access.
  - Local client or agent. Platforms: Linux, macOS, Windows. Hardware: CPU, Apple Silicon, NVIDIA GPU, AMD GPU, DGX Spark / GB10.
  - License: [Unclear; check upstream](https://github.com/kindlingai/boots). [Metadata and evidence](data/projects/boots.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-08. Archived: no. Disabled: no.
  - Note: Windows setup uses WSL; model downloads and provisioning can need network access.
  - Note: Can use SSH and sudo with permission; inspect the setup plan before approving host changes.
  - Note: No explicit upstream license was found in the root or deno.json; confirm licensing before redistribution.

- [spark-vllm-docker](https://github.com/eugr/spark-vllm-docker): Run vLLM in Docker on one or more DGX Spark systems with networking and distributed-inference setup scripts.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/eugr/spark-vllm-docker/a4c172976a5f9f8669b356a0891bf972cae14fd4/LICENSE). [Metadata and evidence](data/projects/spark-vllm-docker.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-16. Archived: no. Disabled: no.
  - Note: Targets DGX Spark; multi-node operation depends on compatible networking and model configuration.

- [sparkrun](https://github.com/spark-arena/sparkrun): Launch, manage, and stop recipe-based inference workloads on single-node or multi-node DGX Spark setups.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/spark-arena/sparkrun/b444da874923fd27228dcb98ab844c328a91752d/LICENSE). [Metadata and evidence](data/projects/sparkrun.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Setup can change SSH, sudoers, and host services; review the recipe and requested permissions.
  - Note: Anonymous usage telemetry is on by default; SPARKRUN\_NO\_TELEMETRY=1 disables it for one process.
  - Note: The bundled SparkRoute integration has separate AGPL licensing; check the selected channel's defaults.

<a id="clustering"></a>

### Clustering and interconnects

- [DGX Spark Networking](https://github.com/christopherowen/dgx-spark-networking): RoCE collectives, patched NCCL profiles, topology discovery, and fabric probes for multi-node DGX Spark inference.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/christopherowen/dgx-spark-networking/f7fcc1e2937f19b6f4f3539b3fe0e43a51201110/LICENSE). [Metadata and evidence](data/projects/dgx-spark-networking.json).
  - Documentation reviewed: 2026-10-18. Repository: not checked yet.
  - Note: Documented node stack includes DGX Spark OS 26.09+, kernel 7.0.0-1019-nvidia with kho=off, driver 580.178.04, ConnectX-7 firmware 28.45.4028, and rdma-core 50.
  - Note: Needs MTU 9000, static IPv4 per cable stripe, GID index 3, unlimited locked memory, libibverbs headers, and a C compiler. Container recipes require NVIDIA runtime, host networking, RDMA devices, and IPC\_LOCK.
  - Note: One-shot runtime needs torch, cuda-python, and TileLang 0.1.15+; every NCCL profile requires a rebuilt library with the packaged send-path fence patch to avoid hangs.
  - Note: No adapter ships for upstream vLLM or SGLang. Switched 2-16-node profiles are configuration paths not qualified on the author's fleet; GPU-initiated transport is not implemented.
  - Note: Does not configure hosts or supervise serving. Probe and benchmark each fabric before use; collective failures require restarting the rank group.

- [MCDMA](https://github.com/ashhart/MCDMA): Configure and verify RDMA links between supported Mac and Linux hosts for distributed local inference.
  - Local workload. Platforms: macOS, Linux. Hardware: Apple Silicon, DGX Spark / GB10, AMD GPU.
  - License: [Apache-2.0](https://raw.githubusercontent.com/ashhart/MCDMA/3f4f4be02dd9289ccd72b496d723660b5f181ffb/LICENSE). [Metadata and evidence](data/projects/mcdma.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-15. Archived: no. Disabled: no.
  - Note: Requires qualified hardware, cables, adapters, and drivers; hardware tags do not imply every cross-platform link is validated.
  - Note: The documented Strix Halo/Mac workflow still needs physical validation.

- [mentat](https://github.com/kindlingai/mentat): Manage small inference clusters and route model endpoints with a lightweight replacement for vLLM's Ray executor dependencies.
  - Local workload. Platforms: Linux. Hardware: Not recorded.
  - License: [MIT OR Apache-2.0](https://raw.githubusercontent.com/kindlingai/mentat/e9d2ce11395d1adf0bbc4b640f5bcc356e82e41b/rust/Cargo.toml). [Metadata and evidence](data/projects/mentat.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-08. Archived: no. Disabled: no.
  - Note: Implements the Ray functionality used by vLLM, not the full Ray API.
  - Note: The Rust workspace declares MIT OR Apache-2.0; no top-level license text was found, so confirm terms for other components.

- [Sqwakie](https://github.com/alexcarney460-hue/walkie): Split one open-weight model across opted-in team machines with llama.cpp RPC and serve an OpenAI-compatible API on localhost; also links Claude Code and Codex agents.
  - Local workload. Platforms: macOS, Linux. Hardware: Not recorded.
  - License: [FSL-1.1-ALv2](https://raw.githubusercontent.com/alexcarney460-hue/walkie/89229f3352fba9402eef611ff6cc118c8a801485/LICENSE). [Metadata and evidence](data/projects/sqwakie.json).
  - Documentation reviewed: 2026-10-17. Repository: not checked yet.
  - Note: v0.2 pre-release. Sharing is off by default; a person on each machine must turn pooled model runs on.
  - Note: The README does not document hardware requirements or which llama.cpp backends pooled runs use.
  - Note: Needs a Sqwakie team: the Free plan covers up to 2 people and 4 machines; larger teams need a paid per-person plan.
  - Note: Licensing calls home for one-time activation and, on paid plans, a daily renewal check. When no direct path exists, an encrypted relay sees connection metadata such as IP addresses.
  - Note: Source-available license (FSL-1.1-ALv2), not OSI open source; each version becomes Apache-2.0 two years after release.

<a id="systems"></a>

### Systems

- [DGX Spark Fan Control](https://github.com/christopherowen/dgx-spark-fan-control): Set minimum fan-speed floors or a temperature-based performance curve on qualified DGX Spark systems.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [GPL-2.0-only](https://raw.githubusercontent.com/christopherowen/dgx-spark-fan-control/deb2ea155f6698b769ff4977dea2119e3b32f460/LICENSE). [Metadata and evidence](data/projects/dgx-spark-fan-control.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-09-08. Archived: no. Disabled: no.
  - Note: Experimental; validated against specific NVIDIA kernel and EC firmware versions. Other GB10 variants are unverified.
  - Note: Needs root access and a locally built/signed kernel module; Secure Boot requires certificate enrollment.
  - Note: Sets minimums, not exact fan speeds. Hard crashes can prevent restoring automatic control, and manual floors have no expiry.

- [DGX Spark Memory Saver](https://github.com/christopherowen/dgx-spark-memory-saver): Reduce GPU page-table memory overhead by patching NVIDIA UVM allocation on qualified 64 KiB DGX Spark kernels.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/christopherowen/dgx-spark-memory-saver/6f97319e7c00e5422b0afe4cabbd348211bfcb34/LICENSE). [Metadata and evidence](data/projects/dgx-spark-memory-saver.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-16. Archived: no. Disabled: no.
  - Note: Changes a kernel module and initramfs; requires root access, matching headers, signing, and an explicit activation/rollback plan.
  - Note: R580 has production-trial evidence; R610 has additional conditions. Check the exact driver/kernel compatibility manifest.
  - Note: Distribution is source-only; build and sign locally. Remove overrides before NVIDIA upgrades and recheck compatibility.
  - Note: Original additions are MIT-licensed; retained NVIDIA source and patches carry their own notices and terms.

- [kindling-spark-os](https://github.com/kindlingai/kindling-spark-os): Boot a minimal read-only OS image beside DGX OS on NVIDIA GB10 systems for local model-serving infrastructure.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [AGPL-3.0-only](https://raw.githubusercontent.com/kindlingai/kindling-spark-os/099e62f29acedbdc9623d858c468a89ac2b126df/LICENSE). [Metadata and evidence](data/projects/kindling-spark-os.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-04. Archived: no. Disabled: no.
  - Note: Beta software that changes the boot setup; read recovery instructions and back up the host first.
  - Note: Built images can contain proprietary NVIDIA packages that upstream says must not be redistributed; check the licensing section.

<a id="harnesses"></a>

### Agent harnesses

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness): Run a plugin-based agent harness with a web UI and configurable model-provider adapters.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/d743267388641bc76f17c45ce8b4c231aed1d32c/LICENSE). [Metadata and evidence](data/projects/deepseek-harness.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Developer preview with compatibility-breaking changes; review the upstream safety notice.
  - Note: Self-hosted endpoints may need explicit request-compatibility settings; protocol support is not full feature certification.

- [Oh My Pi](https://github.com/can1357/oh-my-pi): Use a coding-agent harness with IDE-oriented tools and configurable local model providers.
  - Local client or agent. Platforms: Linux, macOS, Windows. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/can1357/oh-my-pi/5063baf59ec68ad3f2bff060a3ba44b0547eee15/LICENSE). [Metadata and evidence](data/projects/oh-my-pi.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: A local provider still needs a separately running model server and model-specific capability checks.

- [Pi](https://github.com/earendil-works/pi): Use an extensible coding-agent harness with local model connections, skills, extensions, and automation interfaces.
  - Local client or agent. Platforms: Linux, macOS, Windows. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/earendil-works/pi/4ac0bd8c7b96d72cb6a73226edc7c9ecaae1d14e/LICENSE). [Metadata and evidence](data/projects/pi.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Local inference needs a separate model server; endpoint-specific behavior may need configuration.

- [YYLO](https://github.com/yylo-dev/yylo): Orchestrate coding agents from the terminal with typed tasks, skills installs, and receipt-backed merge gates; Pi is a supported subagent.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/yylo-dev/yylo/e958c03fa2d6a3135d9583c2f0f58998f319109d/LICENSE). [Metadata and evidence](data/projects/yylo.json).
  - Documentation reviewed: 2026-10-18. Repository: not checked yet.
  - Note: Requires Node.js 20.10 or newer and Git; upstream does not document per-operating-system support.
  - Note: The orchestrator itself contacts no model provider: subagents such as Pi are installed and configured separately, and provider credentials, model availability, and any local model servers remain external.
  - Note: Evidence describes unreleased CLI 0.2.12; features and required companion versions may differ from the published stable package.
  - Note: Advanced-mode bootstrap can create an initial commit and protected integration-owner worktree in an empty Git repository. Simple mode uses a shared checkout; fresh Simple initialization downloads agent skills by default unless --no-skills is set. Review skills before loading them.

<a id="evaluation"></a>

### Evaluation and benchmarking

- [Inference Atlas](https://github.com/0xBakeer/inference-atlas): Browse community inference measurements and benchmark local model servers with configuration fingerprints, coverage maps, and install recipes.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/0xBakeer/inference-atlas/b93f6281f150788d53c05600725b63f8febddd1e/LICENSE). [Metadata and evidence](data/projects/inference-atlas.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-14. Archived: no. Disabled: no.
  - Note: Early-stage project; coverage depends on contributed measurements, not universal engine, model, or hardware compatibility.
  - Note: Benchmarking requires Python 3.11 or newer, a configured inference server, suitable model hardware, and a resolvable GitHub login for provenance.
  - Note: The terminal UI requires Node.js 20 or newer, git, and pnpm; it browses data and generates recipes rather than serving models.
  - Note: The terminal UI syncs published data on launch and periodically by default; cached data works offline, or --repo reads a local checkout with compiled data.
  - Note: Benchmark telemetry samples local hardware by default and can be disabled; submitted results include contributor provenance and become public.
  - Note: Code-execution grading runs generated code in a subprocess, not a security sandbox; avoid untrusted models on sensitive machines.
  - Note: Code is MIT licensed; registry and measurement data use CC-BY-4.0, while third-party datasets and model weights retain their own terms.

- [llama-benchy](https://github.com/eugr/llama-benchy): Measure prompt-processing and token-generation speed at different context depths through a model server's API.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/eugr/llama-benchy/e9be344578cec17745066b220798b80a0d2686d3/LICENSE). [Metadata and evidence](data/projects/llama-benchy.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-07-10. Archived: no. Disabled: no.
  - Note: Measures serving performance, not tool-calling correctness or complete coding-agent quality.

- [RigMark](https://github.com/alexellis/rigmark): Benchmark model-serving behavior with prose, code, structured output, cache tests, and concurrent requests.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/alexellis/rigmark/52c29c3fc1d741b9aef8895b23372aafa5dc6161/LICENSE). [Metadata and evidence](data/projects/rigmark.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-14. Archived: no. Disabled: no.
  - Note: A serving benchmark, not a complete multi-turn coding-agent evaluation.
  - Note: Comparisons need disclosed model and serving settings; different stacks do not isolate topology effects.

- [Spark Bench](https://github.com/Weschera/spark-bench): Evaluate model-serving recipes with tool-use, multi-turn, coding, and throughput workloads aimed at DGX Spark operators.
  - Local client or agent. Platforms: Not recorded. Hardware: DGX Spark / GB10.
  - License: [Unclear; check upstream](https://raw.githubusercontent.com/Weschera/spark-bench/0a2e2afe96112020919e74d371f73d9a57640984/README.md). [Metadata and evidence](data/projects/spark-bench.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-13. Archived: no. Disabled: no.
  - Note: Scores describe model and deployment combinations; different methodology versions are not directly comparable.
  - Note: Includes executable-code grading; review execution isolation and resource limits before running.
  - Note: The README declares MIT, but no license text was found; confirm licensing before redistribution.

- [Spark Tools](https://github.com/knapcio/spark-tools): Check and simulate inference configurations, compiler resources, schedulers, and MoE layouts for DGX Spark.
  - Local client or agent. Platforms: macOS, Linux. Hardware: CPU, DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/knapcio/spark-tools/6caf4757397a887983802b52f905de371465c29b/LICENSE). [Metadata and evidence](data/projects/spark-tools.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-11. Archived: no. Disabled: no.
  - Note: Most checks need no GPU; optional device validation needs a compatible GPU and toolchain.
  - Note: Simulations and static checks do not establish real throughput, GPU correctness, or model quality; timing predictions need calibration.

- [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench): Evaluate tool-calling quality and benchmark self-hosted model endpoints with deterministic scenarios and conversation traces.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/SeraphimSerapis/tool-eval-bench/b60e2f00f6c44352a3680356e7c7948f777c5280/LICENSE). [Metadata and evidence](data/projects/tool-eval-bench.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Tests assistant conversations with mock tools, not full agent systems or multi-agent handoffs.
  - Note: Difficulty tiers are author estimates; localization coverage is German-focused.

<a id="monitoring"></a>

### Monitoring and diagnostics

- [Spark Doctor](https://github.com/joeynyc/spark-doctor): Collect DGX Spark diagnostics and explain likely system, runtime, network, and recipe problems from local evidence.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/joeynyc/spark-doctor/e50a14faf5fed4a9f202663451db92da34979298/LICENSE). [Metadata and evidence](data/projects/spark-doctor.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-04. Archived: no. Disabled: no.
  - Note: Read-only diagnostics, not automatic repairs; requires Python 3.11 or newer.
  - Note: Review and anonymize diagnostic reports before sharing them.

- [SparkDash](https://github.com/MiaAI-Lab/sparkDash): Monitor GPU, memory, network, and local model metrics across DGX Spark and other hosts in a web dashboard.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10, NVIDIA GPU.
  - License: [Apache-2.0](https://raw.githubusercontent.com/MiaAI-Lab/sparkDash/1403c1ce79db030645c4787ca3b78529c9ea6b5b/LICENSE). [Metadata and evidence](data/projects/sparkdash.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-16. Archived: no. Disabled: no.
  - Note: The dashboard runs on Linux; monitored hosts may use other operating systems.
  - Note: Remote monitoring needs SSH access; review authentication before exposing the dashboard.

<a id="applications"></a>

### Applications and model management

- [Contemplative Agent](https://github.com/shimo4228/contemplative-agent): Run an autonomous agent on a local LLM through Ollama that posts on Moltbook, logs every action, and stages changes to its own prompts for a person to adopt or reject.
  - Local client or agent. Platforms: macOS. Hardware: Apple Silicon.
  - License: [MIT](https://raw.githubusercontent.com/shimo4228/contemplative-agent/620728552019f8be5ae9cb843400592ce5cde12d/LICENSE). [Metadata and evidence](data/projects/contemplative-agent.json).
  - Documentation reviewed: 2026-10-17. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-17. Archived: no. Disabled: no.
  - Note: Needs a separately installed Ollama and about 10 GB of disk for the models; the documented tested setup is an Apple Silicon Mac with 16 GB of memory.
  - Note: Posting is public and needs a Moltbook account; the owner verifies an email address and an X account (as of October 2026). A local two-agent dialogue runs without an account.
  - Note: Posts wait for confirmation by default, but scheduled sessions run with --auto and post without asking. The agent talks only to moltbook.com and to Ollama on localhost.
  - Note: A long-running research experiment, not a productivity tool; changes it proposes to its constitution, identity, and skills take effect only after a person adopts them.

- [Orkas](https://github.com/Orkas-AI/Orkas): Open-source, local-first desktop AI workforce where Commander coordinates specialist project work, with supported own-provider API keys and compatible local model endpoints.
  - Local client or agent. Platforms: macOS, Windows, Linux. Hardware: Not recorded.
  - License: [MIT](https://github.com/Orkas-AI/Orkas/blob/10e4e61b9e7549312060b9ee613c105228801181/LICENSE). [Metadata and evidence](data/projects/orkas.json).
  - Documentation reviewed: 2026-10-18. Repository: not checked yet.
  - Note: Orkas is a desktop client and agent workspace, not a model inference server; a suitable model endpoint is configured separately.
  - Note: Packaged installers cover macOS and Windows 10+; Linux currently runs from source on glibc 2.34+ x64 or arm64, not musl-based distributions.
  - Note: Local endpoint compatibility depends on the selected model and supported protocol; no hardware or model-level runtime certification was performed.
  - Note: Remote model providers and authorized external tools require network access and can receive task data; provider usage can cost extra.
  - Note: The source build has no Orkas account layer; packaged official builds require sign-in and optional managed services have separate terms.

- [SparkPilot](https://github.com/ashhart/SparkPilot): Connect Apple devices to DGX Spark for private chat, model management, and authenticated runtime access.
  - Local client or agent. Platforms: iOS, iPadOS, Linux. Hardware: DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/ashhart/SparkPilot/c9faa949be429da5cc5ab3579259d65aa6c3c5de/LICENSE). [Metadata and evidence](data/projects/sparkpilot.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-09-11. Archived: no. Disabled: no.
  - Note: Beta testing focuses on iPhone and iPad with Nemotron Lightning; the Linux tag describes the Spark runtime.
  - Note: A source build does not establish hardware qualification; not every development recipe is approved for distribution.
  - Note: The Qwen engine adaptation includes separately licensed AGPL components.

<a id="skills"></a>

### Agent skills and extensions

- [Matt Pocock's skills](https://github.com/mattpocock/skills): Add reusable engineering and productivity skills for planning, requirements, implementation, and review.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/mattpocock/skills/49dd158d1076134a641b33efb035946536778336/LICENSE). [Metadata and evidence](data/projects/matt-pocock-skills.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-13. Archived: no. Disabled: no.
  - Note: Model-agnostic skill instructions are not proof of reliable behavior with every local model.
  - Note: Review selected skills for commands, integrations, and permissions before loading them.

<a id="mcp"></a>

### MCP servers

No local-first entries yet. [Suggest a project](CONTRIBUTING.md).

Cloud-dependent entries are in [Cloud integrations](#cloud-integrations).

## Cloud integrations

These integrations connect agents to cloud services. They are not offline local AI tools.

- [gcloud MCP servers](https://github.com/googleapis/gcloud-mcp): Connect MCP-capable agents to Google Cloud management, observability, storage, and backup tools.
  - Cloud integration. Platforms: Not recorded. Hardware: Not recorded.
  - License: [Apache-2.0](https://raw.githubusercontent.com/googleapis/gcloud-mcp/238728f237ecb5f483199906b564a1767a0713f9/LICENSE). [Metadata and evidence](data/projects/gcloud-mcp.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-13. Archived: no. Disabled: no.
  - Note: Requires Google Cloud access and credentials; tool operations can change remote resources and incur charges.
  - Note: A locally running MCP process does not make its cloud operations offline.

- [Google Agent Skills](https://github.com/google/skills): Add agent skills for Google products and technologies, including Google Cloud workflows.
  - Cloud integration. Platforms: Not recorded. Hardware: Not recorded.
  - License: [Apache-2.0](https://raw.githubusercontent.com/google/skills/4b940dd4b5f5759794cc257266cb8cb7524b7a66/LICENSE). [Metadata and evidence](data/projects/google-skills.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-10-17 (reachable).
  - Last observed push: 2026-10-16. Archived: no. Disabled: no.
  - Note: Many skills require Google APIs, cloud resources, credentials, or billing; inspect each selected skill's requirements.
  - Note: The collection is listed as an optional cloud integration, not as a guarantee that every skill requires cloud access.

<!-- catalog:end -->

## How this list works

The source of truth is one JSON file per project in [`data/projects`](data/projects).
The task index and catalog above are generated from those files, with repository
observations from [`data/health.json`](data/health.json). No accounts,
submission fees, star-count thresholds, or paid placement. Self-submissions are welcome.

Listings describe what a tool does and where it fits. They are not rankings or
endorsements. Preview projects can be useful; their limitations should be visible.
The starting collection is Spark-heavy, and submissions for other hardware are welcome.

The scripts require Python 3.11 or newer and have no third-party dependencies:

```sh
python3 scripts/catalog.py validate
python3 scripts/catalog.py render
python3 scripts/catalog.py check
python3 -m unittest discover -s scripts -p 'test_*.py'
```

PR checks cover data validation, generated output, spelling, Markdown, and local
documentation links. Remote links in changed project records get an advisory check;
weekly checks cover all upstream links. See [the contribution guide](CONTRIBUTING.md)
for review criteria and local lint commands.

A separate weekly [health workflow](.github/workflows/health.yml) opens or updates
a reviewable PR for repository observations. It does not change documentation
review dates or remove projects. Routine health refreshes can merge automatically
after the [health safety gate](docs/maintenance.md#automatic-merging-of-routine-refreshes)
and CI pass; flagged refreshes and project submissions need human review.
Contributors record catalog changes in the [weekly changelog](CHANGELOG.md);
routine health snapshots are not new catalog entries or upstream release notes.

## License

The catalog, original documentation, and other original repository content are
dedicated to the public domain under [CC0-1.0](LICENSE), except for `scripts/` and
`.github/workflows/`, which use the [MIT license](scripts/LICENSE).

Listed projects, their dependencies, and model weights retain their own licenses.
An entry's license describes the upstream root license or package declaration;
it does not cover every bundled dependency or model. `null` means the license is
unclear, not that reuse is unrestricted. Confirm upstream terms before reuse.
