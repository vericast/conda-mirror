#!/bin/bash
# Ready to release

NEW_TAG=${1?Need a tag}
GITHUB_TOKEN=${2?Need a github token}

# Generate the new changelog:
github_changelog_generator -t ${GITHUB_TOKEN}

# use `sed` to replace the "untagged" stuff with what is actually in the
# tag that we are about to create
sed -i.bak "s/HEAD/${NEW_TAG}/" CHANGELOG.md
sed -i.bak "s/Unreleased/${NEW_TAG}/" CHANGELOG.md
git add CHANGELOG.md
git commit -m "Tagging ${NEW_TAG}"
git tag -a ${NEW_TAG} -m "Tagging ${NEW_TAG}

See CHANGELOG.md for changes in ${NEW_TAG}"
git push && git push --tags

rm CHANGELOG.md.bak
