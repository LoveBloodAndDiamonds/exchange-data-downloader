clean-macos-trash-stuff:
	find . -name ".DS_Store" -type f -delete

pypi-build-and-publish:
	python -m build ; rm -rf exdata.egg-info ; python -m twine upload dist/* ; rm ; rm -rf dist
)
