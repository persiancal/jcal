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

# @OPTIONS
OPTS="ah"
LONG_OPTS="help,alternative"

# @USAGE
function usage() {
	echo -e "Jalali calendar library autogen build script."
	echo -e "usage: autogen.sh [-ch]"
	echo -e "try \`autogen.sh --help\' for more information."
}

# @HELP
function help() {
	echo -e "usage: autogen.sh [-ch]..."
	echo -ne "Invokes GNU build system tools in order to create"
	echo -e " necessary configuration scripts.\n"
	echo -e "Operation modes:"
	echo -e "  -a, --alternative\tdo not invoke autoreconf"
	echo -e "  -h, --help\t\tprint this help, then exit\n"
	echo -e "Report bugs to <ghassemi@ftml.net>."
	echo -e "Jalali calendar home page: <http://nongnu.org/jcal>."
}

# Operation modes.
HELP=0
ALTERN=0

which which 1>/dev/null 2>&1
if [ $? -ne 0 ]; then
	echo -e "cannot find \`\`which''. autogen cannot continue."
	exit 1
fi

# Parsing command-line arguments
GETOPT=`which getopt 2>/dev/null`
if [ -z ${GETOPT} ]; then
	echo -ne "warning: getopt(1) was not found on your system."
	echo -e " command line arguments will be ignored."
else
	TEMP=`${GETOPT} -o ${OPTS} -l ${LONG_OPTS} -n 'autogen.sh' -- "$@"`

	for i in $TEMP; do
		case $i in
			-h|--help) let HELP=1;;
			-a|--alternative) let ALTERN=1;;
		esac
	done
fi

# HELP
if [ ${HELP} -eq 1 ]; then
	help
	exit 0
fi

libtoolize="$(command -v libtoolize || command -v glibtoolize)"
if [ -z "$libtoolize" ]; then
	printf "libtoolize or glibtoolize is needed and not found.
		Add to \$PATH or use another way to bootstrap the project.\n"
	exit 1
fi

"$libtoolize" --force --copy --install || exit 1
if command -v autoreconf || [ "$ALTERN" = "1" ]; then
	printf 'using autoreconf...\n'
	autoreconf --force --install || exit 1
	automake --add-missing --force-missing --copy || exit 1
	autoconf --force || exit 1
else
	printf 'not using autoreconf...\n'
	autoreconf --force --install || exit 1
fi	

printf "done. Read the README and INSTALL files.\n"
