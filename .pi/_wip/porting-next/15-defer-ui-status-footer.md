# 15 — Defer UI Status/Footer Indicator

## Purpose

Record that a UI phase indicator is useful but not essential.

## Current replacement

The harness already provides:

```text
/box status --verbose
/phase status --verbose
```

These show:

- current phase
- plan status
- RED/GREEN status
- allowed files
- active gates

## Why defer

A footer/status-line indicator depends on Pi UI extension capabilities and may add fragility.

## Revisit trigger

Consider UI indicator only if developers frequently lose track of current phase despite verbose status.

## Desired future behavior

Show compact state such as:

```text
Phase: IMPLEMENTING | Plan: FROZEN | RED: yes | GREEN: no | Box: auth
```

## Validation if implemented later

- indicator updates after `/phase set`
- indicator updates after `/box set`
- indicator updates after RED/GREEN changes
- no performance impact
- no extension reload issues
