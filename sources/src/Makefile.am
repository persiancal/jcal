bin_PROGRAMS = jcal jdate

AM_CPPFLAGS = -I${top_srcdir} -I${top_srcdir}/libjalali -I@includedir@

AM_CFLAGS = @CFLAGS@ -fno-inline -Wall\
	-D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE

jcal_SOURCES = jcal.c
jdate_SOURCES = jdate.c
LDADD           = ../libjalali/libjalali.la -L@libdir@
