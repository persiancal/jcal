#!/bin/sh
#
# Run GNU Autotool commands forcefully to regenerate stuff.
#
# Reverse the generation by removing any file created (`git clean -fxdn` lists
# them).

libtoolize="$(command -v libtoolize || command -v glibtoolize)"
if [ -z "$libtoolize" ]; then
	printf "libtoolize or glibtoolize is needed and not found.
		Add to \$PATH or use another way to bootstrap the project.\n"
	exit 1
fi

"$libtoolize" --force --copy --install || exit 1
if command -v autoreconf; then
	printf 'using autoreconf...\n'
	autoreconf --force --install || exit 1
	automake --add-missing --force-missing --copy || exit 1
	autoconf --force || exit 1
else
	printf 'not using autoreconf...\n'
	autoreconf --force --install || exit 1
fi	

printf "done. Read the README and INSTALL files.\n"
