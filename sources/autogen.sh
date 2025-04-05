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
OPTS="ach"
LONG_OPTS="clean,help,alternative"

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
	echo -ne "  -c, --clean\t\tremove all auto-generated scripts"
	echo -e " and files from source tree"
	echo -e "  -h, --help\t\tprint this help, then exit\n"
	echo -e "Report bugs to <ghassemi@ftml.net>."
	echo -e "Jalali calendar home page: <http://nongnu.org/jcal>."
}

# echoes ``ok'' if parameter is zero, ''failed'' otherwise.
function printk() {
	local STAT=$1

	if [ $1 -eq 0 ]; then
		echo -e "ok"
	else
		echo -e "failed"
	fi

	return ${STAT}
}

# performs make distclean and removes auto-generated files by GNU build system.
function clean() {
	local STAT
	# files
	local FUBARS=( "autom4te.cache" "Makefile.in" "m4" "aclocal.m4"
		"configure" "config.sub" "config.guess" "config.log"
		"config.status" "depcomp" "install-sh" "libtool" "ltmain.sh"
		"missing" "src/Makefile.in" "man/Makefile.in"
        "test_kit/jalali/Makefile.in" "test_kit/jalali/Makefile"
        "test_kit/Makefile.in" "test_kit/Makefile"
        "test_kit/jalali/.deps" "test_kit/jtime/.deps"
        "test_kit/jtime/Makefile.in" "test_kit/jalali/Makefile"
		"libjalali/Makefile.in" "INSTALL" )

	echo -e "* cleaning source tree..."

	# Makefile is present.
	if test -f Makefile; then
		echo -ne "* performing distclean on sources if possible... "
		make distclean >/dev/null 2>&1
		let STAT=$?

		printk ${STAT}
		if [ ${STAT} -ne 0 ]; then
			echo -ne "error: cannot perform make distclean."
			echo -e " run make distclean manually and check for erros."
		fi
	fi

	for i in ${FUBARS[@]}; do
		if [ -f $i ] || [ -d $i ]; then
			echo -ne "* deleting $i... "
			rm -rf $i
			printk 0
		fi
	done

	echo -e "* done"
}

# @is_present() $SERVICE $NAME $OUTPUT $EXIT
# Checks whether a service is present on system.
# $SERVICE is the path to service.
# $NAME is the service name.
# $OUTPUT specifies whether is_present() should work silently or not.
# $EXIT specifies whther is_present() should exit on the event of
# service not found.
function is_present() {
	local SERVICE=$1
	local NAME=$2
	local OUTPUT=$3
	local EXIT=$4
	local PRESENT=0

	if [ -n "${SERVICE}" ]; then
		let PRESENT=1
	fi

	if [ ${OUTPUT} -eq 1 ]; then
		echo -ne "* checking for ${NAME}... "
		if [ ${PRESENT} -eq 1 ]; then
			echo -e "yes"
		else
			echo -e "no"
		fi
	fi

	if [ ${PRESENT} -eq 0 ] && [ ${EXIT} -eq 1 ]; then
		echo -ne "error: ${NAME} was not found"
		echo -e "on your system. autogen.sh cannot continue."
		exit 1
	fi

	return ${PRESENT}
}

# Checking for tools
# aclocal, libtoolize, autoconf, automake and autoreconf
function check_services() {
	local STAT
	ACLOCAL="$(which aclocal 2>/dev/null)"
	is_present "${ACLOCAL}" "aclocal" 1 1
	# glibtoolize glue-patch
	LIBTOOLIZE="$(which glibtoolize 2>/dev/null)"
	STAT=$?
	is_present "${LIBTOOLIZE}" "glibtoolize" 1 0
	if [ ${STAT} -ne 0 ]; then
		LIBTOOLIZE="$(which libtoolize 2>/dev/null)"
		is_present "${LIBTOOLIZE}" "libtoolize" 1 1
	fi
	AUTOCONF="$(which autoconf 2>/dev/null)"
	is_present "${AUTOCONF}" "autoconf" 1 1
	AUTOMAKE="$(which automake 2>/dev/null)"
	is_present "${AUTOMAKE}" "automake" 1 1
	AUTORECONF="$(which autoreconf 2>/dev/null)"
	is_present "${AUTORECONF}" "autoreconf" 1 0
	echo -e "* done\n"
}

# @perform() $SERVICE $NAME $EXIT $PARAMS
# runs a service with a set of parameters.
# $SERVICE is the path to the service.
# $NAME is the service name.
# $EXIT specifies whether perform() should exit on the event of
# encoutering any errors or not.
# $PARAMS are the parameters passed to the service.
function perform() {
	local SERVICE=$1
	local NAME=$2
	local EXIT=$3
	local PARAMS=$4
	local SSTAT

	echo -ne "* running ${NAME} ${PARAMS}... "
	${SERVICE} ${PARAMS} >/dev/null 2>&1
	let STAT=$?

	printk ${STAT}

	if [ ${STAT} -ne 0 ]; then
		echo -ne "error: cannot run ${NAME}."
		echo -e " please run ${NAME} manually and check for errors."
	fi

	if [ ${EXIT} -eq 1 ] && [ ${STAT} -ne 0 ]; then
		exit 1
	fi
}

# Operation modes.
CLEAN=0
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
			-c|--clean) let CLEAN=1;;
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

# CLEAN
if [ ${CLEAN} -eq 1 ]; then
	clean
	exit 0
fi

# Checking for services.
check_services

# alternative method.
if [ -z "${AUTORECONF}" ] || [ ${ALTERN} -eq 1 ]; then
	echo -e "using alternative method: manual"
	perform "${LIBTOOLIZE}" "libtoolize" "1" "--force --copy --install"
	perform "${ACLOCAL}" "aclocal" "1" "--force"
	perform "${AUTOMAKE}" "automake" "1" "--add-missing --force-missing --copy"
	perform "${AUTOCONF}" "autoconf" "1" "--force"
# autoreconf method
else
	echo -e "using prefered method: autoreconf"
	perform "${LIBTOOLIZE}" "libtoolize" "1" "--force --copy --install"
	perform "${AUTORECONF}" "autoreconf" "1" "--force --install"
fi
echo -e "* done"

exit 0
