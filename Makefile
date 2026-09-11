.PHONY: pipeline test serve

pipeline:
	python3 pipeline/run_pipeline.py

test:
	python3 -m unittest discover -s tests -v

serve: pipeline
	python3 -m http.server 8000 -d dashboard
