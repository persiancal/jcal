ACLOCAL_AMFLAGS = -I m4
SUBDIRS = libjalali src man test_kit

if WANT_PYJALALI
install-exec-hook:
	@printf "Installing PyJalali"
	test -d pyjalali || mkdir pyjalali
	@cp $(srcdir)/pyjalali/*.py pyjalali
	@cp $(srcdir)/setup.py .
	LIBJALALI_DIR=$(DESTDIR)$(libdir) \
	$(PYTHON) setup.py install --prefix=$(DESTDIR)$(exec_prefix) --record=pyinstalled.txt

uninstall-hook:
	while read -r fn; do rm -rf "$$fn"; done <pyinstalled.txt
	-rmdir $(DESTDIR)$(pythondir)/pyjalali && rm pyinstalled.txt
endif
