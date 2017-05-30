Contributing
============

Here are some guidelines for hacking on `proto-compiler-plugin`_.

-  Please **sign** one of the `Contributor License Agreements`_ below.
-  `File an issue`_ to notify the maintainers about what you're working on.
-  `Fork the repo`_; develop and `test your code changes`_; add docs.
-  Make sure that your `commit messages`_ clearly describe the changes.
-  `Make the pull request`_.

.. _`Fork the repo`: https://help.github.com/articles/fork-a-repo
.. _`forking`: https://help.github.com/articles/fork-a-repo
.. _`commit messages`: http://chris.beams.io/posts/git-commit/

.. _`File an issue`:

Before writing code, file an issue
----------------------------------

Use the issue tracker to start the discussion. It is possible that someone else
is already working on your idea, your approach is not quite right, or that the
functionality exists already. The ticket you file in the issue tracker will be
used to hash that all out.

Fork `proto-compiler-plugin`
-------------------

We will use GitHub's mechanism for `forking`_ repositories and making pull
requests. Fork the repository, and make your changes in the forked repository.

.. _`test your code changes`:

Include tests
-------------

Be sure to add relevant tests and run then them using :code:`tox` before making the pull request.
Docs will be updated automatically when we merge to `master`, but
you should also build the docs yourself via :code:`tox -e docs`, making sure that the docs build OK
and that they are readable.

.. _`tox`: https://tox.readthedocs.org/en/latest/

Make the pull request
---------------------

Once you have made all your changes, tested, and updated the documentation,
make a pull request to move everything back into the main `proto-compiler-plugin`_
repository. Be sure to reference the original issue in the pull request.
Expect some back-and-forth with regards to style and compliance of these
rules.

Using a Development Checkout
----------------------------

You’ll have to create a development environment to hack on
`proto-compiler-plugin`_, using a Git checkout:

-   While logged into your GitHub account, navigate to the `proto-compiler-plugin repo`_ on GitHub.
-   Fork and clone the `proto-compiler-plugin` repository to your GitHub account
    by clicking the "Fork" button.
-   Clone your fork of `proto-compiler-plugin` from your GitHub account to your
    local computer, substituting your account username and specifying
    the destination as `hack-on-proto-compiler-plugin`. For example:

  .. code:: bash

    cd ${HOME}
    git clone git@github.com:USERNAME/proto-compiler-plugin.git hack-on-proto-compiler-plugin
    cd hack-on-proto-compiler-plugin

    # Configure remotes such that you can pull changes from the proto-compiler-plugin
    # repository into your local repository.
    git remote add upstream https://github.com:google/proto-compiler-plugin

    # fetch and merge changes from upstream into master
    git fetch upstream
    git merge upstream/master


Now your local repo is set up such that you will push changes to your
GitHub repo, from which you can submit a pull request.

-   Create use tox to create development virtualenv in which `proto-compiler-plugin`_ is installed:

  .. code:: bash

    sudo pip install tox
    cd ~/hack-on-proto-compiler-plugin
    tox -e devenv

-   This is creates a tox virtualenv named `development` that has proto-compiler-plugin installed.
    Activate it to use proto-compiler-plugin locally, e.g, from the python prompt.

  .. code:: bash

    cd ~/hack-on-proto-compiler-plugin
    . .tox/develop/bin/activate

.. _`proto-compiler-plugin`: https://github.com/googleapis/proto-compiler-plugin
.. _`proto-compiler-plugin repo`: https://github.com/googleapis/proto-compiler-plugin


Running Tests
-------------

-   To run the full set of `proto-compiler-plugin` tests on all platforms, install
    `tox`_ into a system Python.  The :code:`tox` console script will be
    installed into the scripts location for that Python.  While in the
    `proto-compiler-plugin` checkout root directory (it contains :code:`tox.ini`),
    invoke the `tox` console script.  This will read the :code:`tox.ini` file and
    execute the tests on multiple Python versions and platforms; while it runs,
    it creates a virtualenv for each version/platform combination.  Note that
    your `BREW_HOME` must be set to the brew directory where protoc is installed
    in order for tests to work. For example:

  .. code:: bash

      export BREW_HOME=~/.linuxbrew
      sudo pip install tox
      cd ~/hack-on-proto-compiler-plugin
      tox

Contributor License Agreements
------------------------------

Before we can accept your pull requests you'll need to sign a Contributor
License Agreement (CLA):

-   **If you are an individual writing original source code** and **you own
    the intellectual property**, then you'll need to sign an
    `individual CLA`_.
-   **If you work for a company that wants to allow you to contribute your
    work**, then you'll need to sign a `corporate CLA`_.

You can sign these electronically (just scroll to the bottom). After that,
we'll be able to accept your pull requests.

.. _`individual CLA`: https://developers.google.com/open-source/cla/individual
.. _`corporate CLA`: https://developers.google.com/open-source/cla/corporate
