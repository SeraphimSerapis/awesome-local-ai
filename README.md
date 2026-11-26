# Awesome Local AI

Tools for running, using, evaluating, and maintaining AI on your own hardware.
Browse by task, or ask your agent to find tools that fit your machine and workflow.

Local includes personal computers and self-hosted clusters. A project can support
cloud providers too, but every listing must have a documented local use case.

## Start here

- [Find tools by task](#find-tools-by-task)
- [Browse by category](#browse-by-category)
- [Weekly catalog changelog](CHANGELOG.md)
- [Understand review and activity dates](docs/maintenance.md)
- [Submit or update a project](CONTRIBUTING.md)
- [Let an agent help you choose](AGENTS.md)
- [Machine-readable catalog index (JSON)](data/catalog.json)
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
checks report GitHub metadata separately: reachability, default-branch commit
date, last observed push, archived/disabled flags, and repository redirects.
Recent pushes do not prove maintenance or quality, and inactivity does not prove
abandonment. See [maintenance](docs/maintenance.md).

<!-- catalog:start -->

## Find tools by task

- **Run a model on my hardware:**
  [AudioSmith](#project-audiosmith),
  [DwarfStar / ds4](#project-dwarfstar),
  [Kapitsa](#project-kapitsa),
  [Live Translator](#project-live-translator),
  [mlx-serve](#project-mlx-serve),
  [Off Grid AI](#project-off-grid-ai),
  [oMLX](#project-omlx),
  [RAI](#project-rai),
  [spark-vllm-docker](#project-spark-vllm-docker),
  [sparkrun](#project-sparkrun),
  [Splash](#project-splash),
  [Strata](#project-strata),
  [TandemEngine (TandemLLM)](#project-tandemllm),
  [TensorFold](#project-tensorfold),
  [vLLM Windows Build](#project-vllm-windows-build),
  [VoxtMini](#project-voxtmini)
- **Connect a coding agent to a local model:**
  [DeepSeek Harness](#project-deepseek-harness),
  [DwarfStar / ds4](#project-dwarfstar),
  [Kapitsa](#project-kapitsa),
  [mlx-serve](#project-mlx-serve),
  [Oh My Pi](#project-oh-my-pi),
  [oMLX](#project-omlx),
  [Pi](#project-pi),
  [Splash](#project-splash),
  [Strata](#project-strata),
  [TandemEngine (TandemLLM)](#project-tandemllm),
  [TensorFold](#project-tensorfold)
- **Run autonomous agents with local models:**
  [Contemplative Agent](#project-contemplative-agent)
- **Test tool-calling quality:**
  [tool-eval-bench](#project-tool-eval-bench)
- **Compare inference speed:**
  [llama-benchy](#project-llama-benchy),
  [tool-eval-bench](#project-tool-eval-bench)
- **Deploy or manage a cluster:**
  [spark-vllm-docker](#project-spark-vllm-docker),
  [sparkrun](#project-sparkrun)
- **Set up local AI:**
  [RAI](#project-rai),
  [sparkrun](#project-sparkrun),
  [vLLM Windows Build](#project-vllm-windows-build),
  [whichquant](#project-whichquant)
- **Monitor my setup:**
  [SparkDash](#project-sparkdash)
- **Troubleshoot my setup:**
  [Spark Doctor](#project-spark-doctor)
- **Validate or simulate inference configurations:**
  [whichquant](#project-whichquant)
- **Chat with a local model:**
  [DwarfStar / ds4](#project-dwarfstar),
  [Kapitsa](#project-kapitsa),
  [mlx-serve](#project-mlx-serve),
  [Off Grid AI](#project-off-grid-ai),
  [oMLX](#project-omlx),
  [RAI](#project-rai),
  [Splash](#project-splash),
  [Strata](#project-strata),
  [ThreadShelf](#project-threadshelf)
- **Add skills, extensions, or MCP tools:**
  [AudioSmith](#project-audiosmith),
  [ClickHouse Loom](#project-clickhouse-loom),
  [DeepSeek Harness](#project-deepseek-harness),
  [Oh My Pi](#project-oh-my-pi),
  [Pi](#project-pi),
  [ThreadShelf](#project-threadshelf)

## Browse by category

- [Inference and serving](#inference)
- [Deployment and bootstrapping](#deployment)
- [Agent harnesses](#harnesses)
- [Evaluation and benchmarking](#evaluation)
- [Monitoring and diagnostics](#monitoring)
- [Applications and model management](#applications)
- [MCP servers](#mcp)
- [Open categories](#open-categories): [Clustering and interconnects](#clustering), [Systems](#systems), [Agent skills and extensions](#skills)

Mode: **Local** runs the main AI workload locally; **Client** connects to a separate local model server or hardware runtime. Platforms and hardware reflect physically tested targets; `Not recorded` means unverified, not universal support. Activity shows the latest observed default-branch commit date from [the health snapshot](data/health.json), last updated 2026-11-26, or a bold alert when unchecked or flagged. Expand the notes block under each category for compatibility, limitations, and human documentation-review dates.

<a id="inference"></a>

### Inference and serving

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-dwarfstar"></a>[DwarfStar / ds4](https://github.com/antirez/ds4) | Run a focused native inference engine and coding agent for selected large models on consumer hardware. | Local | macOS, Linux | Apple Silicon, NVIDIA GPU, AMD GPU, DGX Spark / GB10 | [MIT](https://raw.githubusercontent.com/antirez/ds4/fc80bd695da76ee14bcb86820bf900a5cdfda806/LICENSE) | 2026-11-03; [JSON](data/projects/dwarfstar.json) |
| <a id="project-kapitsa"></a>[Kapitsa](https://github.com/nace-ai/kapitsa) | Serve Qwen, Nemotron, Flint and Clover models on Apple Silicon with a native C++ engine on Metal kernels and the Neural Engine, without an MLX or llama.cpp runtime. | Local | macOS | Apple Silicon | [Apache-2.0](https://raw.githubusercontent.com/nace-ai/kapitsa/95a0a552fab5c359dd91b716e9936918d436d713/LICENSE) | 2026-11-25; [JSON](data/projects/kapitsa.json) |
| <a id="project-mlx-serve"></a>[mlx-serve](https://github.com/ddalcu/mlx-serve) | Serve MLX and GGUF models on Apple Silicon through a native server with a companion model-management and chat app. | Local | macOS | Apple Silicon | [MIT](https://raw.githubusercontent.com/ddalcu/mlx-serve/1b00c65a3cdf4a60a6e64709e150b75d4ecd8b02/LICENSE) | 2026-11-26; [JSON](data/projects/mlx-serve.json) |
| <a id="project-omlx"></a>[oMLX](https://github.com/jundot/omlx) | Serve local MLX models with continuous batching, tiered memory/SSD caching, and menu-bar management. | Local | macOS | Apple Silicon | [Apache-2.0](https://raw.githubusercontent.com/jundot/omlx/013bc3f3a48fa9a4b7dffbfeb6cdc7c1face1c5d/LICENSE) | 2026-11-26; [JSON](data/projects/omlx.json) |
| <a id="project-rai"></a>[RAI](https://github.com/Classevelabs/rai) | Run 4-bit language models on the CPU with a Rust engine, a local chat page and HTTP API, and one-step installers for Windows, macOS and Linux. | Local | Linux, macOS, Windows | CPU, Apple Silicon | [Apache-2.0](https://raw.githubusercontent.com/Classevelabs/rai/02b0b95c5e2225e6ea72d5fb3289ce368cb9b7d1/LICENSE) | 2026-11-17; [JSON](data/projects/rai.json) |
| <a id="project-splash"></a>[Splash](https://github.com/incoai/splash) | Serve supported models on Apple Silicon with speculative decoding, Metal kernels, and coding-agent integrations. | Local | macOS | Apple Silicon | [Apache-2.0](https://raw.githubusercontent.com/incoai/splash/8a2b42069923d483151372b615f6182c72c2b6cd/LICENSE) | 2026-11-25; [JSON](data/projects/splash.json) |
| <a id="project-strata"></a>[Strata](https://github.com/Niko1221/Strata) | Run supported Qwen models on Windows or Linux PCs with NVIDIA or AMD GPUs, with a local UI and model APIs. | Local | Windows, Linux | NVIDIA GPU, AMD GPU | [MIT](https://raw.githubusercontent.com/Niko1221/Strata/61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406/LICENSE) | 2026-11-25; [JSON](data/projects/strata.json) |
| <a id="project-tandemllm"></a>[TandemEngine (TandemLLM)](https://github.com/TandemLLM/TandemEngine) | Serve supported LLMs on a single DGX Spark with speculative decoding, conversation caches, and an OpenAI-compatible API. | Local | Linux | DGX Spark / GB10 | [AGPL-3.0-only](https://raw.githubusercontent.com/TandemLLM/TandemEngine/da76b01a499d8014d57bf16721d5354dc6d67350/LICENSE) | 2026-11-24; [JSON](data/projects/tandemllm.json) |
| <a id="project-tensorfold"></a>[TensorFold](https://github.com/ashhart/TensorFold) | Serve supported language models with a native inference engine using Metal or CUDA kernels. | Local | macOS, Linux | Apple Silicon, NVIDIA GPU, DGX Spark / GB10 | [Apache-2.0](https://raw.githubusercontent.com/ashhart/TensorFold/bec00ae6961a43a9ab73c4fa9338c167b3f82851/LICENSE) | 2026-11-26; [JSON](data/projects/tensorfold.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **DwarfStar / ds4**, reviewed 2026-10-10; default-branch commit 2026-11-03, push 2026-11-08; [record](data/projects/dwarfstar.json)
  - **Compatibility:**
    - Metal, CUDA, and ROCm backends; native coding agent and HTTP server.
    - OpenAI-style Chat Completions, Responses, and Completions; Anthropic-style Messages.
  - **Limitations:**
    - Beta-quality software with fast-changing model support; uses project-produced GGUF files, not arbitrary GGUF models.
    - Metal primarily targets Macs with 96 GB or more; smaller machines and larger models may need SSD streaming.

- **Kapitsa**, reviewed 2026-11-08; last commit 2026-11-25; [record](data/projects/kapitsa.json)
  - **Compatibility:**
    - OpenAI- and Anthropic-compatible HTTP APIs (/v1/chat/completions, /v1/messages, /v1/responses) and a chat page.
    - Starts opencode, Claude Code, Codex or pi on a local model with one command.
    - Imports Qwen or Flint GGUF files from LM Studio, Ollama or llama.cpp.
  - **Limitations:**
    - Requires Apple Silicon (M1 or newer) and macOS 14 or later; no Linux or Windows.
    - Memory: the README points 16-24 GB Macs at the 9b model (or 4b); the 35B-A3B's 4-bit build is 22.1 GB and needs a 32 GB Mac, while its 2-bit builds fit 16-24 GB Macs.
    - Runs the models in its catalog and imported Qwen or Flint GGUFs; Flint, Clover, the text-only Nemotrons and the 35B's 16gb build read text only.
    - Checks GitHub once a day for a new release and can update itself; KAPITSA\_NO\_AUTO\_UPDATE=1 or kapitsa update --auto off turns this off.

- **mlx-serve**, reviewed 2026-10-10; last commit 2026-11-26; [record](data/projects/mlx-serve.json)
  - **Compatibility:** OpenAI- and Anthropic-compatible HTTP APIs; companion app with agent mode and MCP tools.
  - **Limitations:** Requires macOS 26.2 or newer; confirm the selected model and modality against upstream documentation.

- **oMLX**, reviewed 2026-10-10; last commit 2026-11-26; [record](data/projects/omlx.json)
  - **Compatibility:** MLX model serving; optional MCP support.
  - **Limitations:**
    - Requires Apple Silicon and macOS 15 or newer; source installs require Python 3.11-3.13.
    - Some model families require custom Metal kernels; use the packaged app or follow the full Xcode build requirements.

- **RAI**, reviewed 2026-11-18; last commit 2026-11-17; [record](data/projects/rai.json)
  - **Compatibility:**
    - Converts Hugging Face safetensors checkpoints of Llama 2 to 3.2, Mistral 7B, Mixtral 8x7B, Qwen 2 to 3, Gemma 1 and 2, Gemma 3 270M and 1B, Phi-3 mini 4k, OLMo 2, OLMoE, TinyLlama and SmolLM to its own .raimodel format, without Python.
    - Serves a chat page and a JSON chat API (/api/chat, streaming at /api/chat/stream) on 127.0.0.1, and answers single prompts from the command line.
    - rai-get-model downloads Qwen2.5 Instruct starter models (0.5B, 1.5B, 7B) pinned to one Hugging Face commit and checked file by file against SHA-256.
  - **Limitations:**
    - Runs only its own .raimodel format: GGUF files and pickle checkpoints such as pytorch\_model.bin are not read, and checkpoints outside the listed families are refused at conversion.
    - Stores weights at 4 bits, with the embedding table at 8 bits.
    - The AVX2 fast path needs an x86-64 CPU with AVX2, FMA and F16C; other CPUs, Apple Silicon included, use a portable path.
    - Needs Windows 10 or 11, macOS 10.12 or later on Intel or 11 or later on Apple Silicon, or x86-64 Linux with glibc 2.28 or later; ARM Linux builds from source.
    - rai-get-model downloads models from Hugging Face; the rai program itself makes no network connections.

- **Splash**, reviewed 2026-10-10; last commit 2026-11-25; [record](data/projects/splash.json)
  - **Compatibility:** OpenAI Chat Completions, Responses, and Completions; Anthropic Messages; documented Pi launch command.
  - **Limitations:**
    - Requires Apple M3 or newer and macOS 26.4 or newer; memory requirements depend on model and quantization.
    - Model and draft downloads need network access on first use.

- **Strata**, reviewed 2026-10-10; last commit 2026-11-25; [record](data/projects/strata.json)
  - **Compatibility:** OpenAI-compatible API, Anthropic Messages, OpenAI Responses, and a setup MCP server.
  - **Limitations:**
    - The standard setup requires a supported GPU with at least 12 GB VRAM, at least 32 GB RAM, and about 80 GB free disk.
    - Model support is specific; experimental hardware paths and AMD vision support have additional limits.

- **TandemEngine (TandemLLM)**, reviewed 2026-11-24; last commit 2026-11-24; [record](data/projects/tandemllm.json)
  - **Compatibility:** OpenAI-compatible model API with tool calls and structured output; documented TandemApp and opencode client paths.
  - **Limitations:**
    - Qualified for one DGX Spark (GB10) serving one supported model at a time; other CUDA GPUs are best effort.
    - Requires the documented Linux, Python 3.11, PyTorch 2.13/CUDA 13.0, and Triton stack; run one engine per board and set an admin password before exposing the port.
    - The web dashboard and chat UI moved to TandemApp; engine code is AGPL-3.0-only with a commercial option, while docs and model weights carry separate licenses.

- **TensorFold**, reviewed 2026-10-10; last commit 2026-11-26; [record](data/projects/tensorfold.json)
  - **Compatibility:** OpenAI Chat Completions, Completions, and Responses; Anthropic Messages.
  - **Limitations:**
    - Model, checkpoint format, and hardware qualification are specific to each release; consult the qualification table.
    - Experimental Living Weights modifies checkpoint files; teach a copy and keep the original.

</details>

<a id="deployment"></a>

### Deployment and bootstrapping

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-spark-vllm-docker"></a>[spark-vllm-docker](https://github.com/eugr/spark-vllm-docker) | Run vLLM in Docker on one or more DGX Spark systems with networking and distributed-inference setup scripts. | Local | Linux | DGX Spark / GB10 | [MIT](https://raw.githubusercontent.com/eugr/spark-vllm-docker/a4c172976a5f9f8669b356a0891bf972cae14fd4/LICENSE) | 2026-11-25; [JSON](data/projects/spark-vllm-docker.json) |
| <a id="project-sparkrun"></a>[sparkrun](https://github.com/spark-arena/sparkrun) | Launch, manage, and stop recipe-based inference workloads on single-node or multi-node DGX Spark setups. | Local | Linux | DGX Spark / GB10 | [Apache-2.0](https://raw.githubusercontent.com/spark-arena/sparkrun/593e3920ca2f74b8aa1cd59446ccbc4eeb307307/LICENSE) | 2026-10-26; [JSON](data/projects/sparkrun.json) |
| <a id="project-vllm-windows-build"></a>[vLLM Windows Build](https://github.com/aivrar/vllm-windows-build) | Install native Windows builds of vLLM with OpenAI-compatible serving on NVIDIA GPUs, without WSL, Docker, or a Linux VM. | Local | Windows | NVIDIA GPU | [MIT](https://raw.githubusercontent.com/aivrar/vllm-windows-build/3974c4a568351fd2e41ff71922bd26146933c003/LICENSE) | 2026-11-19; [JSON](data/projects/vllm-windows-build.json) |
| <a id="project-whichquant"></a>[whichquant](https://github.com/ngo-binh0108/whichquant) | Check every GGUF quant in a Hugging Face repo against your GPU and RAM before downloading it, by reading only the file headers, and get the llama.cpp flags for each one. | Client | Linux, macOS, Windows | Not recorded | [MIT](https://raw.githubusercontent.com/ngo-binh0108/whichquant/5e1d9b09cabbf7fee09877b42d0c7775ab3c7f6d/LICENSE) | 2026-11-19; [JSON](data/projects/whichquant.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **spark-vllm-docker**, reviewed 2026-10-10; last commit 2026-11-25; [record](data/projects/spark-vllm-docker.json)
  - **Compatibility:** vLLM; Ray or native PyTorch distributed execution; NCCL/RDMA.
  - **Limitations:** Targets DGX Spark; multi-node operation depends on compatible networking and model configuration.

- **sparkrun**, reviewed 2026-11-26; default-branch commit 2026-10-26, push 2026-11-25; [record](data/projects/sparkrun.json)
  - **Compatibility:**
    - vLLM, SGLang, and llama.cpp recipes; SSH-based node management and InfiniBand/RDMA tensor parallelism.
    - Bundled LiteLLM proxy gateway by default across stable, beta, and alpha channels; optional external plugin integrations such as SparkRoute and ColdSnap.
  - **Limitations:**
    - Guided setup configures SSH mesh, ConnectX-7 NICs, sudoers, and earlyoom, and sparkrun update refreshes managed plugins and recipe registries unless --no-update-plugins is passed; review recipes and permissions before running.
    - Anonymous usage telemetry to telemetry.sparkrun.dev is enabled by default; disable persistently with sparkrun setup telemetry --disable or for one process with SPARKRUN\_NO\_TELEMETRY=1.
    - SparkRoute and ColdSnap are not bundled and are installed separately as external plugins with their own upstream repositories and licenses; OCI Relay remains bundled.

- **vLLM Windows Build**, reviewed 2026-11-18; last commit 2026-11-19; [record](data/projects/vllm-windows-build.json)
  - **Compatibility:** OpenAI-compatible HTTP serving through vllm\_launcher.py and the upstream OpenAI API server, including /v1/models and streaming.
  - **Limitations:**
    - This is a community native Windows distribution; official vLLM support is Linux-only.
    - Windows builds run on a single GPU per process because PyTorch on Windows lacks NCCL, so multi-GPU setups require separate vLLM instances per GPU with external load balancing.
    - Requires Windows 10 21H2 or later (x64), an NVIDIA GPU with SM 7.5 or newer, at least 12 GB VRAM (24 GB recommended), at least 16 GB RAM, and a CUDA 13.0 driver (R580 or newer).
    - Current wheels target Python 3.13 with CUDA 13.0 or Python 3.14 with CUDA 13.2. The R580 or newer driver requirement applies to the Python 3.13 CUDA 13.0 wheel, while upstream does not document a minimum driver for the Python 3.14 CUDA 13.2 wheel.
    - v0.33.0 was GPU-validated on an RTX 3090. The Windows wheel does not include native Blackwell FP4 acceleration, and that 0.33.0 release has not been run on Blackwell hardware.
    - The six bundled Multi-TurboQuant KV cache methods run on a PyTorch fallback at around 0.73 tok/s on the tested 14B RTX 3090 setup. The four upstream TurboQuant variants use fused Triton kernels.

- **whichquant**, reviewed 2026-11-26; last commit 2026-11-19; [record](data/projects/whichquant.json)
  - **Compatibility:**
    - Prints llama.cpp flags for each quant, counts optional vision-projector and draft-model memory, and with -q prints llama-server and KoboldCpp commands including draft-model flags.
    - Pure Python 3.9+ standard-library CLI with zero runtime dependencies; reads local GGUF files or remote Hugging Face GGUF headers over HTTP range requests.
  - **Limitations:**
    - Weights are exact, but the compute buffer is an estimate and the KV cache follows llama.cpp's sizing rules; it estimates fit and does not run or benchmark the model.
    - Hardware tags are omitted because CI tests only CPU environments with explicit --gpu/--ram flags; auto-detection reads nvidia-smi on NVIDIA GPUs and macOS unified-memory defaults on Apple Silicon, while AMD and Intel users pass --gpu.
    - Checking a Hugging Face repo needs network access, and gated repos need HF\_TOKEN; local GGUF files work offline.
    - Currently distributed as a Git source install (version 0.2.0 in pyproject.toml) with no tagged GitHub release or PyPI package yet.

</details>

<a id="harnesses"></a>

### Agent harnesses

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-deepseek-harness"></a>[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) | Run a plugin-based agent harness with a web UI and configurable model-provider adapters. | Client | Not recorded | Not recorded | [MIT](https://raw.githubusercontent.com/deepseek-ai/deepseek-harness/d743267388641bc76f17c45ce8b4c231aed1d32c/LICENSE) | 2026-11-22; [JSON](data/projects/deepseek-harness.json) |
| <a id="project-oh-my-pi"></a>[Oh My Pi](https://github.com/can1357/oh-my-pi) | Use a coding-agent harness with IDE-oriented tools and configurable local model providers. | Client | Linux, macOS, Windows | Not recorded | [MIT](https://raw.githubusercontent.com/can1357/oh-my-pi/5063baf59ec68ad3f2bff060a3ba44b0547eee15/LICENSE) | 2026-11-26; [JSON](data/projects/oh-my-pi.json) |
| <a id="project-pi"></a>[Pi](https://github.com/earendil-works/pi) | Use an extensible coding-agent harness with local model connections, skills, extensions, and automation interfaces. | Client | Linux, macOS, Windows | Not recorded | [MIT](https://raw.githubusercontent.com/earendil-works/pi/4ac0bd8c7b96d72cb6a73226edc7c9ecaae1d14e/LICENSE) | 2026-11-26; [JSON](data/projects/pi.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **DeepSeek Harness**, reviewed 2026-10-10; last commit 2026-11-22; [record](data/projects/deepseek-harness.json)
  - **Compatibility:** Custom self-hosted model APIs using OpenAI Chat Completions, Responses, or Anthropic Messages.
  - **Limitations:**
    - Developer preview with compatibility-breaking changes; review the upstream safety notice.
    - Self-hosted endpoints may need explicit request-compatibility settings; protocol support is not full feature certification.

- **Oh My Pi**, reviewed 2026-10-10; last commit 2026-11-26; [record](data/projects/oh-my-pi.json)
  - **Compatibility:** Local Ollama, LM Studio, llama.cpp, and vLLM endpoints; custom OpenAI-compatible providers.
  - **Limitations:** A local provider still needs a separately running model server and model-specific capability checks.

- **Pi**, reviewed 2026-10-10; last commit 2026-11-26; [record](data/projects/pi.json)
  - **Compatibility:** llama.cpp router; custom OpenAI-, Anthropic-, or Google-compatible endpoints; skills and extensions.
  - **Limitations:** Local inference needs a separate model server; endpoint-specific behavior may need configuration.

</details>

<a id="evaluation"></a>

### Evaluation and benchmarking

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-llama-benchy"></a>[llama-benchy](https://github.com/eugr/llama-benchy) | Measure prompt-processing and token-generation speed at different context depths through a model server's API. | Client | Not recorded | Not recorded | [MIT](https://raw.githubusercontent.com/eugr/llama-benchy/e9be344578cec17745066b220798b80a0d2686d3/LICENSE) | 2026-07-10; [JSON](data/projects/llama-benchy.json) |
| <a id="project-tool-eval-bench"></a>[tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) | Evaluate tool-calling quality and benchmark self-hosted model endpoints with deterministic scenarios and conversation traces. | Client | Not recorded | Not recorded | [MIT](https://raw.githubusercontent.com/SeraphimSerapis/tool-eval-bench/b60e2f00f6c44352a3680356e7c7948f777c5280/LICENSE) | 2026-11-25; [JSON](data/projects/tool-eval-bench.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **llama-benchy**, reviewed 2026-10-10; last commit 2026-07-10; [record](data/projects/llama-benchy.json)
  - **Compatibility:** OpenAI-compatible /v1/chat/completions endpoints.
  - **Limitations:** Measures serving performance, not tool-calling correctness or complete coding-agent quality.

- **tool-eval-bench**, reviewed 2026-10-10; last commit 2026-11-25; [record](data/projects/tool-eval-bench.json)
  - **Compatibility:**
    - OpenAI-compatible Chat Completions endpoints; additional hosted-provider adapters.
    - Python 3.11 or newer; optional Docker deployment.
  - **Limitations:**
    - Tests assistant conversations with mock tools, not full agent systems or multi-agent handoffs.
    - Difficulty tiers are author estimates; localization coverage is German-focused.

</details>

<a id="monitoring"></a>

### Monitoring and diagnostics

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-spark-doctor"></a>[Spark Doctor](https://github.com/joeynyc/spark-doctor) | Collect DGX Spark diagnostics and explain likely system, runtime, network, and recipe problems from local evidence. | Local | Linux | DGX Spark / GB10 | [MIT](https://raw.githubusercontent.com/joeynyc/spark-doctor/e50a14faf5fed4a9f202663451db92da34979298/LICENSE) | 2026-11-18; [JSON](data/projects/spark-doctor.json) |
| <a id="project-sparkdash"></a>[SparkDash](https://github.com/MiaAI-Lab/sparkDash) | Monitor GPU, memory, network, and local model metrics across DGX Spark and other hosts in a web dashboard. | Local | Linux | DGX Spark / GB10, NVIDIA GPU | [Apache-2.0](https://raw.githubusercontent.com/MiaAI-Lab/sparkDash/1403c1ce79db030645c4787ca3b78529c9ea6b5b/LICENSE) | 2026-11-25; [JSON](data/projects/sparkdash.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **Spark Doctor**, reviewed 2026-10-10; last commit 2026-11-18; [record](data/projects/spark-doctor.json)
  - **Compatibility:** DGX Spark system and Docker diagnostics; JSON and Markdown reports.
  - **Limitations:**
    - Read-only diagnostics, not automatic repairs; requires Python 3.11 or newer.
    - Review and anonymize diagnostic reports before sharing them.

- **SparkDash**, reviewed 2026-10-10; last commit 2026-11-25; [record](data/projects/sparkdash.json)
  - **Compatibility:** SSH collectors for Linux, macOS, and Windows hosts; HTTP probes for local model servers.
  - **Limitations:**
    - The dashboard runs on Linux; monitored hosts may use other operating systems.
    - Remote monitoring needs SSH access; review authentication before exposing the dashboard.

</details>

<a id="applications"></a>

### Applications and model management

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-audiosmith"></a>[AudioSmith](https://github.com/hehehai/AudioSmith) | macOS voice studio that runs text to speech, voice cloning, audiobooks, dubbing and transcription on the Mac's GPU with MLX, with a local OpenAI-compatible API and MCP server. | Local | macOS | Apple Silicon | [AGPL-3.0-only](https://raw.githubusercontent.com/hehehai/AudioSmith/4e52f9102efa57b03feadbfb1bf7ce4937835884/LICENSE) | 2026-11-23; [JSON](data/projects/audiosmith.json) |
| <a id="project-contemplative-agent"></a>[Contemplative Agent](https://github.com/shimo4228/contemplative-agent) | Run an autonomous agent on a local LLM through Ollama that posts on Moltbook, logs every action, and stages changes to its own prompts for a person to adopt or reject. | Client | macOS | Apple Silicon | [MIT](https://raw.githubusercontent.com/shimo4228/contemplative-agent/620728552019f8be5ae9cb843400592ce5cde12d/LICENSE) | 2026-11-25; [JSON](data/projects/contemplative-agent.json) |
| <a id="project-live-translator"></a>[Live Translator](https://github.com/umutcetinkaya/live-translator) | Mac menu bar app that shows live translated subtitles for any system audio, translating on-device with TranslateGemma through MLX and optionally reading them aloud. | Local | macOS | Apple Silicon | [MIT](https://raw.githubusercontent.com/umutcetinkaya/live-translator/2708f8dd81f014fa811e4d98abdbf863efed2356/LICENSE) | 2026-11-21; [JSON](data/projects/live-translator.json) |
| <a id="project-off-grid-ai"></a>[Off Grid AI](https://github.com/off-grid-ai/OGAD) | Desktop app for local chat with text and vision models, image generation, speech-to-text and text-to-speech, plus a local OpenAI-compatible API. | Local | macOS, Windows, Linux | Apple Silicon, CPU | [AGPL-3.0-only](https://raw.githubusercontent.com/off-grid-ai/OGAD/312b8f45ef6afdd2bff3f7be130b4d0a23124bc8/LICENSE) | 2026-11-25; [JSON](data/projects/off-grid-ai.json) |
| <a id="project-threadshelf"></a>[ThreadShelf](https://github.com/ChrystianSchutz/ThreadShelf) | Index ChatGPT, Claude, Google AI Studio, OpenRouter, LM Studio and Grok exports locally for semantic and exact search, then continue old threads with local GGUF models. | Local | Linux, macOS, Windows | CPU | [MIT](https://raw.githubusercontent.com/ChrystianSchutz/ThreadShelf/f13b721561305c3b040dc701ce86553ec36c4447/LICENSE) | 2026-10-28; [JSON](data/projects/threadshelf.json) |
| <a id="project-voxtmini"></a>[VoxtMini](https://github.com/hehehai/VoxtMini) | macOS voice input: press a shortcut in any app, speak, and local Qwen3-ASR models on MLX (Whisper experimental) type, translate or rewrite the text at your cursor. | Local | macOS | Apple Silicon | [Apache-2.0](https://raw.githubusercontent.com/hehehai/VoxtMini/50cb2cc85169aea88032185db2917e91e3d04bdd/LICENSE) | 2026-11-26; [JSON](data/projects/voxtmini.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **AudioSmith**, reviewed 2026-11-25; last commit 2026-11-23; [record](data/projects/audiosmith.json)
  - **Compatibility:**
    - Runs Qwen3-TTS, Kokoro, Chatterbox, VoxCPM2, Qwen3-ASR, Whisper and other models with MLX on Apple silicon, without Python.
    - Serves an OpenAI-compatible speech and transcription API on 127.0.0.1:3901/v1 and an MCP server over HTTP and stdio.
  - **Limitations:**
    - Needs macOS 15 or later on Apple silicon; 8 GB of memory runs the Fast pack and 24 GB the Quality pack, with 1.3 to 17 GB of model downloads.
    - Beta software.
    - Model weights keep their own licences; OmniVoice is CC BY-NC 4.0 (non-commercial) and the app asks before downloading it.
    - Generated audio carries an AudioSeal watermark by default; the optional phone agent uses the user's own Twilio account.
    - Microphone and Accessibility permissions are asked only for recording and dictation. Official builds check actnow.dev once a day for software updates and, when the user downloads them, fetch ffmpeg and yt-dlp from github.com or mirror.actnow.dev; feedback is sent to actnow.dev only when the user sends it.
    - Official builds add dictation sounds from a private library that is not under the AGPL; builds from source use system sounds instead.

- **Contemplative Agent**, reviewed 2026-10-17; last commit 2026-11-25; [record](data/projects/contemplative-agent.json)
  - **Compatibility:** Ollama on localhost for generation (Gemma 4 E4B by default, or another local chat model) and embeddings (nomic-embed-text).
  - **Limitations:**
    - Needs a separately installed Ollama and about 10 GB of disk for the models; the documented tested setup is an Apple Silicon Mac with 16 GB of memory.
    - Posting is public and needs a Moltbook account; the owner verifies an email address and an X account (as of October 2026). A local two-agent dialogue runs without an account.
    - Posts wait for confirmation by default, but scheduled sessions run with --auto and post without asking. The agent talks only to moltbook.com and to Ollama on localhost.
    - A long-running research experiment, not a productivity tool; changes it proposes to its constitution, identity, and skills take effect only after a person adopts them.

- **Live Translator**, reviewed 2026-11-21; last commit 2026-11-21; [record](data/projects/live-translator.json)
  - **Compatibility:**
    - Runs TranslateGemma 4B (4-bit or 8-bit, chosen by memory) or an opt-in 12B 4-bit model through mlx-lm; models download from Hugging Face on first use.
    - Captures system audio with ScreenCaptureKit and transcribes it with Apple speech recognition; speech output uses the built-in macOS voices or Piper.
    - OpenAI, Gemini and Anthropic providers are optional and need the user's own API key.
  - **Limitations:**
    - The free on-device mode needs Apple Silicon and macOS 14 or newer; Intel Macs need a cloud API key.
    - Apple speech recognition runs on-device only for languages whose dictation model is installed; other languages use Apple's servers.
    - The first run downloads 2.2 to 6.7 GB of model weights, which follow the Gemma Terms of Use.
    - Needs the Screen and System Audio Recording permission.

- **Off Grid AI**, reviewed 2026-11-18; last commit 2026-11-25; [record](data/projects/off-grid-ai.json)
  - **Compatibility:**
    - Runs GGUF models from a built-in catalog or Hugging Face search through bundled llama.cpp, image models through stable-diffusion.cpp, transcription through whisper.cpp and speech through Kokoro.
    - Serves chat, vision, images, transcription, speech and embeddings on an OpenAI-compatible API at `http://127.0.0.1:7878/v1` with no key by default, and can run as a headless gateway without the UI.
    - Adds Model Context Protocol servers (no auth, token or OAuth) as tools inside chat.
  - **Limitations:**
    - Release builds cover macOS on Apple Silicon, Windows x64 and Linux x64 (Ubuntu 24.04 or newer).
    - Model downloads come from Hugging Face; the app checks for signed updates. Anonymous usage data and crash reports are sent only if the user turns them on.
    - The gateway listens on all IPv4 interfaces. API-key authentication is optional and off by default; reachable network peers can use model routes unless authentication is enabled.
    - An optional paid Pro layer (screen memory, meetings, dictation, clipboard) lives in a separate private package; the Linux build does not include it.

- **ThreadShelf**, reviewed 2026-11-08; last commit 2026-10-28; [record](data/projects/threadshelf.json)
  - **Compatibility:**
    - Runs GGUF models through a managed, loopback-only llama.cpp llama-server, with guided setup of an official llama.cpp build.
    - Serves its GGUF models over OpenAI- and Anthropic-compatible endpoints at /v1 (chat/completions, completions, responses, messages).
    - Exposes archive search and full-thread reading to MCP clients through a stdio MCP server.
  - **Limitations:**
    - Single-user application: the HTTP API has no accounts or authentication and should stay on loopback unless deliberately exposed on a trusted network.
    - The local embedding model downloads once on first indexing; llama.cpp builds come from GitHub Releases and GGUF models from Hugging Face only when the user asks.
    - Optional OpenRouter generation is off-device: it sends the selected conversation history and prompt to OpenRouter and the routed provider.
    - Google AI Studio, OpenRouter, LM Studio and Grok exports use undocumented formats that can change without notice.
    - Requires Node.js 20.19 or newer; installed through npm (npx threadshelf).

- **VoxtMini**, reviewed 2026-11-25; last commit 2026-11-26; [record](data/projects/voxtmini.json)
  - **Compatibility:**
    - Speech runs locally with Qwen3-ASR on MLX, with Whisper (experimental: no live text, not yet run on a Mac with VoxtMini) or with Apple Speech; clean-up, translation and rewriting use local language models such as Qwen3.5 and Hy-MT2.
    - A remote service (OpenAI, Gemini, Anthropic, DeepSeek and others) or Ollama and LM Studio on the same Mac can be chosen per feature instead of the local default.
  - **Limitations:**
    - Needs macOS 15 or later on Apple silicon; 16 GB of memory is recommended for the recommended models.
    - Beta software; models download on first use from Hugging Face. Whisper is experimental, and Apple Speech and Apple Intelligence have not yet been checked on real hardware.
    - Needs the Microphone permission, and Accessibility to type into other apps.
    - No account and no analytics. Installed builds check actnow.dev once a day for updates (/updates/voxtmini) and poll actnow.dev/api/voxtmini/notifications at launch and every six hours for announcements, sending only the app language and version (VOXTMINI\_ANNOUNCEMENTS\_URL="" turns this off); feedback and diagnostics are sent to actnow.dev only when the user sends them from the feedback window.
    - Official builds bundle React Bits Sound Lab cue sounds (MIT + Commons Clause v1.0, from a private library, not under Apache-2.0); builds from source play macOS system sounds instead.

</details>

<a id="mcp"></a>

### MCP servers

| Project | Summary | Mode | Platforms | Hardware | License | Activity |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="project-clickhouse-loom"></a>[ClickHouse Loom](https://github.com/ClickHouse/loom) | Self-hosted MCP server for shared agent memory, cited document retrieval and code intelligence, with local embedding and LLM options. | Client | Not recorded | Not recorded | [Apache-2.0](https://raw.githubusercontent.com/ClickHouse/loom/06544c04c9466a8d9f9c7c40f27fa30063f55792/LICENSE) | 2026-11-26; [JSON](data/projects/clickhouse-loom.json) |

<details>
<summary>Compatibility, limitations, and review notes</summary>

- **ClickHouse Loom**, reviewed 2026-11-26; last commit 2026-11-26; [record](data/projects/clickhouse-loom.json)
  - **Compatibility:**
    - MCP over Streamable HTTP (plus mcp-remote bridge for stdio-only clients).
    - LLM jobs on Ollama, llama.cpp llama-server, or other OpenAI chat-completions endpoints via LOOM\_LLM\_PROVIDER=local, alongside the released image's bundled CPU embedder.
    - Claude Code and Codex plugins, plus MCP setup helpers for Cursor, VS Code, Cline, Windsurf, Zed, Gemini CLI and OpenCode.
  - **Limitations:**
    - Released as v1.3.0 (evidence pinned to main at commit 06544c04). This entry has not qualified a local-model runtime or any OS or hardware target; upstream notes that prompts and thresholds are tuned on hosted models and no published benchmark covers a local model.
    - Self-hosted deployment needs Docker with Compose (WSL 2 on Windows) or a Kubernetes cluster via the Helm chart; platform and hardware tags are omitted because physical target tests are not established for this entry.
    - The released Docker image carries a local bge-small CPU embedder and defaults to a fake-echo-1 placeholder LLM unless the interactive installer detects Ollama or LOOM\_LOCAL\_MODELS=ollama is set. A source checkout defaults to fake embedding and LLM providers.
    - Local LLM jobs require a separately installed Ollama or llama.cpp server with a large context window (upstream recommends OLLAMA\_CONTEXT\_LENGTH=32768 for extraction). The local preset disables the capture verifier, conflict resolver and entity extraction to protect small local models.
    - Local providers do not guarantee offline operation or private client behavior. Hosted provider overrides, independently configured coding clients and optional ClickStack OTLP or Langfuse trace exports can send processed data elsewhere.

</details>

### Open categories

These categories do not have entries yet. [Suggest a project](CONTRIBUTING.md).

- <a id="clustering"></a>**Clustering and interconnects**
- <a id="systems"></a>**Systems**
- <a id="skills"></a>**Agent skills and extensions**

<!-- catalog:end -->

## How this list works

The editable source of truth is one JSON file per project in
[`data/projects`](data/projects), paired with [`data/taxonomy.json`](data/taxonomy.json)
and repository observations from [`data/health.json`](data/health.json).
Running `python3 scripts/catalog.py render` generates both the README catalog
above and the single-file machine-readable index
[`data/catalog.json`](data/catalog.json) for AI agents and scripts. No accounts,
submission fees, star-count thresholds, or paid placement. Self-submissions are welcome.

Listings describe what a tool does and where it fits. They are not rankings or
endorsements. Preview projects can be useful; their limitations should be visible.
The starting collection is Spark-heavy, and submissions for other hardware are welcome.

The scripts require Python 3.11 or newer and have no third-party dependencies:

```sh
python3 scripts/catalog.py validate
python3 scripts/catalog.py render
python3 scripts/catalog.py check
python3 scripts/catalog.py verify
python3 scripts/catalog.py status
python3 -m unittest discover -s scripts -p 'test_*.py'
```

For offline hygiene checks or live GitHub compliance auditing during review, run
`python3 scripts/audit.py --offline` or `python3 scripts/audit.py`.

PR checks cover data validation, generated output (`README.md` and
`data/catalog.json`), spelling, Markdown, and local documentation links. Remote
links in changed project records and changelog fragments get an advisory check;
weekly checks cover all upstream links. See
[the contribution guide](CONTRIBUTING.md) for review criteria and local lint
commands.

A separate weekly [health workflow](.github/workflows/health.yml) opens or updates
a reviewable PR for repository observations (`data/health.json`,
`data/catalog.json`, and `README.md`). It does not change documentation review
dates or remove projects. Routine health refreshes can merge automatically after
the [health safety gate](docs/maintenance.md#automatic-merging-of-routine-refreshes)
and CI pass; flagged refreshes and project submissions need human review.
Contributors add fragments in `changelog.d/` for the [weekly changelog](CHANGELOG.md);
routine health snapshots are not new catalog entries or upstream release notes.

## License

The catalog, original documentation, and other original repository content are
dedicated to the public domain under [CC0-1.0](LICENSE), except for `scripts/` and
`.github/workflows/`, which use the [MIT license](scripts/LICENSE).

Listed projects, their dependencies, and model weights retain their own licenses.
Every entry declares a non-deprecated OSI-approved SPDX license identifier backed
by the upstream top-level license file; it does not cover every bundled dependency
or model. Confirm upstream terms before reuse.
