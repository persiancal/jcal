bin_PROGRAMS = jasctime jctime jgmtime jstrftime jstrptime jlocaltime jmktime

AM_CPPFLAGS = -I${top_srcdir}/libjalali

AM_CFLAGS = @CFLAGS@ -D_FILE_OFFSET_BITS=64 -D_TIME_BITS=64

jasctime_SOURCES = jasctime.c
jctime_SOURCES = jctime.c
jgmtime_SOURCES = jgmtime.c
jstrftime_SOURCES = jstrftime.c
jstrptime_SOURCES = jstrptime.c
jlocaltime_SOURCES = jlocaltime.c
jmktime_SOURCES = jmktime.c

LDADD           = ../../libjalali/libjalali.la -lreadline
