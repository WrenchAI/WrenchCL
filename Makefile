.PHONY: release-patch release-minor release-major dry-release-patch dry-release-minor dry-release-major

release-patch:
	./release.sh patch

release-minor:
	./release.sh minor

release-major:
	./release.sh major

dry-release-patch:
	DRY_RUN=1 ./release.sh patch

dry-release-minor:
	DRY_RUN=1 ./release.sh minor

dry-release-major:
	DRY_RUN=1 ./release.sh major
