# Buggy Multilingual Corpus

This folder contains intentionally broken programs for exercising ANCP adapters and compiler shims.

The files are not meant to compile. They contain common error classes:

- missing imports,
- unresolved symbols,
- type mismatches,
- wrong argument counts,
- syntax errors,
- missing delimiters,
- missing modules/packages.

Run the automatic smoke runner:

```bash
python tools/run_bug_corpus.py
```

The runner detects which native tools are installed, runs the corresponding ANCP adapter/proxy path, and writes results under:

```text
.ancp/bug-corpus/
```

This corpus is intentionally small enough for repository use. Larger stress corpora should be generated outside git.

