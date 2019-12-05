
# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	/bin/rm -rf $(BUILDDIR)/html0
	/bin/mkdir -p $(BUILDDIR)/html0
	/bin/mv $(BUILDDIR)/html/.git $(BUILDDIR)/html0
	/bin/mv $(BUILDDIR)/html/.nojekyll  $(BUILDDIR)/html0
	/bin/rm -rf $(BUILDDIR)/html
	/bin/mv $(BUILDDIR)/html0 $(BUILDDIR)/html
