---
description: Windows + Git Bash environment quirks when running AWS CLI / aws commands from this repo.
paths: ["**/*"]
---

# Windows / Git Bash dev environment notes

This repo is developed on Windows via Git Bash. Two AWS CLI quirks cost real debugging time
during #346 and recur constantly whenever a command touches CloudWatch logs, S3 URLs, or
`file://` paths:

- **`MSYS_NO_PATHCONV=1`** -- without it, Git Bash mangles any `/`-leading argument (log group
  names, `file://` URIs, S3 paths) into a bogus Windows path before `aws.exe` ever sees it. Set it
  on the same line as the `aws` call -- exported env vars don't persist across separate Bash tool
  invocations.
- **`PYTHONIOENCODING=utf-8`** (and `PYTHONUTF8=1`) -- without it, a non-ASCII byte anywhere in
  AWS CLI output (CloudWatch logs, EB tail logs -- it always shows up eventually) crashes the
  CLI's own output with a `charmap codec can't encode` error, even when output is redirected to a
  file. When parsing that output in Python afterward, write with `f.write(..., encoding='utf-8')`,
  never `print()` -- `print()` still routes through the Windows console codepage even when stdout
  is redirected, and hits the same crash downstream.
- Windows-native tools (e.g. `python.exe`) don't understand Git Bash's own `/tmp` mount mapping --
  pass them real Windows-style paths (`C:/Users/...`) instead of `/tmp/...` when a command will be
  consumed by a non-MSYS-aware executable.

See the `debug-pipeline` skill for these applied to the actual AWS log-fetching commands this
repo's pipeline debugging needs.
