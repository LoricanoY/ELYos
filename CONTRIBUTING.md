# Contributing to ELYos

Thank you for your interest in contributing to **ELYos**! We welcome developers, system architects, and open-source contributors from all backgrounds to help shape the modular operating system ecosystem.

Before contributing, please read our [Manifesto](docs/MANIFESTO.md) and [Technical Specification](docs/TECHNICAL_SPECIFICATION.md) to understand our architectural principles and technical decisions.

---

## 1. Architectural Guardrails

Every contribution to ELYos must adhere to our fundamental architectural rules:

1. **Single Active System Module:** ELYos is strictly non-concurrent. Never propose or implement features for running multiple system modules simultaneously or nesting inactive modules in windows.
2. **Core Inviolability:** ELYos Core is protected and immutable from the perspective of running modules. Modules may consume Core's public APIs, but cannot alter Core binaries, boot logic, or configurations.
3. **Component Clarity:** Preserve the strict separation between:
   - **ELYos Core:** The supervisor, bootloader manager, and security anchor.
   - **ELYos System Modules:** Full operating system distributions (e.g., ArchELYos).
   - **ELYos Modules:** Modular extensions for active system modules.
4. **Community Component Policy:** Community module source code must **never** be committed to this repository. Community contributions are registered as TOML metadata manifests pointing to developers' external repositories.

---

## 2. Repository Layout

```text
ELYos/
├── README.md                          # Project introduction and quick-start
├── LICENSE                            # Software license
├── CONTRIBUTING.md                    # Contributor guide and standards
│
├── core/                              # ELYos Core source code (Rust, Qt 6 / QML)
├── system-modules/                    # Official ELYos System Modules (ArchELYos)
├── community-system-modules/          # Registry manifests for community System Modules
├── modules/                           # Official ELYos Modules
├── community-modules/                 # Registry manifests for community Modules
│
├── sdk/                               # ELYos SDK, libraries, and compiler wrappers
├── tools/                             # Build, packaging, and validation tools
├── tests/                             # Integration tests and QEMU test harnesses
│
└── docs/                              # Project documentation
    ├── MANIFESTO.md                   # Core philosophy and principles
    └── TECHNICAL_SPECIFICATION.md     # Full architectural specification
```

---

## 3. Contributing Official Components

Official components (inside `core/`, `system-modules/`, `modules/`, `sdk/`, `tools/`, `tests/`, and `docs/`) are maintained directly in this repository.

### Development Prerequisites
- **Language:** Rust (latest stable toolchain).
- **GUI Framework:** Qt 6 + QML.
- **Automation:** Python 3.10+.
- **Virtualization:** QEMU (for testing Core boot and module installation).
- **Host System:** Windows 11 with WSL2 or native Linux.
- **Editor:** Visual Studio Code (recommended).

### Git Workflow
1. Fork or branch from `main`.
2. Use descriptive branch names:
   - `feature/<description>` for new capabilities
   - `fix/<description>` for bug repairs
   - `chore/<description>` for maintenance and structure
   - `docs/<description>` for documentation improvements
3. Ensure all code passes linting, formatting, and unit tests before opening a Pull Request.
4. Follow Conventional Commits format (e.g., `feat(core): implement boot selector timeout`, `fix(boot): resolve systemd-boot entry parser`).

---

## 4. Contributing Community Components (Registry)

Community components follow a decentralized registry pattern. **Do not commit your source code to the ELYos repository.**

### How to Register a Community Module:
1. Host your module source code and releases in your own public repository (e.g., on GitHub or GitLab).
2. Prepare a package adhering to the ELYos package specification (`.elyossysmod` for System Modules or `.elyosmod` for Modules).
3. Submit a Pull Request adding a single TOML manifest file to the appropriate registry directory:
   - For System Modules: `community-system-modules/<module-id>.toml`
   - For Modules: `community-modules/<module-id>.toml`

### Example Registry Manifest Format

```toml
[module]
id = "com.developer.example-module"
name = "Example Module"
description = "A concise description of what the module provides"
version = "1.0.0"

[repository]
type = "git"
url = "https://github.com/developer/example-module"
branch = "main"
tag = "v1.0.0"

[compatibility]
minimum_core_version = "0.1.0"
architecture = ["x86_64"]

[metadata]
developer = "Developer Name"
license = "MIT"
status = "unverified"
```

### Verification Tiers
- **Official:** Developed and maintained by the core ELYos team.
- **Community-Reviewed:** Audited by community reviewers for security and architectural compliance.
- **Unverified:** Default status upon initial registry submission.
- **Problematic:** Automatically assigned when issue reports exceed 25% of unique installations.

---

## 5. Review & Acceptance Process

1. **Automated Checks:** All PRs run CI checks (linting, build verification, and manifest validation).
2. **Architectural Review:** Maintainers verify adherence to the [Technical Specification](docs/TECHNICAL_SPECIFICATION.md).
3. **Safety & Security:** Code touching boot orchestration, cryptography, or user data partitions undergoes heightened review.
4. **Approval:** A minimum of one maintainer review is required for merging.

---

## 6. Communication & Questions

If you have questions about architectural decisions, open an issue on GitHub or consult the [Technical Specification](docs/TECHNICAL_SPECIFICATION.md).
