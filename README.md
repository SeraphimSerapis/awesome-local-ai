# Awesome Local AI

Tools for running, using, evaluating, and maintaining AI on your own hardware.
Browse by task, or ask your agent to find tools that fit your machine and workflow.

Local includes personal computers and self-hosted clusters. A project can support
cloud providers too, but its core listing must have a documented local use case.

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

### Run a model on my hardware

- [DwarfStar / ds4](#project-dwarfstar)
- [Kapitsa](#project-kapitsa)
- [mlx-serve](#project-mlx-serve)
- [Off Grid AI](#project-off-grid-ai)
- [oMLX](#project-omlx)
- [RAI](#project-rai)
- [spark-vllm-docker](#project-spark-vllm-docker)
- [sparkrun](#project-sparkrun)
- [Splash](#project-splash)
- [Strata](#project-strata)
- [TandemLLM](#project-tandemllm)
- [TensorFold](#project-tensorfold)
- [vLLM Windows Build](#project-vllm-windows-build)

### Connect a coding agent to a local model

- [DeepSeek Harness](#project-deepseek-harness)
- [DwarfStar / ds4](#project-dwarfstar)
- [Kapitsa](#project-kapitsa)
- [mlx-serve](#project-mlx-serve)
- [Oh My Pi](#project-oh-my-pi)
- [oMLX](#project-omlx)
- [Pi](#project-pi)
- [Splash](#project-splash)
- [Strata](#project-strata)
- [TandemLLM](#project-tandemllm)
- [TensorFold](#project-tensorfold)

### Run autonomous agents with local models

- [agent-qa](#project-agent-qa)
- [Contemplative Agent](#project-contemplative-agent)

### Test tool-calling quality

- [tool-eval-bench](#project-tool-eval-bench)

### Compare inference speed

- [llama-benchy](#project-llama-benchy)
- [tool-eval-bench](#project-tool-eval-bench)

### Deploy or manage a cluster

- [spark-vllm-docker](#project-spark-vllm-docker)
- [sparkrun](#project-sparkrun)

### Set up local AI

- [RAI](#project-rai)
- [sparkrun](#project-sparkrun)
- [vLLM Windows Build](#project-vllm-windows-build)
- [whichquant](#project-whichquant)

### Monitor my setup

- [SparkDash](#project-sparkdash)

### Troubleshoot my setup

- [Spark Doctor](#project-spark-doctor)

### Tune thermals and memory

- [DGX Spark Fan Control](#project-dgx-spark-fan-control)

### Validate or simulate inference configurations

- [whichquant](#project-whichquant)

### Chat with a local model

- [DwarfStar / ds4](#project-dwarfstar)
- [Kapitsa](#project-kapitsa)
- [mlx-serve](#project-mlx-serve)
- [Off Grid AI](#project-off-grid-ai)
- [oMLX](#project-omlx)
- [RAI](#project-rai)
- [Splash](#project-splash)
- [Strata](#project-strata)
- [ThreadShelf](#project-threadshelf)

### Add skills, extensions, or MCP tools

- [agent-qa](#project-agent-qa)
- [DeepSeek Harness](#project-deepseek-harness)
- [Oh My Pi](#project-oh-my-pi)
- [Pi](#project-pi)
- [ThreadShelf](#project-threadshelf)

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

<a id="inference"></a>

### Inference and serving

- <a id="project-dwarfstar"></a>[DwarfStar / ds4](https://github.com/antirez/ds4): Run a focused native inference engine and coding agent for selected large models on consumer hardware.
  - Local workload. Platforms: macOS, Linux. Hardware: Apple Silicon, NVIDIA GPU, AMD GPU, DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/antirez/ds4/fc80bd695da76ee14bcb86820bf900a5cdfda806/LICENSE). [Metadata and evidence](data/projects/dwarfstar.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-08. Archived: no. Disabled: no.
  - Note: Beta-quality software with fast-changing model support; uses project-produced GGUF files, not arbitrary GGUF models.
  - Note: Metal primarily targets Macs with 96 GB or more; smaller machines and larger models may need SSD streaming.

- <a id="project-kapitsa"></a>[Kapitsa](https://github.com/nace-ai/kapitsa): Serve Qwen, Nemotron, Flint and Clover models on Apple Silicon with a native C++ engine on Metal kernels and the Neural Engine, without an MLX or llama.cpp runtime.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/nace-ai/kapitsa/95a0a552fab5c359dd91b716e9936918d436d713/LICENSE). [Metadata and evidence](data/projects/kapitsa.json).
  - Documentation reviewed: 2026-11-08. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Requires Apple Silicon (M1 or newer) and macOS 14 or later; no Linux or Windows.
  - Note: Memory: the README points 16-24 GB Macs at the 9b model (or 4b); the 35B-A3B's 4-bit build is 22.1 GB and needs a 32 GB Mac, while its 2-bit builds fit 16-24 GB Macs.
  - Note: Runs the models in its catalog and imported Qwen or Flint GGUFs; Flint, Clover, the text-only Nemotrons and the 35B's 16gb build read text only.
  - Note: Checks GitHub once a day for a new release and can update itself; KAPITSA\_NO\_AUTO\_UPDATE=1 or kapitsa update --auto off turns this off.

- <a id="project-mlx-serve"></a>[mlx-serve](https://github.com/ddalcu/mlx-serve): Serve MLX and GGUF models on Apple Silicon through a native server with a companion model-management and chat app.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [MIT](https://raw.githubusercontent.com/ddalcu/mlx-serve/1b00c65a3cdf4a60a6e64709e150b75d4ecd8b02/LICENSE). [Metadata and evidence](data/projects/mlx-serve.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Requires macOS 26.2 or newer; confirm the selected model and modality against upstream documentation.

- <a id="project-omlx"></a>[oMLX](https://github.com/jundot/omlx): Serve local MLX models with continuous batching, tiered memory/SSD caching, and menu-bar management.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/jundot/omlx/013bc3f3a48fa9a4b7dffbfeb6cdc7c1face1c5d/LICENSE). [Metadata and evidence](data/projects/omlx.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Requires Apple Silicon and macOS 15 or newer; source installs require Python 3.11-3.13.
  - Note: Some model families require custom Metal kernels; use the packaged app or follow the full Xcode build requirements.

- <a id="project-rai"></a>[RAI](https://github.com/Classevelabs/rai): Run 4-bit language models on the CPU with a Rust engine, a local chat page and HTTP API, and one-step installers for Windows, macOS and Linux.
  - Local workload. Platforms: Linux, macOS, Windows. Hardware: CPU, Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/Classevelabs/rai/02b0b95c5e2225e6ea72d5fb3289ce368cb9b7d1/LICENSE). [Metadata and evidence](data/projects/rai.json).
  - Documentation reviewed: 2026-11-18. Repository: not checked yet.
  - Note: Runs only its own .raimodel format: GGUF files and pickle checkpoints such as pytorch\_model.bin are not read, and checkpoints outside the listed families are refused at conversion.
  - Note: Stores weights at 4 bits, with the embedding table at 8 bits.
  - Note: The AVX2 fast path needs an x86-64 CPU with AVX2, FMA and F16C; other CPUs, Apple Silicon included, use a portable path.
  - Note: Needs Windows 10 or 11, macOS 10.12 or later on Intel or 11 or later on Apple Silicon, or x86-64 Linux with glibc 2.28 or later; ARM Linux builds from source.
  - Note: rai-get-model downloads models from Hugging Face; the rai program itself makes no network connections.

- <a id="project-splash"></a>[Splash](https://github.com/incoai/splash): Serve supported models on Apple Silicon with speculative decoding, Metal kernels, and coding-agent integrations.
  - Local workload. Platforms: macOS. Hardware: Apple Silicon.
  - License: [Apache-2.0](https://raw.githubusercontent.com/incoai/splash/8a2b42069923d483151372b615f6182c72c2b6cd/LICENSE). [Metadata and evidence](data/projects/splash.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-11. Archived: no. Disabled: no.
  - Note: Requires Apple M3 or newer and macOS 26.4 or newer; memory requirements depend on model and quantization.
  - Note: Model and draft downloads need network access on first use.

- <a id="project-strata"></a>[Strata](https://github.com/Niko1221/Strata): Run supported Qwen models on Windows or Linux PCs with NVIDIA or AMD GPUs, with a local UI and model APIs.
  - Local workload. Platforms: Windows, Linux. Hardware: NVIDIA GPU, AMD GPU.
  - License: [MIT](https://raw.githubusercontent.com/Niko1221/Strata/61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406/LICENSE). [Metadata and evidence](data/projects/strata.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: The standard setup requires a supported GPU with at least 12 GB VRAM, at least 32 GB RAM, and about 80 GB free disk.
  - Note: Model support is specific; experimental hardware paths and AMD vision support have additional limits.

- <a id="project-tandemllm"></a>[TandemLLM](https://github.com/0xBakeer/TandemLLM): Serve Qwen3.8-27B on a single DGX Spark with speculative decoding, conversation caches, and a local dashboard.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [AGPL-3.0-only](https://raw.githubusercontent.com/0xBakeer/TandemLLM/c11aecaa7ba767642409ff51d90d48c79c572d3a/LICENSE). [Metadata and evidence](data/projects/tandemllm.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-12. Archived: no. Disabled: no.
  - Note: Currently qualified for one DGX Spark and Qwen3.8-27B; other CUDA GPUs are best effort.
  - Note: Requires the documented Python 3.11, PyTorch/CUDA, and Triton stack; run one engine per board.
  - Note: Code is AGPL-3.0-only with a separate commercial option; documentation and model artifacts have separate licenses.

- <a id="project-tensorfold"></a>[TensorFold](https://github.com/ashhart/TensorFold): Serve supported language models with a native inference engine using Metal or CUDA kernels.
  - Local workload. Platforms: macOS, Linux. Hardware: Apple Silicon, NVIDIA GPU, DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/ashhart/TensorFold/bec00ae6961a43a9ab73c4fa9338c167b3f82851/LICENSE). [Metadata and evidence](data/projects/tensorfold.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Model, checkpoint format, and hardware qualification are specific to each release; consult the qualification table.
  - Note: Experimental Living Weights modifies checkpoint files; teach a copy and keep the original.

<a id="deployment"></a>

### Deployment and bootstrapping

- <a id="project-spark-vllm-docker"></a>[spark-vllm-docker](https://github.com/eugr/spark-vllm-docker): Run vLLM in Docker on one or more DGX Spark systems with networking and distributed-inference setup scripts.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/eugr/spark-vllm-docker/a4c172976a5f9f8669b356a0891bf972cae14fd4/LICENSE). [Metadata and evidence](data/projects/spark-vllm-docker.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-07. Archived: no. Disabled: no.
  - Note: Targets DGX Spark; multi-node operation depends on compatible networking and model configuration.

- <a id="project-sparkrun"></a>[sparkrun](https://github.com/spark-arena/sparkrun): Launch, manage, and stop recipe-based inference workloads on single-node or multi-node DGX Spark setups.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [Apache-2.0](https://raw.githubusercontent.com/spark-arena/sparkrun/b444da874923fd27228dcb98ab844c328a91752d/LICENSE). [Metadata and evidence](data/projects/sparkrun.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-13. Archived: no. Disabled: no.
  - Note: Setup can change SSH, sudoers, and host services; review the recipe and requested permissions.
  - Note: Anonymous usage telemetry is on by default; SPARKRUN\_NO\_TELEMETRY=1 disables it for one process.
  - Note: The bundled SparkRoute integration has separate AGPL licensing; check the selected channel's defaults.

- <a id="project-vllm-windows-build"></a>[vLLM Windows Build](https://github.com/aivrar/vllm-windows-build): Install native Windows builds of vLLM with OpenAI-compatible serving on NVIDIA GPUs, without WSL, Docker, or a Linux VM.
  - Local workload. Platforms: Windows. Hardware: NVIDIA GPU.
  - License: [MIT](https://raw.githubusercontent.com/aivrar/vllm-windows-build/3974c4a568351fd2e41ff71922bd26146933c003/LICENSE). [Metadata and evidence](data/projects/vllm-windows-build.json).
  - Documentation reviewed: 2026-11-18. Repository: not checked yet.
  - Note: This is a community native Windows distribution; official vLLM support is Linux-only.
  - Note: Windows builds run on a single GPU per process because PyTorch on Windows lacks NCCL, so multi-GPU setups require separate vLLM instances per GPU with external load balancing.
  - Note: Requires Windows 10 21H2 or later (x64), an NVIDIA GPU with SM 7.5 or newer, at least 12 GB VRAM (24 GB recommended), at least 16 GB RAM, and a CUDA 13.0 driver (R580 or newer).
  - Note: Current wheels target Python 3.13 with CUDA 13.0 or Python 3.14 with CUDA 13.2. The R580 or newer driver requirement applies to the Python 3.13 CUDA 13.0 wheel, while upstream does not document a minimum driver for the Python 3.14 CUDA 13.2 wheel.
  - Note: v0.33.0 was GPU-validated on an RTX 3090. The Windows wheel does not include native Blackwell FP4 acceleration, and that 0.33.0 release has not been run on Blackwell hardware.
  - Note: The six bundled Multi-TurboQuant KV cache methods run on a PyTorch fallback at around 0.73 tok/s on the tested 14B RTX 3090 setup. The four upstream TurboQuant variants use fused Triton kernels.

- <a id="project-whichquant"></a>[whichquant](https://github.com/ngo-binh0108/whichquant): Check every GGUF quant in a Hugging Face repo against your GPU and RAM before downloading it, by reading only the file headers, and get the llama.cpp flags for each one.
  - Local workload. Platforms: Linux, macOS, Windows. Hardware: NVIDIA GPU, Apple Silicon.
  - License: [MIT](https://raw.githubusercontent.com/ngo-binh0108/whichquant/30bcc736095dc9ea80a6cd0f6686cb7855309226/LICENSE). [Metadata and evidence](data/projects/whichquant.json).
  - Documentation reviewed: 2026-11-18. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-11. Archived: no. Disabled: no.
  - Note: Weights are exact, but the compute buffer is an estimate and the KV cache follows llama.cpp's sizing rules.
  - Note: GPU memory is detected only on NVIDIA and Apple Silicon; AMD and Intel users pass it with --gpu.
  - Note: Checking a Hugging Face repo needs network access, and gated repos need HF\_TOKEN; local GGUF files work offline.
  - Note: It estimates fit and does not run or benchmark the model.

<a id="clustering"></a>

### Clustering and interconnects

No entries yet. [Suggest a project](CONTRIBUTING.md).

<a id="systems"></a>

### Systems

- <a id="project-dgx-spark-fan-control"></a>[DGX Spark Fan Control](https://github.com/christopherowen/dgx-spark-fan-control): Set minimum fan-speed floors or a temperature-based performance curve on qualified DGX Spark systems.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [GPL-2.0-only](https://raw.githubusercontent.com/christopherowen/dgx-spark-fan-control/deb2ea155f6698b769ff4977dea2119e3b32f460/LICENSE). [Metadata and evidence](data/projects/dgx-spark-fan-control.json).
  - Documentation reviewed: 2026-10-11. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-10-29. Archived: no. Disabled: no.
  - Note: Experimental; validated against specific NVIDIA kernel and EC firmware versions. Other GB10 variants are unverified.
  - Note: Needs root access and a locally built/signed kernel module; Secure Boot requires certificate enrollment.
  - Note: Sets minimums, not exact fan speeds. Hard crashes can prevent restoring automatic control, and manual floors have no expiry.

<a id="harnesses"></a>

### Agent harnesses

- <a id="project-deepseek-harness"></a>[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness): Run a plugin-based agent harness with a web UI and configurable model-provider adapters.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/d743267388641bc76f17c45ce8b4c231aed1d32c/LICENSE). [Metadata and evidence](data/projects/deepseek-harness.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-13. Archived: no. Disabled: no.
  - Note: Developer preview with compatibility-breaking changes; review the upstream safety notice.
  - Note: Self-hosted endpoints may need explicit request-compatibility settings; protocol support is not full feature certification.

- <a id="project-oh-my-pi"></a>[Oh My Pi](https://github.com/can1357/oh-my-pi): Use a coding-agent harness with IDE-oriented tools and configurable local model providers.
  - Local client or agent. Platforms: Linux, macOS, Windows. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/can1357/oh-my-pi/5063baf59ec68ad3f2bff060a3ba44b0547eee15/LICENSE). [Metadata and evidence](data/projects/oh-my-pi.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: A local provider still needs a separately running model server and model-specific capability checks.

- <a id="project-pi"></a>[Pi](https://github.com/earendil-works/pi): Use an extensible coding-agent harness with local model connections, skills, extensions, and automation interfaces.
  - Local client or agent. Platforms: Linux, macOS, Windows. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/earendil-works/pi/4ac0bd8c7b96d72cb6a73226edc7c9ecaae1d14e/LICENSE). [Metadata and evidence](data/projects/pi.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Local inference needs a separate model server; endpoint-specific behavior may need configuration.

<a id="evaluation"></a>

### Evaluation and benchmarking

- <a id="project-llama-benchy"></a>[llama-benchy](https://github.com/eugr/llama-benchy): Measure prompt-processing and token-generation speed at different context depths through a model server's API.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/eugr/llama-benchy/e9be344578cec17745066b220798b80a0d2686d3/LICENSE). [Metadata and evidence](data/projects/llama-benchy.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-07-10. Archived: no. Disabled: no.
  - Note: Measures serving performance, not tool-calling correctness or complete coding-agent quality.

- <a id="project-tool-eval-bench"></a>[tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench): Evaluate tool-calling quality and benchmark self-hosted model endpoints with deterministic scenarios and conversation traces.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [MIT](https://raw.githubusercontent.com/SeraphimSerapis/tool-eval-bench/b60e2f00f6c44352a3680356e7c7948f777c5280/LICENSE). [Metadata and evidence](data/projects/tool-eval-bench.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: Tests assistant conversations with mock tools, not full agent systems or multi-agent handoffs.
  - Note: Difficulty tiers are author estimates; localization coverage is German-focused.

<a id="monitoring"></a>

### Monitoring and diagnostics

- <a id="project-spark-doctor"></a>[Spark Doctor](https://github.com/joeynyc/spark-doctor): Collect DGX Spark diagnostics and explain likely system, runtime, network, and recipe problems from local evidence.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10.
  - License: [MIT](https://raw.githubusercontent.com/joeynyc/spark-doctor/e50a14faf5fed4a9f202663451db92da34979298/LICENSE). [Metadata and evidence](data/projects/spark-doctor.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-10-22. Archived: no. Disabled: no.
  - Note: Read-only diagnostics, not automatic repairs; requires Python 3.11 or newer.
  - Note: Review and anonymize diagnostic reports before sharing them.

- <a id="project-sparkdash"></a>[SparkDash](https://github.com/MiaAI-Lab/sparkDash): Monitor GPU, memory, network, and local model metrics across DGX Spark and other hosts in a web dashboard.
  - Local workload. Platforms: Linux. Hardware: DGX Spark / GB10, NVIDIA GPU.
  - License: [Apache-2.0](https://raw.githubusercontent.com/MiaAI-Lab/sparkDash/1403c1ce79db030645c4787ca3b78529c9ea6b5b/LICENSE). [Metadata and evidence](data/projects/sparkdash.json).
  - Documentation reviewed: 2026-10-10. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-16. Archived: no. Disabled: no.
  - Note: The dashboard runs on Linux; monitored hosts may use other operating systems.
  - Note: Remote monitoring needs SSH access; review authentication before exposing the dashboard.

<a id="applications"></a>

### Applications and model management

- <a id="project-contemplative-agent"></a>[Contemplative Agent](https://github.com/shimo4228/contemplative-agent): Run an autonomous agent on a local LLM through Ollama that posts on Moltbook, logs every action, and stages changes to its own prompts for a person to adopt or reject.
  - Local client or agent. Platforms: macOS. Hardware: Apple Silicon.
  - License: [MIT](https://raw.githubusercontent.com/shimo4228/contemplative-agent/620728552019f8be5ae9cb843400592ce5cde12d/LICENSE). [Metadata and evidence](data/projects/contemplative-agent.json).
  - Documentation reviewed: 2026-10-17. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-11. Archived: no. Disabled: no.
  - Note: Needs a separately installed Ollama and about 10 GB of disk for the models; the documented tested setup is an Apple Silicon Mac with 16 GB of memory.
  - Note: Posting is public and needs a Moltbook account; the owner verifies an email address and an X account (as of October 2026). A local two-agent dialogue runs without an account.
  - Note: Posts wait for confirmation by default, but scheduled sessions run with --auto and post without asking. The agent talks only to moltbook.com and to Ollama on localhost.
  - Note: A long-running research experiment, not a productivity tool; changes it proposes to its constitution, identity, and skills take effect only after a person adopts them.

- <a id="project-off-grid-ai"></a>[Off Grid AI](https://github.com/off-grid-ai/OGAD): Desktop app for local chat with text and vision models, image generation, speech-to-text and text-to-speech, plus a local OpenAI-compatible API.
  - Local workload. Platforms: macOS, Windows, Linux. Hardware: Apple Silicon, CPU.
  - License: [AGPL-3.0-only](https://raw.githubusercontent.com/off-grid-ai/OGAD/312b8f45ef6afdd2bff3f7be130b4d0a23124bc8/LICENSE). [Metadata and evidence](data/projects/off-grid-ai.json).
  - Documentation reviewed: 2026-11-18. Repository: not checked yet.
  - Note: Release builds cover macOS on Apple Silicon, Windows x64 and Linux x64 (Ubuntu 24.04 or newer).
  - Note: Model downloads come from Hugging Face; the app checks for signed updates. Anonymous usage data and crash reports are sent only if the user turns them on.
  - Note: The gateway listens on all IPv4 interfaces. API-key authentication is optional and off by default; reachable network peers can use model routes unless authentication is enabled.
  - Note: An optional paid Pro layer (screen memory, meetings, dictation, clipboard) lives in a separate private package; the Linux build does not include it.

- <a id="project-threadshelf"></a>[ThreadShelf](https://github.com/ChrystianSchutz/ThreadShelf): Index ChatGPT, Claude, Google AI Studio, OpenRouter, LM Studio and Grok exports locally for semantic and exact search, then continue old threads with local GGUF models.
  - Local workload. Platforms: Linux, macOS, Windows. Hardware: CPU.
  - License: [MIT](https://raw.githubusercontent.com/ChrystianSchutz/ThreadShelf/f13b721561305c3b040dc701ce86553ec36c4447/LICENSE). [Metadata and evidence](data/projects/threadshelf.json).
  - Documentation reviewed: 2026-11-08. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-10-28. Archived: no. Disabled: no.
  - Note: Single-user application: the HTTP API has no accounts or authentication and should stay on loopback unless deliberately exposed on a trusted network.
  - Note: The local embedding model downloads once on first indexing; llama.cpp builds come from GitHub Releases and GGUF models from Hugging Face only when the user asks.
  - Note: Optional OpenRouter generation is off-device: it sends the selected conversation history and prompt to OpenRouter and the routed provider.
  - Note: Google AI Studio, OpenRouter, LM Studio and Grok exports use undocumented formats that can change without notice.
  - Note: Requires Node.js 20.19 or newer; installed through npm (npx threadshelf).

<a id="skills"></a>

### Agent skills and extensions

No entries yet. [Suggest a project](CONTRIBUTING.md).

<a id="mcp"></a>

### MCP servers

- <a id="project-agent-qa"></a>[agent-qa](https://github.com/vostride/agent-qa): Test web and mobile apps through a local CLI/MCP server with local model endpoints, memidex memory and validated self-improvement.
  - Local client or agent. Platforms: Not recorded. Hardware: Not recorded.
  - License: [FSL-1.1-ALv2](https://raw.githubusercontent.com/vostride/agent-qa/1b8a9daf46dd0ec1b2c4503d2f1c0e26b0002293/LICENSE.md). [Metadata and evidence](data/projects/agent-qa.json).
  - Documentation reviewed: 2026-10-31. Repository checked: 2026-11-16 (reachable).
  - Last observed push: 2026-11-14. Archived: no. Disabled: no.
  - Note: Early-stage project; the pinned upstream README warns that bugs should be expected.
  - Note: Requires Node.js 24+ and a separately configured model server. Specific model, hardware and host OS combinations were not runtime-tested for this catalog.
  - Note: Visual checks need an image-capable model; text-only mode omits screenshots and cannot verify visual details.
  - Note: Mobile testing needs Appium and platform tooling; iOS needs macOS and Xcode. Docker is required only for hooks.
  - Note: App observations go to the configured model provider. Runs and MCP tools act without approval prompts; use limited test accounts and review plugins, which have full machine access.
  - Note: Released versions send usage analytics unless analytics.privacy is true, and run/dashboard update checks contact npm; local model configuration does not guarantee offline operation.
  - Note: FSL-1.1-ALv2 restricts use to the license's Permitted Purpose; each version transitions to Apache-2.0 after two years.

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
documentation links. Remote links in changed project records and changelog
fragments get an advisory check; weekly checks cover all upstream links. See
[the contribution guide](CONTRIBUTING.md) for review criteria and local lint
commands.

A separate weekly [health workflow](.github/workflows/health.yml) opens or updates
a reviewable PR for repository observations. It does not change documentation
review dates or remove projects. Routine health refreshes can merge automatically
after the [health safety gate](docs/maintenance.md#automatic-merging-of-routine-refreshes)
and CI pass; flagged refreshes and project submissions need human review.
Contributors add fragments in `changelog.d/` for the [weekly changelog](CHANGELOG.md);
routine health snapshots are not new catalog entries or upstream release notes.

## License

The catalog, original documentation, and other original repository content are
dedicated to the public domain under [CC0-1.0](LICENSE), except for `scripts/` and
`.github/workflows/`, which use the [MIT license](scripts/LICENSE).

Listed projects, their dependencies, and model weights retain their own licenses.
An entry's license describes the upstream root license or package declaration;
it does not cover every bundled dependency or model. `null` means the license is
unclear, not that reuse is unrestricted. Confirm upstream terms before reuse.
