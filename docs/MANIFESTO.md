# The ELYos Manifesto

> *"One ecosystem. Multiple systems. One at a time."*

---

## 1. The Vision

The contemporary computing landscape forces users and developers into an artificial compromise:

- **Traditional Dual-Booting** requires juggling disconnected partitions, fragile bootloaders, and duplicated data stores. Switching environments feels like leaving one computer to boot another entirely different machine.
- **Heavy Virtualization and Emulation** introduce measurable performance overhead, input latency, battery drain, and complex hardware passthrough hurdles—severely limiting demanding workloads like gaming and low-level development.
- **Siloed Operating Systems** isolate user files, application libraries, configuration profiles, and credentials within their own walled gardens.

**ELYos** proposes a third path: **a modular operating system ecosystem**. 

In ELYos, specialized operating systems are treated as modular components (**ELYos System Modules**) governed by an independent, protected core supervisor (**ELYos Core**). You run directly on bare metal with 100% native hardware performance, while maintaining a shared foundation of user data, unified application access, and centralized recovery.

---

## 2. The 10 Fundamental Principles

The design, architecture, and evolution of ELYos are strictly bound to ten non-negotiable principles:

### I. Single Active System Module
> **Only one ELYos System Module may be active at any given time.**

Switching between operating systems requires rebooting the machine. ELYos does not allow simultaneous execution of two system modules, nor does it embed windows or processes of an inactive module inside the active one. Each system module receives dedicated, uncompromised access to bare-metal hardware.

### II. Independent and Protected Core
> **ELYos Core is the sovereign foundation of the ecosystem.**

ELYos Core executes as the first component at boot. It manages boot orchestration, module lifecycles, cryptographic trust, ecosystem configurations, and system recovery. Core operates independently of any specific operating system module and remains physically and logically isolated.

### III. Inviolability of Core
> **No module may modify, overwrite, delete, or alter ELYos Core.**

System modules and optional modules are completely prohibited from altering Core binaries, configurations, or boot logic. Core integrity is validated through hardware-rooted security, cryptographic signatures, and immutable partition boundaries.

### IV. Public API Boundary
> **Modules interact with Core exclusively through defined public APIs.**

Modules are granted access to Core services via standard public interfaces (real-time local IPC and file-based request queues). Modules can never access, manipulate, or rely on internal implementation details of Core.

### V. Cohesion Through Shared Data
> **Integration is achieved through unified data and services, never through concurrent execution.**

Shared user data (**ELYos User Data**) allows personal documents, compatible credentials, clipboard history, application libraries, and trash to persist across reboots and remain accessible to whichever system module is currently active.

### VI. Developer Freedom (The LFS Philosophy)
> **Developers retain full architectural freedom within their modules.**

Inspired by the philosophy of *Linux From Scratch*, ELYos provides an official SDK, compilation tools, validation harnesses, and technical specifications, rather than rigid, pre-packaged boilerplate. Developers are empowered to understand the internal architecture of their systems and build clean, purposeful modules.

### VII. Centralized Cryptographic Security
> **Security, verification, and integrity are centralized responsibilities of Core.**

Every module, update, and dependency must be cryptographically signed and verified against trusted roots. Audit logs are tamper-evident, hash-chained, and digitally signed by Core. Keys are protected via TPM or hardened master-key derivation with progressive rate-limiting against brute force.

### VIII. Compatibility-First Lifecycle
> **Dependency and version management must guarantee multi-version coexistence.**

Core maintains a central dependency repository supporting concurrent versions. An update required by one system module must never silently degrade, conflict with, or break another module's dependencies.

### IX. Absolute User Sovereignty
> **The user maintains final authority over installations, updates, and restorations.**

ELYos does not force opaque background changes. Critical updates require explicit consent, backups are created automatically prior to major operations, and users retain complete agency over recovery, rollbacks, and storage quotas.

### X. Modularity, Extensibility, and Community
> **ELYos is built from the ground up as a community-driven, modular ecosystem.**

Official components and community contributions are strictly separated. The community registry provides transparent metadata, decentralized repository tracking, and decentralized innovation without compromising core ecosystem stability.

---

## 3. Philosophy of Module Development

ELYos rejects unnecessary opacity. When a developer creates a module for ELYos—whether a performance-tuned Linux environment like **ArchELYos** or a future desktop module—they are encouraged to engage with the operating system at a structural level. 

By defining clear manifests, standardized package formats (`.elyossysmod` and `.elyosmod`), and explicit dependency contracts, the ELYos ecosystem fosters transparency, auditability, and long-term sustainability.

---

## 4. The Path Forward

The ultimate objective of ELYos is to make operating systems interchangeable lenses through which users interact with their hardware and data. Whether booting into a high-performance gaming environment, a streamlined development workstation, or a legacy productivity system, the user is always at home in **ELYos**.

*One ecosystem. Multiple systems. One at a time.*
