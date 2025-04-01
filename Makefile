.PHONY: js docs

install: 
	# install the build tool for JS written in Golang
	curl -fsSL https://esbuild.github.io/dl/v0.19.11 | sh
	python -m pip install -e .
	python -m pip install twine wheel

pypi: clean
	uv build
	uv publish

js:
	# build the JS file, only needed for the edge widget
	./esbuild --watch=forever --bundle --format=esm --outfile=wigglystuff/static/edgedraw.js js/edgedraw.js

clean:
	rm -rf .ipynb_checkpoints build dist drawdata.egg-info

docs: 
	marimo export html-wasm notebook.py --output docs/index.html --mode run