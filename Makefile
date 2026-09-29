clean-macos-trash-stuff:
	find . -name ".DS_Store" -type f -delete

pypi-build-and-publish:
	python3 -m build ; rm -rf exdata.egg-info ; python3 -m twine upload dist/* ; rm -rf dist exchange_data_downloader.egg-info ; rm -rf dist
