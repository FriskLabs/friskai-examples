# Central commands for the friskai-examples repo.
#
# Words after the target are forwarded to the underlying script:
#
#   make run python/basic-langchain-agent
#   make run -- python/basic-langchain-agent --frisk-env staging
#   make set-versions EXAMPLE=python/basic-langchain-agent SOURCE_ENV=local
#   make example python/basic-langchain-agent SOURCE_ENV=local
#
# The `--` is only needed when passing --flags (make would otherwise try to
# parse them as its own options). Multi-word quoted args don't survive make's
# word splitting — for those, fall back to ARGS="...".

RUN := ./frisk-example.sh
SOURCE_ENV ?= production

# Everything after a forwarding target becomes no-op goals, collected here.
FORWARD_TARGETS := run example
ifneq ($(filter $(firstword $(MAKECMDGOALS)),$(FORWARD_TARGETS)),)
  FWD := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  ifneq ($(FWD),)
    .PHONY: $(FWD)
    $(eval $(FWD):;@:)
  endif
endif
FWD := $(or $(ARGS),$(FWD))

.PHONY: help run set-versions example

help:
	@echo 'Usage:'
	@echo '  make run [--] <path> [--frisk-env local|staging|production] [--example <file>] [args...]'
	@echo '      Alias for $(RUN). Use -- before any --flags.'
	@echo '  make set-versions [EXAMPLE=<platform/name>] [SOURCE_ENV=production|local]'
	@echo '      Set frisk SDK versions (all examples if EXAMPLE unset) and install.'
	@echo '  make example [--] <path> [args...] [SOURCE_ENV=production|local]'
	@echo '      Run set-versions for the example, then run it via $(RUN).'
	@echo ''
	@echo 'Multi-word quoted args need the ARGS="..." form instead.'

run:
	$(RUN) $(FWD)

set-versions:
	./set-versions.sh $(if $(EXAMPLE),--example $(EXAMPLE)) --source-env $(SOURCE_ENV)

example:
ifeq ($(FWD),)
	$(error an example path is required, e.g. make example python/basic-langchain-agent)
endif
	./set-versions.sh --example $(firstword $(FWD)) --source-env $(SOURCE_ENV)
	$(RUN) $(FWD)
