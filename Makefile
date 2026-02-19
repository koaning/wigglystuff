.PHONY: js docs test docs-demos docs-serve docs-build docs-llm docs-gh marimo-notebook

install:
	# install the build tool for JS written in Golang
	curl -fsSL https://esbuild.github.io/dl/v0.19.11 | sh
	uv venv --allow-existing
	uv pip install -e '.[test,docs]'
	npm i

test:
	uv pip install -e '.[test]'
	uv run pytest --ignore=tests/test_browser

test-browser:
	uv pip install -e '.[test-browser]'
	uv run playwright install chromium
	uv run pytest tests/test_browser -v

test-all:
	uv pip install -e '.[test-browser]'
	uv run playwright install chromium
	uv run pytest -v

pypi: clean
	uv build
	uv publish

js-edgedraw:
	./esbuild --watch=forever --bundle --format=esm --outfile=wigglystuff/static/edgedraw.js js/edgedraw.js

js-gamepad:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/gamepad-widget.js js/gamepad/widget.js

js-keystroke:
	# build the keyboard shortcut widget bundle
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/keystroke-widget.js js/keystroke/widget.js

js-copybutton:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/copybutton.js js/copybutton/widget.tsx

js-talk:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/talk-widget.js js/talk/widget.js

js-driver-tour:
	cp js/driver-tour/styles.css wigglystuff/static/driver-tour.css
	./esbuild --bundle --format=esm --loader:.css=text --outfile=wigglystuff/static/driver-tour.js js/driver-tour/widget.js

js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx --bundle --format=esm --outfile=wigglystuff/static/paint.js --minify

js-pulsar-chart:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/pulsar-chart.js js/pulsar-chart/widget.js

js-neo4j-widget:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/neo4j-widget.js js/neo4j-widget/widget.js

js-diff-viewer:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/diff-viewer.js js/diff-viewer/widget.js --minify

js-scatter-widget:
	cp js/scatter-widget/styles.css wigglystuff/static/scatter-widget.css
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/scatter-widget.js js/scatter-widget/widget.js

clean:
	rm -rf .ipynb_checkpoints build dist drawdata.egg-info

docs: docs-demos
	mkdocs build -f mkdocs.yml
	uv run python scripts/copy_docs_md.py

docs-demos:
	uv run python scripts/export_marimo_demos.py --force

docs-serve:
	uv run python -m http.server --directory site

docs-build: docs-demos
	uv run mkdocs build -f mkdocs.yml
	uv run python scripts/copy_docs_md.py

docs-llm:
	uv run python scripts/copy_docs_md.py

docs-gh: docs-build
	uv run mkdocs gh-deploy -f mkdocs.yml --dirty

marimo-notebook:
	uv run marimo -y export html-wasm notebook.py --output docs/index.html --mode edit
	uv run python -m http.server 8000 --directory docs
