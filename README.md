# ELYos

One ecosystem. Multiple systems. One at a time.

ELYos is a modular operating system ecosystem.

---

## Overview

**ELYos** is designed to eliminate the friction between operating systems without compromising on performance. Rather than relying on heavyweight virtualization, nested windows, or fragile dual-boot setups, ELYos introduces an independent, protected management core (**ELYos Core**) that orchestrates bare-metal execution of specialized operating system environments (**ELYos System Modules**).

With ELYos, each operating system runs directly on bare-metal hardware with 100% native performance, while your personal documents, compatible credentials, clipboard history, and application libraries remain unified across reboots in **ELYos User Data**.

---

## Core Philosophy

ELYos is founded upon **10 non-negotiable principles** detailed in our [Manifesto](docs/MANIFESTO.md). The foundational rule governing the entire ecosystem is:

> **Only one ELYos System Module may be active at any given time.**  
> Switching between operating systems requires rebooting the machine. Simultaneous execution or window embedding across modules is strictly prohibited.

---

## Architectural Triad

```text
+-------------------------------------------------------------------------+
|                               ELYos Core                                |
|    (Boot supervisor, Rust engine, Qt 6 + QML UI, Security & Recovery)   |
+-------------------------------------------------------------------------+
        |                                                 |
        v (Bare-metal switch via reboot)                  v
+-------------------------------+         +-------------------------------+
|   Active System Module        |         |    Inactive System Modules    |
|   (e.g., ArchELYos)           |         | (Windows Module, Ubuntu, etc) |
+-------------------------------+         +-------------------------------+
        |                                                 |
        +-----------------------+-------------------------+
                                |
                                v
+-------------------------------------------------------------------------+
|                            ELYos User Data                              |
|   (Shared Documents, Configs, Credentials, Clipboard Buffer, Trash)     |
+-------------------------------------------------------------------------+
|                       Shared Component Store                            |
|             (Multi-version dependency store, Zstandard)                 |
+-------------------------------------------------------------------------+
```

1. **ELYos Core:**  
   The sovereign foundation of the ecosystem. Boots first via a custom systemd-boot wrapper, renders the graphical and text module selector, enforces cryptographic integrity, manages backups and atomic updates, and provides recovery shells. Written in **Rust** with a **Qt 6 + QML** user interface.
2. **ELYos System Modules (`.elyossysmod`):**  
   Complete, independent operating system distributions managed by Core.
   - **ArchELYos:** The initial official system module, based on Arch Linux and tuned for high-performance bare-metal gaming with Proton, Wine, Lutris, and graphics translation layers.
   - **Future Modules:** Windows Module (Windows 11 base with BYO-license), Ubuntu Module, and Apple hardware adaptations.
3. **ELYos Modules (`.elyosmod`):**  
   Modular extensions that expand the functionality of an active system module.

---

## Technology Stack

| Component | Technology |
|---|---|
| **Core Engine** | Rust |
| **User Interface** | Qt 6 + QML |
| **Automation & Tools** | Python 3.10+ |
| **Bootloader** | systemd-boot (with custom ELYos orchestration layer) |
| **Manifests & Config** | TOML |
| **Package Compression** | Zstandard (`zstd`) |
| **Versioning** | Semantic Versioning (SemVer) with `build_date` |
| **Virtualization & Testing** | QEMU |
| **First System Module** | Arch Linux (ArchELYos) |

---

## Repository Structure

```text
ELYos/
├── .github/                           # GitHub Actions CI/CD workflows, issue & PR templates
│   ├── workflows/                     # Automated quality gates (CI, manifest, structure)
│   ├── ISSUE_TEMPLATE/                # Standardized issue forms
│   ├── PULL_REQUEST_TEMPLATE.md       # Pull request checklist
│   └── CODEOWNERS                     # Repository maintainer definitions
│
├── README.md                          # Project introduction and overview
├── LICENSE                            # Software license
├── CONTRIBUTING.md                    # Guidelines for contributors and registry submissions
│
├── core/                              # ELYos Core source code (Rust, Qt 6 / QML)
├── system-modules/                    # Official ELYos System Modules (ArchELYos)
├── community-system-modules/          # Registry manifests for community System Modules
├── modules/                           # Official ELYos Modules
├── community-modules/                 # Registry manifests for community Modules
│
├── sdk/                               # ELYos SDK, development libraries, and compiler wrappers
├── tools/                             # Build scripts, packaging, and validation tools
│   ├── validate_manifests.py          # Manifest validation script
│   └── validate_structure.py          # Repository structure validation script
├── tests/                             # Integration tests, unit tests, and QEMU harnesses
│   ├── test_validate_manifests.py     # Manifest validator tests
│   └── test_validate_structure.py     # Structure validator tests
│
└── docs/                              # Architecture and design documentation
    ├── MANIFESTO.md                   # Project philosophy and 10 fundamental principles
    └── TECHNICAL_SPECIFICATION.md     # Full technical specification (v0.1)
```

---

## Official vs. Community Components

To preserve core stability and security:
- **Official Components** (`system-modules/`, `modules/`): Maintained directly in this repository by the core team.
- **Community Components** (`community-system-modules/`, `community-modules/`): **Never** store source code in this repository. Developers host their code in their own external repositories, submitting only standardized TOML manifests to the registry.

---

## Roadmap & MVP Scope (v0.1)

The immediate milestone is developing a functional ELYos Core running within a **QEMU virtual machine** capable of installing and launching **ArchELYos**:

- [ ] **Phase 1 — Preparation:** Repository structure, build pipelines, QEMU configuration.
- [ ] **Phase 2 — ELYos Core:** Boot supervisor, module selector, terminal, configuration system.
- [ ] **Phase 3 — ArchELYos:** Build first `.elyossysmod` package, automated installer, bare-metal/VM boot.
- [ ] **Phase 4 — Management & Recovery:** Fault detection (3 consecutive failed boots), atomic backups, recovery USB.
- [ ] **Phase 5 — Validation:** Virtual machine automated testing, hardware compatibility verification.

For full technical specifications, see [`docs/TECHNICAL_SPECIFICATION.md`](docs/TECHNICAL_SPECIFICATION.md).

---

## Documentation Links

- **[Manifesto](docs/MANIFESTO.md):** Deep dive into the philosophy, motivation, and principles of ELYos.
- **[Technical Specification](docs/TECHNICAL_SPECIFICATION.md):** Comprehensive engineering architecture, storage partitioning, security, and protocols.
- **[Contributing Guide](CONTRIBUTING.md):** Information on development standards, PR workflow, and community module registration.

---

## License

This project is licensed under the terms described in [LICENSE](LICENSE).
