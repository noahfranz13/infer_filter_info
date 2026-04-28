Contributing
============

Contributions are welcome and greatly appreciated! Every little bit helps, and credit will always be given.

Workflow
--------

We follow the standard GitHub **fork and pull request** workflow:

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:

   .. code-block:: bash

      git clone https://github.com/your-username/infer_filter_info.git
      cd infer_filter_info

3. Install the package in **editable** mode with development dependencies:

   .. code-block:: bash

      pip install -e .[dev,docs]

4. Create a **branch** for local development:

   .. code-block:: bash

      git checkout -b name-of-your-bugfix-or-feature

5. When you're done making changes, check that your changes pass the **tests**:

   .. code-block:: bash

      pytest

6. **Commit** your changes using `Conventional Commits <https://www.conventionalcommits.org/>`_ (e.g., ``feat: add new filter mapping`` or ``fix: correct wavelength unit``). This is important for our automated versioning!

7. **Push** your branch to GitHub:

   .. code-block:: bash

      git push origin name-of-your-bugfix-or-feature

8. Submit a **pull request** through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

- The pull request should include tests.
- If the pull request adds functionality, the docs should be updated.
- The pull request should work for Python 3.10 and 3.12. Check the CI status on GitHub.
