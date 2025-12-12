.PHONY: js docs test docs-demos docs-serve docs-build marimo-notebook

install: 
	# install the build tool for JS written in Golang
	curl -fsSL https://esbuild.github.io/dl/v0.19.11 | sh
	uv venv --allow-existing
	uv pip install -e '.[test,docs]'
	npm i

test:
	uv pip install -e '.[test]'
	uv run pytest

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
	./esbuild --watch=forever --bundle --format=esm --outfile=wigglystuff/static/copybutton.js js/copybutton/widget.tsx

js-talk:
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/talk-widget.js js/talk/widget.js

js-driver-tour:
	{ cat node_modules/driver.js/dist/driver.css; echo; cat js/driver-tour/styles.css; } > wigglystuff/static/driver-tour.css
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/driver-tour.js js/driver-tour/widget.js

js-paint:
	./node_modules/.bin/tailwindcss -i ./js/paint/styles.css -o ./wigglystuff/static/paint.css
	./node_modules/.bin/esbuild js/paint/widget.tsx --bundle --format=esm --outfile=wigglystuff/static/paint.js --minify

clean:
	rm -rf .ipynb_checkpoints build dist drawdata.egg-info

docs:
	uv run mkdocs build -f mkdocs.yml

docs-demos:
	uv run python scripts/export_marimo_demos.py

docs-serve:
	uv run mkdocs serve -f mkdocs.yml

docs-build: docs-demos
	uv run mkdocs build -f mkdocs.yml

marimo-notebook:
	uv run marimo -y export html-wasm notebook.py --output docs/index.html --mode edit
	uv run python -m http.server 8000 --directory docs
