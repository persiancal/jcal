#!/usr/bin/env bash
#
# autogen.sh - Tools for manipulating Jalali representation of Iranian calendar
# and necessary conversations to Gregorian calendar.
# Copyright (C) 2006, 2007, 2009, 2010, 2011 Ashkan Ghassemi.
#
# This file is part of libjalali.
#
# libjalali is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# libjalali is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with libjalali.  If not, see <http://www.gnu.org/licenses/>.
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
