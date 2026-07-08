# Harness-template authoring tooling (temporary home — _WIP/).
# Travels with the template when it is extracted to its own repo (OQ-3).
#
# The constitution is authored as a dual-layer draft (ADR-015): each section is a
# LEAN binding block followed by a delimited, strippable EXPANDED rationale block.
# `make lean` generates the production edition by stripping the EXPANDED blocks and
# the WIP scaffolding comments, leaving the frontmatter as the file head.
#
# Decision (ADR-017): keep BOTH editions. CLAUDE.draft.md is the source of truth
# (teaching edition); CLAUDE.lean.md is generated on demand (production edition).

SRC      ?= CLAUDE.draft.md
LEAN_OUT ?= CLAUDE.lean.md

.PHONY: lean help

help:
	@echo "Harness-template tooling:"
	@echo "  make lean   Strip EXPANDED blocks + WIP scaffolding -> $(LEAN_OUT) (production edition)"

# Produce the lean/production constitution from the dual-layer draft:
#   1. delete each EXPANDED block (open delimiter .. close delimiter, inclusive);
#   2. delete the multi-line WIP scaffolding comments (<!-- .. --> on their own lines);
#   3. squeeze repeated blank lines, then drop leading blanks so the frontmatter
#      (--- ... ---) is the literal file head, as it must be in an instantiated CLAUDE.md.
lean:
	@sed -e '/<!-- EXPANDED:/,/<!-- \/EXPANDED:/d' \
	     -e '/^<!--$$/,/^-->$$/d' $(SRC) \
	  | cat -s \
	  | sed '/./,$$!d' > $(LEAN_OUT)
	@echo "Wrote $(LEAN_OUT) ($$(wc -l < $(LEAN_OUT)) lines) — EXPANDED blocks + WIP scaffolding stripped."
