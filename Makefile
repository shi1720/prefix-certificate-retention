PYTHON ?= python
TECTONIC ?= tectonic
.PHONY: test data experiments figures paper poster arxiv
test:
	$(PYTHON) -m pytest -q
data:
	$(PYTHON) scripts/download_data.py
experiments:
	$(PYTHON) scripts/run_experiments.py
	$(PYTHON) scripts/run_closure.py
	$(PYTHON) scripts/run_event_grid.py
	$(PYTHON) scripts/verify_results.py
figures:
	$(PYTHON) scripts/make_figures.py
paper:
	mkdir -p output/pdf
	cd paper && $(TECTONIC) main.tex --keep-intermediates --outdir ../output/pdf
	cp output/pdf/main.pdf output/pdf/prefix-certificate-retention.pdf
poster:
	$(PYTHON) scripts/make_poster.py
arxiv:
	$(PYTHON) scripts/package_arxiv.py
