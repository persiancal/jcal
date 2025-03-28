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
OPTS="anch"
LONG_OPTS="nocolor,clean,help,alternative"

# @USAGE
usage() {
	printf "Jalali calendar library autogen build script.
usage: autogen.sh [-nch]
try \`autogen.sh --help\' for more information.
"
}

# @HELP
help() {
	printf "usage: autogen.sh [-nch]...
Invokes GNU build system tools in order to create necessary configuration scripts.

Operation modes:
  -a, --alternative\tdo not invoke autoreconf
  -n, --nocolor\t\tdisable output colors
  -c, --clean\t\tremove all auto-generated scripts and files from source tree
  -h, --help\t\tprint this help, then exit

Report bugs to <ghassemi@ftml.net>.
Jalali calendar home page: <http://nongnu.org/jcal>.
"
}

# prints text in green
print_ok() {
	printf "%s%s%s" "$green" "$1" "$zcolor"
}

# prints text in red
print_fail() {
	printf "%s%s%s" "$red" "$1" "$zcolor"
}

# echoes ``ok'' if parameter is zero, ''failed'' otherwise.
printk() {
	if [ "$1" = "0" ]; then
		print_ok "ok\n"
	else
		print_fail "failed\n"
	fi
	return "$1"
}

# prints text in a highlight
print_highlight() {
	printf "%s%s%s" "$yellow" "$1" "$zcolor"
}

# prints the value with a starting green `* `.
print_bullet() {
	printf "%s*%s %s" "$green" "$zcolor" "$(print_highlight "$1")"
}

# prints a red error and a following value
print_error() {
	printf "%serror%s: %s" "$red" "$zcolor" "$(print_highlight "$1")"
}

# performs make distclean and removes auto-generated files by GNU build system.
clean() {
	print_bullet "cleaning source tree...\n"

	# Makefile is present.
	if test -f Makefile; then
		print_bullet "performing distclean on sources if possible... "
		make distclean >/dev/null 2>&1
		stat=$?
		printk "$stat"
		if [ "$stat" != "0" ]; then
			print_error "cannot perform make distclean. run make distclean manually and check for erros.\n"
		fi
	fi

    files="autom4te.cache Makefile.in m4 aclocal.m4 configure config.sub
        config.guess config.log config.status depcomp install-sh libtool
        ltmain.sh missing src/Makefile.in man/Makefile.in
        test_kit/jalali/Makefile.in test_kit/jalali/Makefile
        test_kit/Makefile.in test_kit/Makefile test_kit/jalali/.deps
        test_kit/jtime/.deps test_kit/jtime/Makefile.in test_kit/jalali/Makefile
        libjalali/Makefile.in INSTALL"
    for i in $files; do
		if [ -f "$i" ] || [ -d "$i" ]; then
			print_bullet "deleting $i... "
			rm -rf "$i"
			printk 0
		fi
	done

	print_bullet
	print_ok "done\n"
}

# Setting colors to vt100 standard values, NULL if 0 gets passed to set_color()
set_colors() {
	if [ "$1" = "1" ]; then
		red="\033[1;31m"
		green="\033[1;32m"
		yellow="\033[1;33m"
		cyan="\033[1;36m"
		zcolor="\033[0m"
	else
		red=""
		green=""
		yellow=""
		cyan=""
		zcolor=""
	fi
}

# @is_present() $service $name $output $exit
# Checks whether a service is present on system.
# $service is the path to service.
# $name is the service name.
# $output specifies whether is_present() should work silently or not.
# $exit specifies whther is_present() should exit on the event of
# service not found.
is_present() {
	service="$1"
	name="$2"
	output="$3"
	exit="$4"
	present="0"

	if [ -n "$service" ]; then
		present=1
	fi

	if [ "$output" = "1" ]; then
		print_bullet "checking for $name... "
		if [ "$present" = "1" ]; then
			print_ok "yes\n"
		else
			print_fail "no\n"
		fi
	fi

	if [ "$present" = "0" ] && [ "$exit" = "1" ]; then
		print_error "$name was not found on your system. autogen.sh cannot continue.\n"
		exit 1
	fi

	return "$present"
}

# Checking for tools
# aclocal, libtoolize, autoconf, automake and autoreconf
check_services() {
	ACLOCAL="$(which aclocal 2>/dev/null)"
	is_present "${ACLOCAL}" "aclocal" 1 1
	# glibtoolize glue-patch
	LIBTOOLIZE="$(which glibtoolize 2>/dev/null)"
	stat=$?
	is_present "${LIBTOOLIZE}" "glibtoolize" 1 0
	if [ ${stat} -ne 0 ]; then
		LIBTOOLIZE="$(which libtoolize 2>/dev/null)"
		is_present "${LIBTOOLIZE}" "libtoolize" 1 1
	fi
	AUTOCONF="$(which autoconf 2>/dev/null)"
	is_present "${AUTOCONF}" "autoconf" 1 1
	AUTOMAKE="$(which automake 2>/dev/null)"
	is_present "${AUTOMAKE}" "automake" 1 1
	AUTORECONF="$(which autoreconf 2>/dev/null)"
	is_present "${AUTORECONF}" "autoreconf" 1 0

	print_bullet
	print_ok "done\n"
}

# @perform() $service $name $exit $params
# runs a service with a set of parameters.
# $service is the path to the service.
# $name is the service name.
# $exit specifies whether perform() should exit on the event of
# encoutering any errors or not.
# $params are the parameters passed to the service.
perform() {
	service="$1"
	name="$2"
	exit="$3"
	params="$4"

	print_bullet "running \`$name $params\`... "
	$service $params >/dev/null 2>&1

	stat="$?"
	printk "$stat"

	if [ "$stat" != "0" ]; then
		print_error "cannot run \`$name\`. please run $name manually and check for errors.\n"
	fi

	if [ "$exit" = "1" ] && [ "$stat" != "0" ]; then
		exit 1
	fi
}

# Operation modes.
CLEAN="0"
HELP="0"
COLOR="1"
ALTERN="0"


if ! which which 1>/dev/null 2>&1; then
	printf "cannot find \`\`which''. autogen cannot continue.\n"
	exit 1
fi

# Parsing command-line arguments
GETOPT=$(which getopt 2>/dev/null)
if [ -z "$GETOPT" ]; then
	printf "warning: getopt(1) was not found on your system. command line arguments will be ignored.\n"
else
	TEMP=$(${GETOPT} -o ${OPTS} -l ${LONG_OPTS} -n 'autogen.sh' -- "$@")

	for i in $TEMP; do
		case $i in
			-c|--clean) CLEAN=1;;
			-n|--nocolor) COLOR=0;;
			-h|--help) HELP=1;;
			-a|--alternative) ALTERN=1;;
		esac
	done
fi

# Setting colors.
set_colors "$COLOR"

# HELP
if [ "$HELP" = "1" ]; then
	help
	exit 0
fi

# CLEAN
if [ "$CLEAN" = "1" ]; then
	clean
	exit 0
fi

# Checking for services.
check_services

# alternative method.
if [ -z "$AUTORECONF" ] || [ "$ALTERN" = "1" ]; then
	printf "using alternative method: "
	print_highlight "manual\n"

	perform "${LIBTOOLIZE}" "libtoolize" "1" "--force --copy --install"
	perform "${ACLOCAL}" "aclocal" "1" "--force"
	perform "${AUTOMAKE}" "automake" "1" "--add-missing --force-missing --copy"
	perform "${AUTOCONF}" "autoconf" "1" "--force"
# autoreconf method
else
	printf "using preferred method: "
	print_highlight "autoreconf\n"
	perform "${LIBTOOLIZE}" "libtoolize" "1" "--force --copy --install"
	perform "${AUTORECONF}" "autoreconf" "1" "--force --install"
fi

print_bullet
print_ok "done\n"

exit 0
