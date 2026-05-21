# Repository Structure

```text
.
├── README.md
├── LICENSE
├── requirements-dev.txt
├── spec/
│   └── ancp-1.0.md
├── schemas/
│   └── ancp-1.0.schema.json
├── taxonomies/
│   ├── diagnostic-kinds.json
│   ├── effect-kinds.json
│   └── repair-kinds.json
├── docs/
│   ├── adapter-authoring.md
│   ├── cli-contract.md
│   ├── conformance.md
│   ├── implementation-roadmap.md
│   ├── language-mapping.md
│   ├── overview.md
│   ├── repository-structure.md
│   ├── security.md
│   └── sources.md
├── research/
│   ├── README.md
│   ├── tooling-matrix.md
│   ├── languages/
│   ├── standards/
│   └── source-docs/
├── examples/
│   ├── generic/
│   ├── python/
│   ├── rust/
│   ├── typescript/
│   ├── manifest.adapter.json
│   └── manifest.capabilities.json
└── tools/
    ├── fetch_sources.py
    └── verify_repo.py
```

The spec repository is intentionally docs-and-contracts first. Language adapters should live in separate packages once the protocol is stable.

