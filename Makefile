.PHONY: add-font

add-font:
	@if [ -z "$(slug)" ]; then \
		echo "Please provide a font slug. Usage: make add-font slug=<font-slug>"; \
		exit 1; \
	fi
	mkdir -p tmp
	curl -L "https://gwfh.mranftl.com/api/fonts/$(slug)?download=zip&subsets=latin&variants=regular&formats=ttf" -o "tmp/$(slug).zip"
	unzip "tmp/$(slug).zip" -d "tmp/$(slug)"
	find "tmp/$(slug)" -name "*.ttf" -exec mv {} "fonts/$(slug).ttf" \;
	rm -rf tmp
	echo "Font $(slug) added successfully."
