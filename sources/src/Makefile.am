bin_PROGRAMS = jcal jdate

AM_CFLAGS = @CFLAGS@ -D_FILE_OFFSET_BITS=64 -D_TIME_BITS=64

jcal_SOURCES = jcal.c
jdate_SOURCES = jdate.c
LDADD           = ../libjalali/libjalali.la -L@libdir@
