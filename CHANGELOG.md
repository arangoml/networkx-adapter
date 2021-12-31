## 3.0.1 (2021-12-31)

### New

* Blog post preparation (#58) [Anthony Mahanna]

### Fix

* Logo links. [aMahanna]

* Gh pr merge. [aMahanna]

* Release. [aMahanna]

### Other

* Revert "trying white networkx logo" [aMahanna]

  This reverts commit f93bf99398bf66a31a1886a61761cf88dc88e7b6.

* Trying white networkx logo. [aMahanna]

* Replace auto merge with echo. [aMahanna]

* Update: restrict build & analyze triggers. [aMahanna]


## 3.0.0 (2021-12-28)

### New

* Update documentation (#55) [Anthony Mahanna]

* Release automation rework (#52) [Anthony Mahanna]

* File & class name restructure (#50) [Anthony Mahanna]

* General Adapter Improvements (#45) [Anthony Mahanna]

### Changes

* Disable twine skip-existing flag (#44) [Anthony Mahanna]

### Fix

* Release. [aMahanna]

* Release.yml. [aMahanna]

### Other

* Update release.yml. [aMahanna]

* Build workflow improvements (#51) [Anthony Mahanna]


## 2.0.0 (2021-12-02)

### New

* Release Automation Debugging (#37) [Anthony Mahanna]

* Introduce batch insertion (#30) [Anthony Mahanna]

  * Update .gitignore

  * initial commit

  * new: test_validate_controller_class

  * Update README.md

  * Update README.md

  * fix: copy README to package directory in release environment

  * Update setup.py

  * Update setup.py

  * Update setup.py

  * Update release.yml

  * bump version

  * Update README.md

  * new: rename adapter method names (#35)

  * initial commit: #34

  * fix: rename methods

  * bump version

  * Update README.md

  * black

  * Revert "bump version"

  This reverts commit 979ab0a8262d23a66b1dde4019566bab6b0ba25b.

  * update: #34

  * revert README changes

  (documentation will be updated in #30 instead)

  * revert notebook changes

  (documentation will be updated in #30)

  * new: address comments

  update batch insertion to work with a batch size, remove insertion logic deprecated by ArangoDB, remove "overwrite" concept, misc cleanup

  * black

  * update documentation

  * Update VERSION

  * Update ArangoDB_NetworkxAdapter.ipynb

  * swap networkx & arangodb logo placement

  * Update build.yml

* Introduce release automation (#31) [Anthony Mahanna]

  * Update .gitignore

  * initial commit

  * Update build.yml

  * black

  * Update release.yml

  * Update release.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update README.md

  * Update build.yml

  * Update release.yml

  * Update release.yml

  * Update release.yml

  * Update release.yml

  * move: scripts directory

  * cleanup

  * new: changelog files

  * new: codeql action

  * Update release.yml

  * Update README.md

  * update: analyze paths

  * Update release.yml

### Fix

* Invalid artifact directories (#42) [Anthony Mahanna]

* Github actions workflow (#39) [Anthony Mahanna]

* Trigger new github action release (#36) [Anthony Mahanna]

  The initial 2.0.0 release was unsuccessful due to a faulty path, this has now been fixed.

### Other

* Trigger 2.0.0 release. [aMahanna]

* Update release.yml. [aMahanna]

* Initial commit (#32) [Anthony Mahanna]


## 1.0.1 (2021-11-17)

### Other

* Release 1.0.1 Preparation (#26) [Anthony Mahanna]

  * initial commit

  * Update setup.py

  * bump

  * new: docstrings

  * cleanup & update README

  * cleanup docstrings

  * Update ArangoDB_NetworkxAdapter.ipynb

  * cleanup


## 1.0.0 (2021-11-17)

### New

* Query options documentation. [aMahanna]

### Other

* Adapter refactoring (#21) [Anthony Mahanna]

  * new: initial cleanup commit

  * new: from_graph & from_collections

  * temporary: test script using fraud_dump data

  * Update arangoDB_networkx_adapter.py

  * checkpoint

  * Delete imdb.py

  * cleanup & increased abstraction

  * Update README.md

  * Update main.py

  * Update main.py

  * Update dgl_arangoDB_networkx_adapter.py

  * Update main.py

  * checkpoint

  * checkpoint

  * more progress

  * Update main.py

  * cleanup

  * update: from_arango_graph() & from_collections() abstraction

  * cleanup

  * checkpoint

  * temporary nuke: dgl

  (post-ML-sync discussion)

  * cleanup

  * Update README.md

  * checkpoint

  * second checkpoint

  * new: imdb data dump

  * new: preparing tests directory

  * update: setup

  * checkpoint pre-ML-sync

  * cleanup

  * Update README.md

  * bump version to 1.0.0

  * leaving jupyter notebooks alone for now

  (will be addressed in separate PR)

  * Update README.md

  * Update arangoDB_networkx_adapter.py

  * Update oasis.py

  * delete creds.data & oasis.py

  to keep things consistent, will pull from from https://github.com/arangodb/interactive_tutorials/tree/oasis_connector

  * Update arangorestore

  * refactor user responsibility

  * Delete arangorestore

  * new: overrides dependency

  For python 3.6/3.7 support

  * new: create_arangodb_graph with overwrite mode

  * cleanup

  * Update README.md

  * Update requirements.txt

  * Update setup.py

  * cleanup

  * Update ArangoDB_NetworkxAdapter.ipynb

  * Update setup.py

  * Update ArangoDB_NetworkxAdapter.ipynb

  * Create build.yml

  * Update test_arangoDB_networkx_adapter.py

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * new: arangorestore exec

  for running tests

  * Delete docker-compose.yml

  switching to oasis

  * cleanup

  * cleanup

  * Update conftest.py

  * Update conftest.py

  * Update build.yml

  * Update conftest.py

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * bump

  * Update conftest.py

  * Update conftest.py

  * Update conftest.py

  * Update conftest.py

  * bump

  * cleanup

  * cleanup

  * Update .gitignore

  * fix: typos

  * fix: _prepare method names

  * new: file renaming, adbnx_controller, notebook changes

  * Update ArangoDB_NetworkxAdapter.ipynb

  * fix: notebook typo

  * update: identify & keyify edge implementations

  * Update ArangoDB_NetworkxAdapter.ipynb

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * new: badges

  * Update adbnx_adapter.py

  * Update build.yml

  * Update build.yml

  * attempt to break pytest

  * break test again

  * pass tests

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * Update build.yml

  * python 3.10 support, cleanup

  * Update README.md

  * Update README.md

  * cleanup

  * new: karate_nx_graph unit test

  * Update README.md

  * cleanup: test_create_arangodb_graph

  * cleanup test & notebook

  * fix: test_full_cycle_from_networkx

* Urgent: fix adbnx_adapter pip install. [aMahanna]

* Merge pull request #24 from arangoml/prep-release-0.0.0.2.5.3. [Chris Woodward]

  Release prep for 0.0.0.2.5.3-1

* Update notebooks & setup.py. [aMahanna]

* Revive branch. [aMahanna]

* Merge pull request #23 from arangoml/prep-release-0.0.0.2.5.3. [Chris Woodward]

  Networkx-Adapter Release 0.0.0.2.5.3 Preparation
  Discussed with Rajiv

* Update: notebooks. [aMahanna]

  (also used nbstripout)

* Minor documentation update (#22) [Anthony Mahanna]

  * Update README.md

  * Update ArangoDB_NetworkxAdapter.ipynb

* Merge pull request #20 from arangoml/query-options. [Chris Woodward]

  Introduce AQL query options to create_networkx_graph

* Initial feature commit. [aMahanna]

* Fix IMDB data import (#15) [Chris Woodward]

* Oasis connection refactoring. (#14) [Rajiv Sambasivan]

* Narrative addition (#13) [Rajiv Sambasivan]

  * Added initial version of examples illustrating Networkx API with IMDB.

  * Added initial version of examples illustrating Networkx API with IMDB.

  * Added more features for bi-partite metrics.

  * Added detailed narrative of leveraging networkx and node2vec using the Networkx-Adapter.

  * Added detailed narrative of leveraging networkx and node2vec using the Networkx-Adapter.

  * Added detailed narrative of leveraging networkx and node2vec using the Networkx-Adapter.

  * Added detailed narrative of leveraging networkx and node2vec using the Networkx-Adapter.

  * Added detailed narrative of leveraging networkx and node2vec using the Networkx-Adapter.

  * Ucient explanation.

* Update oasis.py to ver from tutorial repo. (#12) [Rajiv Sambasivan]

  * Update oasis.py to ver from tutorial repo.

  * Remove output.

* Fixed branch and link issues in ITSM colab demo notebook. (#10) [Rajiv Sambasivan]

* Doc updates nx (#9) [Rajiv Sambasivan]

  * Documentation updates for the Networkx Adapters.

  * Created using Colaboratory

  * Created using Colaboratory

  * Created using Colaboratory

  * Update colab icon url fix.

  * Created using Colaboratory

  * Created using Colaboratory

  * Run autopep8 on new python scripts.

* Moved data files. (#8) [Joerg Schad]

* Initial baseline of the dgl and imdb nx adapter post refactoring. (#7) [Rajiv Sambasivan]

  * Initial baseline of the dgl and imdb nx adapter post refactoring.

  * Created using Colaboratory

  * Created using Colaboratory

  * Created using Colaboratory

  * Created using Colaboratory

  * Added colab version of notebooks.

  * Created using Colaboratory

  * Created using Colaboratory

  * Ran autopep8 on source.

  * Ran autopep8 on source.

* Cert error fix. (#6) [Rajiv Sambasivan]

* Fixed adapter version in Notebook. [joerg84]

* Improved example Notebook. [joerg84]

* Reduce logo size. [Joerg Schad]

* Merge pull request #5 from arangoml/readme. [Rajiv Sambasivan]

  Improved Readme.

* Improved Readme. [joerg84]

* Fixes in Oasis connection. (#4) [Joerg Schad]

* Initial rework of ArangoDB NetworkX Adapter. (#3) [Joerg Schad]

  * Initial rework of ArangoDB NetworkX Adapter.

  * Sketched UX in example notebook.

  * Added notebook infrastructure.

  * intermediate

  * push for checking Schema error

  * push for checking Schema error

  * MWE Fraud detection.

  * Added images.

  * Rework.

* Refactored networkx interface (#2) [Rajiv Sambasivan]

  * Adding example notebook.

  * Created using Colaboratory

  * Created using Colaboratory

  * Created using Colaboratory

  * Update with Colab notebook.

  * Update with Colab notebook.

  * deleted superfluous jupyter notebook.

  * imdb_example.

  * adding refactored networkx interface to repo.

  * adding refactored networkx interface to repo.

  * removed build dist directories.

* Merge pull request #1 from arangoml/add_readme. [Rajiv Sambasivan]

  Add readme

* Fixes for submodule directories. [rajiv.sambasivan@gmail.com]

* Added updates to README and package setup. [rajiv.sambasivan@gmail.com]

* Added README for the project and DGL Adapter. [rajiv.sambasivan@gmail.com]

* Added README for the project and DGL Adapter. [rajiv.sambasivan@gmail.com]

* Add .gitignore. [rajiv.sambasivan@gmail.com]

* Initial commit. [rajiv.sambasivan@gmail.com]


