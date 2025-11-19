.PHONY: js docs test

install: 
	# install the build tool for JS written in Golang
	curl -fsSL https://esbuild.github.io/dl/v0.19.11 | sh
	uv venv --allow-existing
	uv pip install -e '.[test]' marimo
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
	# build the gamepad widget bundle
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/gamepad-widget.js js/gamepad/widget.js

js-copybutton:
	./esbuild --watch=forever --bundle --format=esm --outfile=wigglystuff/static/copybutton.js js/copybutton/widget.tsx

clean:
	rm -rf .ipynb_checkpoints build dist drawdata.egg-info

docs: 
	uv run marimo -y export html-wasm notebook.py --output docs/index.html --mode run
	uv run python -m http.server 8000 --directory docs
