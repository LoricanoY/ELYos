# ELYos Technical Specification

> **Version:** 0.1 · Consolidated Technical Draft  
> **Date:** November 11, 2026  
> **Official Terminology:** `ELYos Core` · `ELYos System Modules` · `ELYos Modules`  
> **Slogan:** *One ecosystem. Multiple systems. One at a time.*

---

## 1. Document Control & Scope

This specification consolidates all architectural and engineering decisions established for the **ELYos** project. It delineates the broader vision for the complete ecosystem from the strictly required minimal viable product (**MVP v0.1**).

### Fundamental Principle
> **Only one ELYos System Module may be active at any time.**  
> Switching between modules requires rebooting the machine. Simultaneous execution or window embedding across modules is prohibited.

---

## 2. System Architecture

```text
+------------------------------------------------------------------------+
|                              ELYos Core                                |
|   (systemd-boot supervisor, Rust core engine, Qt 6 + QML GUI, CLI)     |
+------------------------------------------------------------------------+
        |                                                 |
        v (Bare-metal switch via reboot)                  v
+-------------------------------+         +------------------------------+
|  Active ELYos System Module   |         |    Inactive System Modules   |
|   (e.g., ArchELYos bare-metal)|         | (Windows Module, Ubuntu, etc)|
+-------------------------------+         +------------------------------+
        |                                                 |
        +-----------------------+-------------------------+
                                |
                                v
+------------------------------------------------------------------------+
|                          ELYos User Data                               |
| (Shared Files, Compatible Configs, Credentials, Clipboard, Trash, Libs)|
+------------------------------------------------------------------------+
|                     Shared Dependencies & Components                   |
|           (Multi-version central store, Zstandard compression)          |
+------------------------------------------------------------------------+
```

### 2.1. ELYos Core
ELYos Core is the initial component executed during startup. Its primary responsibilities include:
- Managing system bootstrap and rendering the ELYos System Modules selector.
- Managing module lifecycle (installation, updates, integrity verification, removal).
- Managing shared dependencies across modules.
- Enforcing cryptographic trust, managing security keys, and maintaining signed audit logs.
- Coordinating backups, automated health diagnostics, repairs, and bare-metal recovery.
- Providing user management tools: Graphical User Interface (Qt 6 + QML), terminal console, and emergency recovery shell.

### 2.2. ELYos System Modules
An ELYos System Module is a complete, independent operating system distribution managed by Core.
- **ArchELYos (First Official Module):** Based on Arch Linux, optimized for bare-metal performance and gaming. Integrates Wine, Proton, and Lutris, with native support for Vulkan, OpenGL, and DirectX translation layers.
- **Future System Modules:** Windows Module (initially based on Windows 11), Ubuntu Module, and specialized hardware adaptations (e.g., Apple Silicon/hardware).

### 2.3. ELYos Modules
Optional modular components that extend the capabilities of an ELYos System Module. Developers build modules using the official ELYos SDK and technical specifications.

---

## 3. Boot & Module Management

### 3.1. Boot Sequence
ELYos uses **systemd-boot** augmented with a custom ELYos orchestration layer:
1. System boots directly into **ELYos Core**.
2. Core verifies the cryptographic integrity of all protected ecosystem components.
3. The **Module Selector** interface is displayed.
4. The user selects a target module (or the configured default boots on timeout).
5. The chosen module boots with direct, native hardware control.

- **Selector Modes:** Card-based visual interface (graphical) with automatic text-mode fallback for headless or legacy environments.
- **Configuration:** Default module selection, timeout duration, and auto-boot rules.
- **Recovery Shortcut:** Holding the key combination **`E + L + Y`** during system startup forces direct entry into the Core recovery interface.

### 3.2. Boot Failure & Diagnostic Handling
- After **three (3) consecutive failed boot attempts**, Core flags the module as `Problematic`.
- Core presents an automated diagnostic menu offering options to:
  1. Attempt automated repair.
  2. Reinstall the module.
  3. Inspect crash and boot logs.
  4. Override and force normal boot.
- Warnings remain active until the module achieves a successful, verified boot.
- Every ELYos System Module must provide an emergency Safe Mode environment.

---

## 4. Storage & Partition Layout

```text
Storage Layout
├── [ELYos Core Partition]           -> Immutable/protected bootloader, recovery & Core runtime
├── [ELYos System Modules Space]     -> Partitioned/subvolume allocations for System Modules
├── [ELYos User Data Partition]      -> Shared user documents, configs, credentials, trash
├── [Shared Component Store]         -> Central multi-version dependency & library repository
├── [Windows Module Data Space]      -> Dedicated volume for Windows installation & storage
└── [External Recovery Medium]       -> Bootable official USB recovery environment
```

### 4.1. Shared User Data (`ELYos User Data`)
Accessible by ELYos Core and active System Modules, enabling seamless continuity without concurrent OS execution:
- Personal files and user libraries.
- Compatible application configuration profiles.
- Compatible authentication credentials and keyrings.
- Persistent cross-reboot clipboard buffer.
- Compatible application data and game libraries.
- Unified ecosystem trash bin.

### 4.2. External Storage Policy
- External drives are **not mounted automatically** (prevents unexpected filesystem race conditions or security compromises).
- Partition management, disk migration, and cloning tools are integrated into Core.
- Native BitLocker volume unlocking is supported for cross-platform access.
- SMART diagnostic monitoring and proactive drive health warnings are managed by Core.

---

## 5. Inter-Component Communication (Hybrid API)

Communication between Core and active System Modules employs a hybrid architecture:

| Channel | Purpose |
|---|---|
| **Local Real-Time Services** | Real-time IPC for active queries, status broadcasts, and immediate events |
| **File-Based Channels** | Configuration files, structured audit logs, and asynchronous request queues |
| **Common Shared Protocol** | Standardized primitives implemented across all module ecosystems |
| **Module-Specific APIs** | Specialized interfaces catering to unique capabilities of individual modules |

### 5.1. Permissions & Boundaries
- Core automatically processes authorized requests from known System Modules.
- Suspicious or policy-violating operations are immediately quarantined, triggering user authorization prompts.
- **Strict Inviolability:** Under no circumstances may an active module modify, overwrite, delete, or hook into ELYos Core runtime files.
- Modules interact strictly via public API endpoints; internal implementation details of Core remain inaccessible.
- System Modules can depend on shared services provided by Core, but never on the internal components of another System Module.

---

## 6. Centralized Dependency Management

### 6.1. Central Dependency Store
Core maintains a centralized, deduplicated dependency repository:
- **Multi-Version Coexistence:** Multiple versions of a single shared dependency may reside concurrently in the store. Each module binds specifically to its validated target version.
- **Reference Tracking:** Core maintains an active dependency graph to prevent premature deletion or collisions.

### 6.2. Dependency Updates
1. Core checks the dependency graph before modifying any shared component.
2. If another module requires an older version, that version is preserved side-by-side with the updated package.
3. If no other module references the old version, it may be upgraded in place.
4. If a conflict prevents coexistence, Core halts the operation and surfaces actionable conflict details.

### 6.3. Deprecation & Cleanup
- Unreferenced dependencies are marked as orphaned.
- A **30-day default grace period** (user-configurable) prevents churn.
- If a dependency is re-requested during the grace period, its orphaned flag is cleared.
- Following the expiration of the retention window, orphaned packages are automatically purged.

### 6.4. Dependency Installation Flow
1. Verify whether the dependency exists in the local store.
2. If missing, retrieve package from verified upstream endpoints.
3. Validate digital signatures and SHA-256 integrity hashes.
4. Trusted sources proceed automatically; untrusted or third-party sources require explicit user consent.

---

## 7. Package Formats & Manifest Schema

### 7.1. Package Extensions
- **ELYos System Module:** `.elyossysmod`
- **ELYos Module:** `.elyosmod`
- *Application package format:* Reserved for future finalization.

### 7.2. Package Manifest Specification
Package metadata must be defined in **TOML** using reverse-domain hierarchical identifiers (`org.elyos.arch`, `com.developer.module`).

```toml
[module]
id = "org.elyos.arch"
name = "ArchELYos"
description = "Official gaming and performance system module based on Arch Linux"
version = "0.1.0"
build_date = "2026-11-11"

[compatibility]
minimum_core_version = "0.1.0"
supported_architectures = ["x86_64"]

[dependencies]
required_packages = []
shared_services = ["elyos-ipc-bridge"]

[metadata]
developer = "ELYos Team"
license = "GPL-3.0"
status = "official"
signature_algorithm = "ed25519"
```

### 7.3. Versioning & Compression
- **Semantic Versioning (SemVer):** Standard `MAJOR.MINOR.PATCH` with `build_date` metadata.
- **Compression Algorithm:** **Zstandard (`zstd`)** is the default algorithm across all packages and backups.
- **Directory Structure:** Hybrid layout featuring mandatory standard root metadata coupled with developer freedom for internal layout.

---

## 8. Updates, Backups & Rollback

### 8.1. System Module Lifecycle
- Developers publish their own updates independently.
- Version checks can run automatically; installation defaults to manual confirmation with optional opt-in automation per module.
- Core validates compatibility against its own version before applying module upgrades.

### 8.2. Automated Backups
- Automatic snapshot creation prior to any module update (if enabled).
- Configurable periodic automated snapshots.
- Default retention of **three (3) snapshots** per module.
- Snapshots stored on the module's host drive and compressed with Zstandard.
- Verification of SHA-256 integrity hashes post-creation; corrupted snapshots quarantined.
- Restoration operations require explicit user approval.

### 8.3. ELYos Core Atomic Updates
- Core checks for updates on every boot from official distribution endpoints.
- Downloads run automatically; installation requires manual confirmation.
- **Atomic Staging Sequence:**
  1. Download update package.
  2. Unpack and verify integrity in an isolated staging location.
  3. Validate cryptographic signatures.
  4. Perform atomic swap to replace active Core only once verification completes.
- Critical security updates cannot be rolled back to earlier vulnerable releases.

### 8.4. Release Channels
| Channel | Target Audience | Access Policy |
|---|---|---|
| **Stable** | General public distribution | Default channel |
| **Beta** | Community testers | Voluntary opt-in |
| **Developer** | Core team & certified contributors | Authorized access |

---

## 9. Security, Trust & Cryptography

### 9.1. Core Protection & Key Management
- Cryptographic verification of boot components and binary signatures.
- Startup halts if unauthorized modifications or signature mismatches are detected.
- Bare-metal restoration facilitated by the official ELYos USB recovery image.
- Three tiers of keys: Official ELYos Keys, Recovery Keys, and User Keys.
- Keys manageable via Core GUI and terminal; supports password-encrypted export/import.

### 9.2. Private Key & Credential Storage
- Primary protection backed by hardware **TPM 2.0** when present.
- Software fallback utilizing master password key-derivation encryption.
- Keys unlocked exclusively in volatile memory for the duration of an active transaction.
- Progressive time-lockouts enforced following repeated failed password attempts.

### 9.3. Cryptographic Audit Logs
- Records timestamp, public key fingerprint, operation identifier, execution status, and error traces.
- Sensitive credentials, passwords, and private keys are never logged.
- Audit records are **cryptographically hash-chained** and signed by Core.
- Logs preserved indefinitely by default (configurable retention), queryable via Core terminal or read-only external API. Supports JSON export.

---

## 10. Community Registry Architecture

To protect ecosystem security and integrity, community components follow a strict registry model:

1. **Decentralized Storage:** Community module source code and binaries remain hosted on developers' external repositories (e.g., GitHub, GitLab). The ELYos repository only hosts metadata manifests.
2. **Registry Manifests:** Located in `community-system-modules/` and `community-modules/` in TOML format.
3. **Verification Tiers:**
   - `Official`: Maintained and verified directly by the ELYos project.
   - `Community-Reviewed`: Audited and endorsed by community reviewers.
   - `Unverified`: Community submission pending review.
   - `Problematic`: Modules with critical bugs or policy violations.
4. **Automated `Problematic` Threshold:** A module is flagged automatically when verified issue reports exceed **25% of unique installations** (e.g., >25 complaints per 100 installations). Removal of this flag requires formal developer patch submission, community validation, and manual review.

---

## 11. Application Layer & Cross-Module Integration

### 11.1. Unified Application Management
- Centralized Application Manager featuring a Qt 6 graphical store and terminal package manager.
- Supports official, community, and verified third-party repositories.
- **Flatpak** represents the baseline universal application runtime format.

### 11.2. Cross-Module Redirection
- Applications and games installed in inactive modules appear inside the active module's central application library.
- Attempting to launch an application associated with another system module prompts the user to **reboot and switch modules** seamlessly.

---

## 12. Windows Module Architecture

- Base: Windows 11.
- License: Bring-Your-Own-License (user provides valid Microsoft Windows license).
- Installation: Core coordinates the download of official ISO/WIM binaries directly from Microsoft servers.
- Storage: Dynamic VHDX or dedicated NTFS partition constrained by a user-configured storage quota.
- Management: Windows Update supervised by Core; Windows Defender security policies respected.
- Ecosystem Integration: Access to `ELYos User Data` via transparent filesystem drivers; Windows applications registered in ArchELYos central launcher.

---

## 13. Module Development & SDK

- **Philosophy:** Inspired by *Linux From Scratch* (LFS). The ELYos SDK prioritizes architectural mastery over rigid, black-box scaffolds.
- **SDK Deliverables:** Core libraries, build scripts, package packaging tools (`.elyossysmod`), manifest validators, and debugging utilities.
- **Test Environments:**
  1. QEMU virtualized test harnesses.
  2. Bare-metal target hardware validation.
  3. Integrated Core simulation harness (scheduled post-MVP).

---

## 14. Official Technology Stack

| Domain | Technology / Decision |
|---|---|
| **First System Module** | Arch Linux (ArchELYos) |
| **Core Primary Language** | Rust |
| **Automation & Tooling** | Python |
| **Graphical Interface** | Qt 6 + QML |
| **Inter-Process Communication** | Hybrid API (Unix sockets / local IPC + file queues) |
| **Manifest Format** | TOML |
| **Compression** | Zstandard (`zstd`) |
| **Versioning Scheme** | Semantic Versioning (SemVer) |
| **Boot Engine** | systemd-boot (with custom ELYos wrapper) |
| **Host Development Environment** | Windows 11 + WSL2 |
| **Target IDE** | Visual Studio Code |
| **Virtualization Platform** | QEMU |
| **Version Control** | Git & GitHub |

---

## 15. MVP Scope & Delivery Roadmap

### 15.1. Mandatory MVP Requirements (v0.1)
1. Functional ELYos Core execution in QEMU virtual machine.
2. Bootstrap management using systemd-boot.
3. Functional ELYos System Modules selector.
4. Automated installation of ArchELYos package.
5. Successful bare-metal/VM boot into ArchELYos.
6. Reboot pathway returning cleanly to Core.
7. Diagnostic detection of boot failures (3 consecutive faults).
8. Basic repair and reinstallation pipeline.
9. Initial version control tracking for modules.
10. Validated `.elyossysmod` archive format.
11. Basic Core-to-ArchELYos communication bridge.
12. Preliminary shared storage mounting (`ELYos User Data`).

### 15.2. Phased Development Plan
- **Phase 1 — Preparation:** Repository structure, Rust/Python/Qt tooling setup, QEMU runner scripts.
- **Phase 2 — ELYos Core:** Bootloader layer, module selector UI/CLI, system configuration, module manager.
- **Phase 3 — ArchELYos:** Build first `.elyossysmod` package, implement installer, boot test, basic shared storage.
- **Phase 4 — Management & Recovery:** Fault detection, automated snapshots, atomic updates, recovery USB builder.
- **Phase 5 — Validation:** QEMU test automation, bare-metal hardware validation, stress testing, documentation.

---

## 16. Open Architectural Decisions Needing Clarification

While architectural foundations are established, the following low-level engineering determinations require final technical definition during development:
1. **Shared Filesystem Choice:** Optimal filesystem for `ELYos User Data` partition accessible natively across Linux and Windows without corruption (e.g., exFAT vs Btrfs with WinBtrfs driver vs NTFS).
2. **IPC Protocol Wire Format:** Exact IPC protocol implementation for real-time Core-to-Module communication (e.g., custom Varlink / gRPC / Protobuf over Unix domain sockets).
3. **Hardware Root-of-Trust:** Specific UEFI Secure Boot key enrollment and enrollment tooling for Core verification on production bare metal.
4. **Exact TOML Schema Validation:** Strict formal JSON/TOML Schema definitions for `.elyossysmod` and `.elyosmod` metadata validation.
