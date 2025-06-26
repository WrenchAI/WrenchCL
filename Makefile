.PHONY: release-patch release-minor release-major \
        dry-release-patch dry-release-minor dry-release-major

release-patch:
	bash ./release.sh patch

release-minor:
	bash ./release.sh minor

release-major:
	bash ./release.sh major

dry-release-patch:
	DRY_RUN=1 bash ./release.sh patch

dry-release-minor:
	DRY_RUN=1 bash ./release.sh minor

dry-release-major:
	DRY_RUN=1 bash ./release.sh major