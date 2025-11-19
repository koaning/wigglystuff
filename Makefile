.PHONY: js docs gamepad

install: 
	# install the build tool for JS written in Golang
	curl -fsSL https://esbuild.github.io/dl/v0.19.11 | sh
	uv pip install -e . marimo

pypi: clean
	uv build
	uv publish

js:
	# build the JS file, only needed for the edge widget
	./esbuild --watch=forever --bundle --format=esm --outfile=wigglystuff/static/edgedraw.js js/edgedraw.js

gamepad:
	# build the gamepad widget bundle
	./esbuild --bundle --format=esm --outfile=wigglystuff/static/gamepad-widget.js js/gamepad/widget.js

clean:
	rm -rf .ipynb_checkpoints build dist drawdata.egg-info

docs: 
	uv run marimo -y export html-wasm notebook.py --output docs/index.html --mode run
	uv run python -m http.server 8000 --directory docs
