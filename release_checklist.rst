* Check the release_checklist in the dpf_composites repo

* As soon as the docker image with the version tag is available, add explicit tests for the new version. This should happen when a release branch is created for normal releases and
  once the image is tagged manually for pre-releases.
   * Add docker pull for the container with the new version tag in ci_cd.yml
   * Add pytest run for the new version in tox.ini
* Update the compatibility in the docs: intro.rst / Compatibility
* Revert to released version of dpf core in the pyproject.toml file
* Follow this guide (https://dev.docs.pyansys.com/how-to/releasing.html) to create a release branch and release. Also bump version in test_metadata.py test.
