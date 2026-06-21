# 08 — Improve Bash Destination Parsing

## Purpose

Reduce false positives in bash write-target extraction.

## Current issue

For commands like:

```text
cp
mv
install
dd
```

current extraction may treat source paths as write targets.

## Desired behavior

- `cp source dest` routes only `dest` through write rules.
- `mv source dest` routes only `dest` through write rules.
- `install source dest` routes only `dest` through write rules.
- `dd if=input of=output` routes only `output`.

## Suggested implementation

1. Add a simple shell tokenization helper for non-shell commands.
2. For `cp`, `mv`, `install`:
   - ignore options beginning with `-`
   - collect non-option args
   - use last arg as destination
3. For `dd`:
   - parse tokens matching `of=<path>`
4. Keep conservative fallback:
   - if write intent is detected but target cannot be parsed, confirm/block.

## Validation

- `cp app/auth/source.py /tmp/out.py` does not treat source as write target.
- `cp x app/auth/service.py` routes `app/auth/service.py`.
- `mv x app/auth/service.py` routes destination.
- `dd if=x of=app/auth/file.py` routes `app/auth/file.py`.
- Existing redirection and `tee` behavior still works.

## Stop conditions

Stop if attempting to parse full shell grammar. Keep this targeted.
