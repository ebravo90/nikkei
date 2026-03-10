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

## 📱 How to create the Telegram Bot (For Beginners)

Project Nikkei uses Telegram as its secure, encrypted communication terminal. To connect, you need to create your own private Bot. Follow these simple steps:

1. **Open Telegram** on your phone or computer.
2. In the search bar, search exactly for **`@BotFather`** (make sure it has the blue verification checkmark ✅).
3. Start a chat with him and press the **`Start`** button (or type `/start`).
4. Type the **`/newbot`** command and send it.
5. He will ask you for a name for your bot. Type something like `Nikkei My PC` or `Personal Assistant`.
6. Now he will ask you for a **"username"**. This must be unique and must end with the word "bot" (Example: `MyName_Nikkei_bot`).
7. Done! @BotFather will send you a long congratulatory message. In that message, you will see a red or highlighted text under "Use this token to access the HTTP API". 
   * That text looks similar to this: `1234567890:AAH_xyz123abc456def789`.
   * **COPY IT!** That is your **Telegram Bot Token**. Guard it as if it were a bank password.
8. Once you install Nikkei and open the **Nikkei OS Settings** Dashboard, paste that token in the corresponding field. Click on "Auto-Detect My ID" and send any message to your new bot on Telegram to complete the linking process. 

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
