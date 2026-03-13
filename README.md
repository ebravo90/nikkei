 nikkai
AI automation and task orchestration
<div align="center">
  <img src="https://img.icons8.com/nolan/256/processor.png" alt="Nikkei OS Logo" width="120">
  <h1>Project Nikkei</h1>
  <p><b>Local Autonomous Agent OS</b></p>
  <p><i>A lightweight, zero-trust autonomous agent operating system designed for secure, headless execution environments.</i></p>
</div>

---

Project Nikkei bridges the gap between powerful Large Language Models and grounded, local system execution. It provides a robust framework for agentic workflows, complex orchestration, and reliable system administration. 

Through its unique biological architecture and strict security paradigms, Nikkei allows you to deploy self-healing, locally executed agents that can interact with the host system safely, even in hostile or disconnected network conditions. 

## 🧬 Core Architecture (The Anatomy)

Nikkei is built upon a component-driven pattern of "Composition over Inheritance," adopting a biological naming convention to represent the varying degrees of abstraction and autonomy within the agent layer.

* 🧠 **Neurons (Orchestrators):** Complex, stateful agents. Neurons manage multi-step workflows, long-running processes, multi-agent routing, and Software Development Life Cycle (SDLC) logic. They maintain context and drive the high-level objectives.
* 🐙 **Tentacles (Executors):** The muscle. These are atomic, stateless, system-level execution functions. A Tentacle represents a physical action taken upon the host system or network (e.g., executing a bash command, modifying a file, or starting a container).
* 🧲 **Suckers (Extractors):** The suction wrappers. A Sucker is an encapsulated, grounded data extraction primitive that powers a Tentacle. Utilizing Live Web Search and function calling, Suckers pull verified, real-time data into the execution loop before the Tentacle strikes.

---

## 🛡️ Key Features

Nikkei prioritizes security and reliability above all else, ensuring that LLM hallucinations never result in catastrophic local system compromises.

* **Zero-Trust Security Engine:** Every action is verified. Actions requiring system access pass through an integrated **AST Scanner** and **SHA-256 Hashing engine**. Modified or unauthorized tentacles are immediately localized into Quarantine, requiring explicit cryptographic approval.
* **DaaQ (Drive-as-a-Queue):** True headless Peer-to-Peer communication. DaaQ leverages ubiquitous cloud storage (Google Drive, Dropbox) as secure, offline message queues. This bypasses traditional firewalls and allows remote agent orchestration without exposing local ports.
* **Dual-Tier LLM Gateway:** Optimized routing.
  * *Tier 1 (Gemini 2.5 Flash):* Fast, efficient function-calling router for tool selection.
  * *Tier 2 (Gemini 2.5 Pro):* Complex reasoning and live Google Search Grounding for high-fidelity data extraction.
* **Developer SDET Sandbox:** The `nikkei test` CLI acts as an isolated Developer Experience (DX) environment. Test and validate Tentacle schemas and execution logic offline, cost-free, without invoking the primary orchestrator.

---

## � Configuration & Setup Guides

### 1. 📱 Telegram Bot Setup (The Neurological Link)
Project Nikkei uses Telegram as its encrypted communication terminal. To establish the host connection, you must provision a private Bot:

1. **Open Telegram** and search for **`@BotFather`** (ensure it has the official blue verification checkmark ✅).
2. Start the chat and send the **`/newbot`** command.
3. Provide a display name (e.g., `Nikkei Core`) and a unique programmatic username ending in "bot" (e.g., `Nikkei_Host_01_bot`).
4. Upon creation, @BotFather will grant you a **Telegram Bot Token** (e.g., `1234567890:AAH_xyz123abc456...`). **Guard this token fiercely.** It is the cryptographic key to your machine.
5. In the local **Nikkei OS Settings** Dashboard, paste this token. Click **"Auto-Detect My ID"** and send any message to your new bot to complete the neurological handshake.

### 2. 🛡️ Zero-Trust RCE (The Kill Switch & Quarantine)
Nikkei operates under a strict Zero-Trust execution paradigm to prevent rogue LLM hallucinations or malicious injections.

* **The AST Sandbox:** Whenever a new Tentacle is created or modified, the internal AST Scanner hashes its signature and intercepts execution. Untrusted code is immediately dumped into the Quarantine layer.
* **Manual Verification:** Before any sandboxed code can execute upon your system, you must physically authorize it. 
* **Approval Methods:** You can clear the Quarantine manifest visually via the local UI Dashboard, or directly from the terminal using the physical presence CLI command: `nikkei quarantine approve <tentacle_name.py>`. Without clearance, the execution pipeline remains severed.

### 3. ☁️ DAAQ (Drive-as-a-Queue) Setup
For true headless peering, Nikkei utilizes **DAAQ**—leveraging Google Drive's OAuth2 API as an offline, firewall-bypassing message queue.

1. **Provision Credentials:** Log into the [Google Cloud Console](https://console.cloud.google.com/) and create a new project with the Google Drive API enabled.
2. **Download Secret:** Generate an OAuth 2.0 Client ID for a Desktop Application. Download the resulting JSON file and rename it strictly to `client_secrets.json`.
3. **Implant the Secret:** Place `client_secrets.json` directly into the root directory of your Nikkei repository.
4. **Authorize the Connection:** Boot the Nikkei UI Dashboard and navigate to the DAAQ settings. Initialize the OAuth flow to grant the Agent offline read/write access. Once linked, the local Node can bi-directionally sync telemetry and directives without exposing any network ports.

### 4. 🛰️ Fleet Management Radar
The Fleet Radar provides a real-time DaaQ (Drive-as-a-Queue) telemetry heartbeat to monitor all your distributed Nikkei nodes.
* **Heartbeat:** Every 3 minutes, each active node uploads a lightweight JSON payload (`[NODE_ID]_heartbeat.json`) to the secure Google Drive folder.
* **Radar UI:** The central Web Dashboard aggregates these heartbeats natively. Nodes that have checked in within the last 5 minutes are displayed as `🟢 Online`. If a node misses its check-in interval, its status gracefully degrades to `🔴 Offline`.
* **Zero-Port Telemetry:** Because state is synchronized via Google's REST API, you can monitor an entire global fleet of physical machines without exposing a single inbound network port.

---

## 🚀 Quick Start & Installation

Project Nikkei is designed for rapid deployment as a global system alias.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/project-nikkei.git
   cd project-nikkei
   ```

2. **Install globally (Development Mode):**
   ```bash
   pip install -e .
   ```
   *This links the source directory to your Python environment and exposes the `nikkei` CLI globally. It installs all modern dependencies including `google-genai` and `watchdog`.*

3. **Boot the OS:**
   ```bash
   nikkei run
   ```
   *(Or just `python main.py`)*

---

## 💻 CLI Usage

The headless Developer Harness provides complete control over the Nikkei OS without requiring a Graphical User Interface. 

**Vitals & Telemetry**
View the current status of the Agent, Chat Adapters, and local Nodes:
```bash
nikkei status
```

**Zero-Trust Security Management**
Manage the AST File Quarantine directly from the terminal. 
*List quarantined and approved tools:*
```bash
nikkei quarantine list
```
*Approve a secure tool for execution (Warning: Requires a forced 5-second physical presence delay):*
```bash
nikkei quarantine approve <filename.py>
```

**SDET Sandbox Testing**
Validate an atomic tool using mocked JSON arguments, bypassing the LLM Gateway:
```bash
nikkei test my_tentacle --mock-args '{"target": "localhost"}'
```

---

*Project Nikkei — Advanced Agentic Control Patterns.*