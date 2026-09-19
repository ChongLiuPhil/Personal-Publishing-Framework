QUARTO ?= quarto

.PHONY: check web-publish-check cloudflare-build preview clean help

help:
	@echo "Available targets:"
	@echo "  make check              - validate the template publication contract"
	@echo "  make web-publish-check  - render and validate the Web artifact"
	@echo "  make cloudflare-build   - install pinned Quarto if needed, then run web-publish-check"
	@echo "  make preview            - start the Web preview"
	@echo "  make clean              - remove generated output"

check:
	python3 scripts/check_publication_contract.py

web-publish-check: check
	$(QUARTO) render --profile web
	python3 scripts/verify_web_output.py

cloudflare-build:
	bash scripts/cloudflare_build.sh

preview: check
	$(QUARTO) preview --profile web

clean:
	rm -rf _book _publication .quarto
