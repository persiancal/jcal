bin_PROGRAMS = elc get_date get_diff jalali_update jyinfo leap sec_converter

AM_CPPFLAGS = -I${top_srcdir}/libjalali

AM_CFLAGS = @CFLAGS@ -D_FILE_OFFSET_BITS=64 -D_TIME_BITS=64

elc_SOURCES = elc.c
get_date_SOURCES = get_date.c
get_diff_SOURCES = get_diff.c
jalali_update_SOURCES = jalali_update.c
jyinfo_SOURCES = jyinfo.c
leap_SOURCES = leap.c
sec_converter_SOURCES = sec_converter.c

LDADD           = ../../libjalali/libjalali.la
