#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_INIT([jcal], [0.5.1], [https://github.com/persiancal/jcal])

AM_INIT_AUTOMAKE
AC_PROG_LIBTOOL
AC_CONFIG_MACRO_DIR([m4])

# Checks for programs.
AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_MAKE_SET
AC_PATH_PROG(CP, cp, /bin/cp)
AC_PATH_PROG(RM, rm, /bin/rm)
AC_PATH_PROG(RMDIR, rmdir, /bin/rmdir)

# Checks for header files.
AC_CHECK_HEADERS([time.h limits.h stdlib.h string.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T
AC_STRUCT_TIMEZONE

# Checks for library functions.
AC_FUNC_MALLOC
AC_FUNC_MKTIME
AC_CHECK_FUNCS([gettimeofday localtime_r memset strcasecmp strchr strstr tzset])

AC_CONFIG_FILES([Makefile
                 libjalali/Makefile
                 test_kit/Makefile
                 test_kit/jalali/Makefile
                 test_kit/jtime/Makefile
                 man/Makefile
                 src/Makefile
                ])

AC_PATH_PROG(RM, rm, $FALSE)
RM="$RM -f"

AC_OUTPUT
