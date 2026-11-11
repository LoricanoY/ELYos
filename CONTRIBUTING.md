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
├── .github/                           # GitHub Actions workflows, issue & PR templates
│   ├── workflows/                     # Automated CI/CD pipelines
│   │   ├── ci.yml                     # Main quality gate & test runner
│   │   ├── manifest-validation.yml    # Manifest validator workflow
│   │   └── repository-structure.yml   # Structural boundary validator
│   ├── ISSUE_TEMPLATE/                # Bug, feature, and module submission templates
│   └── PULL_REQUEST_TEMPLATE.md       # Standardized PR checklist
│
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
│   ├── validate_manifests.py          # Manifest validation script
│   └── validate_structure.py          # Repository structure validation script
├── tests/                             # Unit tests, integration tests, and QEMU harnesses
│   ├── test_validate_manifests.py     # Manifest validator unit tests
│   └── test_validate_structure.py     # Structure validator unit tests
│
└── docs/                              # Project documentation
    ├── MANIFESTO.md                   # Core philosophy and principles
    └── TECHNICAL_SPECIFICATION.md     # Full architectural specification
```

---

## 3. Contributing Official Components

Official components (inside `core/`, `system-modules/`, `modules/`, `sdk/`, `tools/`, `tests/`, and `docs/`) are maintained directly in this repository.

### Development Prerequisites
- **Language:** Rust (latest stable toolchain) & Python 3.11+.
- **GUI Framework:** Qt 6 + QML.
- **Virtualization:** QEMU (for testing Core boot and module installation).
- **Host System:** Windows 11 with WSL2 or native Linux.
- **Editor:** Visual Studio Code (recommended).

### Git Workflow
1. Fork or branch from `main`.
2. Use descriptive branch names:
   - `feat/<description>` for new features or capabilities
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
3. Ensure you have published a release and identified its **immutable Git commit SHA** (40-character hexadecimal hash). While a Git tag (e.g., `v1.0.0`) may be provided as human-readable metadata, git tags are mutable and cannot serve as cryptographic proof of immutability.
4. Submit a Pull Request adding a single TOML manifest file to the appropriate registry directory:
   - For System Modules: `community-system-modules/<module-id>.toml`
   - For Modules: `community-modules/<module-id>.toml`

### Manifest Schema & Requirements

Every community manifest must contain the following four sections and fields:

```toml
[module]
id = "com.developer.example-module"         # Required: Reverse-domain format (e.g., org.elyos.*, com.developer.*)
name = "Example Module"                     # Required: Display name string
description = "A concise description"       # Required: Description string
version = "1.0.0"                           # Required: Valid Semantic Version (SemVer 2.0.0)

[repository]
type = "git"                                # Required: Currently 'git'
url = "https://github.com/developer/mod"    # Required: Valid http(s):// or git:// URL
commit = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678" # Required: Immutable 40-character Git commit SHA
tag = "v1.0.0"                              # Optional: Human-readable release tag metadata

[compatibility]
minimum_core_version = "0.1.0"              # Required: SemVer string for minimum supported Core
architecture = ["x86_64"]                   # Required: List of supported architectures (x86_64, aarch64, etc.)

[metadata]
developer = "Developer Name"                # Required: Developer name or organization
license = "MIT"                             # Required: Open-source license identifier
# NOTE: Do NOT include a 'status' field. Verification status is maintained exclusively by ELYos maintainers.
```

### Verification Tiers & Maintainer Control

| Status Tier | Description | Controlled By |
|---|---|---|
| `Official` | Maintained and verified directly by the core ELYos team | Core maintainers |
| `Community-Reviewed` | Audited and validated by community reviewers | Core maintainers |
| `Unverified` | Initial baseline state for newly registered community modules | Core maintainers |
| `Problematic` | Flagged when issue reports exceed 25% of unique installations | Automated / maintainers |

> [!IMPORTANT]
> **Why is the `status` field excluded from community manifests?**  
> Verification status serves as an ecosystem trust anchor. Community developers **must never assign or declare their own verification status**. Verification labels are tracked and managed exclusively by ELYos repository maintainers as external registry metadata. Any community manifest that includes a `status` field will be **automatically rejected** by CI.

---

## 5. Automated Validation & Local Testing

Before submitting a Pull Request, run the local validation scripts to ensure your changes pass CI quality gates:

### Running Validation Locally

From the repository root:

1. **Validate Repository Structure & Boundaries:**
   ```bash
   python tools/validate_structure.py
   ```
   *Verifies that required top-level directories and documentation exist, and confirms that community registries contain only TOML manifests (no accidental source code or binary commits).*

2. **Validate Community TOML Manifests:**
   ```bash
   python tools/validate_manifests.py
   ```
   *Validates TOML syntax, required fields, reverse-domain IDs, SemVer compliance, URL schemes, immutable tags/commits, and verification status restrictions.*

3. **Run the Automated Test Suite:**
   ```bash
   python -m unittest discover -s tests -v
   ```
   *Executes all unit tests verifying the validator tools and test harnesses.*

---

## 6. GitHub Actions CI/CD Pipeline

When a Pull Request is opened or updated, GitHub Actions automatically executes our validation matrix:

- **`CI` (`.github/workflows/ci.yml`):**  
  Triggered on all PRs targeting `main` and pushes to `main`. Runs structure validation, manifest validation, and the unit test suite across Python 3.11 and 3.12.
- **`Community Manifest Validation` (`.github/workflows/manifest-validation.yml`):**  
  Triggered whenever files in `community-system-modules/` or `community-modules/` are modified. Ensures zero duplicate IDs, valid SemVer, and strict security compliance.
- **`Repository Structure & Boundaries` (`.github/workflows/repository-structure.yml`):**  
  Triggered on changes to top-level architecture or core documentation. Ensures community registries remain strictly separated from official component source trees.

---

## 7. Review & Acceptance Process

1. **Automated CI Passing:** All GitHub Actions checks must be green.
2. **Architectural Review:** Maintainers verify adherence to the [Technical Specification](docs/TECHNICAL_SPECIFICATION.md).
3. **Safety & Security:** Code touching boot orchestration, cryptography, or user data partitions undergoes heightened review.
4. **Approval:** A minimum of one maintainer review is required for merging.
