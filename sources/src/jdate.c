/*
 * jdate.c - Unix date-like interface to libjalali.
 * Copyright (C) 2006, 2007, 2009, 2010, 2011 Ashkan Ghassemi.
 *
 * This file is part of jcal.
 *
 * jcal is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * jcal is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.      See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with jcal.      If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _XOPEN_SOURCE
#define _XOPEN_SOURCE
#endif

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>

#include "../libjalali/jalali.h"
#include "../libjalali/jconfig.h"
#include "../libjalali/jtime.h"
#include "jdate.h"

#define IS_BEFORE_JALALI_EPOCH(year, month, day)                               \
  ((year) < 622 ||                                                             \
   ((year) == 622 && ((month) < 3 || ((month) == 3 && (day) < 22))))

extern char *optarg;

/*
 * Unix timestamp of last modification/access time for a file.
 * Returns 0 on success, -1 on errors.
 * Based on a given action, it returns the following values:
 * for 'a' equal zero: st_mtime (last modification time)
 * otherwise: st_atime (last access time)
 */

int mod_time(const char *path, time_t *t, int a) {
  struct stat st;
  int err;

  err = stat(path, &st);
  if (err == -1)
    return err;

  *t = (a == 0) ? st.st_mtime : st.st_atime;

  return 0;
}

int main(int argc, char **argv) {
  int opt;
  int err;
  int option_index;

  char buf[MAX_BUF_SIZE];
  char date_format[MAX_BUF_SIZE];
  char date_string[MAX_BUF_SIZE];

  struct jtm j;
  struct tm g;

  struct jdate_action action = {0};

  /* Long options, see 'jdate.h' for complete list. */
  struct option long_options[] = {{DATE_OPT, 1, 0, 'd'},
                                  {REF_OPT, 1, 0, 'r'},
                                  {ACC_OPT, 1, 0, 'a'},
                                  {RFC2822_OPT, 0, 0, 'R'},
                                  {UTC_OPT, 0, 0, 'u'},
                                  {JALALI_OPT, 1, 0, 'j'},
                                  {GREGORIAN_OPT, 1, 0, 'g'},
                                  {UNIVERSAL_OPT, 0, 0, 'u'},
                                  {HELP_OPT, 0, 0, 'h'},
                                  {VERSION_OPT, 0, 0, 'V'},
                                  {0, 0, 0, 0}};

  action.normal = 1;

  time_t t;
  time(&t);
  jlocaltime_r(&t, &j);

  while ((opt = getopt_long(argc, argv, JDATE_VALID_ARGS, long_options,
                            &option_index)) != -1) {
    switch (opt) {
      /* last access time. */
    case 'a':
      action.access = 1;
      action.access_ptr = optarg;
      break;

      /* last modification time. */
    case 'r':
      action.reference = 1;
      action.reference_ptr = optarg;
      break;

      /* display time described by FORMAT and DATE_STRING, not `now'. */
    case 'd':
      action.date = 1;
      action.date_ptr = optarg;
      break;

      /* convert a jalali date to gregorian. */
    case 'g':
      action.gregorian = 1;
      action.gregorian_ptr = optarg;
      action.utc = 1;
      break;

      /* convert a gregorian date to jalali. */
    case 'j':
      action.jalali = 1;
      action.jalali_ptr = optarg;
      action.utc = 1;
      break;

      /*
       * output date and time in RFC 2822 format.
       * %h, %m %b %Y %H:%M:%S %z
       */
    case 'R':
      action.normal = 0;
      action.format = 0;
      action.rfc2822 = 1;
      break;

      /* print Coordinated Universal Time */
    case 'u':
      action.utc = 1;
      break;

      /* help */
    case 'h':
      action.help = 1;
      action.normal = 0;
      action.format = 0;
      action.rfc2822 = 0;
      break;

      /* version */
    case 'V':
      action.version = 1;
      action.help = 0;
      action.normal = 0;
      action.format = 0;
      action.rfc2822 = 0;
      break;

    default:
      fprintf(stderr, "jdate: usage [OPTION]... [+FORMAT]\n");
      exit(EXIT_FAILURE);
    }
  }

  /*
   * Format string handler. INPUT_FORMAT and DATE_STRING
   * are separated using a semicolon. ';'
   * e.g. "%Y/%m/%d %H:%M:%S;1390/03/06 18:35:41"
   */
  for (int i = 1; i < argc; i++) {
    if (argv[i][0] == '+') {
      action.format = 1;
      action.format_ptr = &argv[i][1];
    }
  }

  /*
   *@action_handlers
   */
  if (action.jalali) {
    setenv("TZ", "Etc/UTC", 1);
    tzset();

    char *endptr_j = strptime(action.jalali_ptr, "%Y/%m/%d", &g);

    int gy = g.tm_year + 1900; // tm_year: years since 1900
    int gm = g.tm_mon + 1;     // tm_mon: 0-11 → 1-12
    int gd = g.tm_mday;

    if (!endptr_j || *endptr_j != '\0' || !is_valid_gregorian(gy, gm, gd) ||
        IS_BEFORE_JALALI_EPOCH(gy, gm, gd)) {
      fprintf(stderr,
              "Specify a Gregorian date that exists, in the following format:\n"
              "%%Y/%%m/%%d e.g. 1366/04/17\n");
      exit(EXIT_FAILURE);
    }

    if (g.tm_year < 0) { // Handle dates before 1900

      /* JDN calculation avoids system-specific mktime limitations
         by using pure mathematical conversion */
      int jdn = compute_jdn(gy, gm, gd);

      /* Epoch reference points:
         - Unix epoch: 1970-01-01 = JDN 2440588
         - 86400 seconds/day (24 * 60 * 60) */
      const long epoch_jdn = 2440588;
      long delta_days = jdn - epoch_jdn;

      /* Direct conversion to Unix time_t:
         Negative values are valid for pre-1970 dates */
      t = delta_days * 86400L; // Cast to long for 32-bit system safety
    } else {                   // for years after 1900
      g.tm_hour = 0;
      g.tm_min = 0;
      g.tm_sec = 0;

      t = mktime(&g);
    }
  } else if (action.gregorian) {
    setenv("TZ", "Etc/UTC", 1);
    tzset();

    char *endptr_g = jstrptime(action.gregorian_ptr, "%Y/%m/%d", &j);

    int jy = j.tm_year;
    int jm = j.tm_mon + 1;
    int jd = j.tm_mday;

    if (!endptr_g || *endptr_g != '\0' || !is_valid_jalali(jy, jm, jd)) {
      fprintf(stderr,
              "Specify a Jalali date that exists, in the following format:\n"
              "%%Y/%%m/%%d e.g. 2017/10/02\n");
      exit(EXIT_FAILURE);
    }

    j.tm_hour = 0;
    j.tm_min = 0;
    j.tm_sec = 0;

    t = jmktime(&j);
  }

  if (action.date) {

    char *ptr;

    ptr = strchr(action.date_ptr, ';');

    if (!ptr) {
      fprintf(stderr, "Malformed date string.");
      fprintf(stderr, " Use ';' to specify format and date string\n");
      exit(EXIT_FAILURE);
    }

    sscanf(action.date_ptr, "%[^;];%s", date_format, date_string);

    jstrptime(date_string, date_format, &j);
    jalali_update(&j);
    t = jmktime(&j);
  }

  if (action.access) {
    err = mod_time(action.access_ptr, &t, 1);

    if (err != 0) {
      fprintf(stderr, "jdate: %s: No such file or directory\n",
              action.access_ptr);
      exit(EXIT_FAILURE);
    }
  }

  if (action.reference) {
    err = mod_time(action.reference_ptr, &t, 0);

    if (err != 0) {
      fprintf(stderr, "jdate: %s: No such file or directory\n",
              action.reference_ptr);
      exit(EXIT_FAILURE);
    }
  }

  if (action.rfc2822) {
    if (!action.gregorian) {
      action.utc ? jgmtime_r(&t, &j) : jlocaltime_r(&t, &j);
      jstrftime(buf, MAX_BUF_SIZE, "%h, %d %b %Y %H:%M:%S %z", &j);
    } else {
      action.utc ? gmtime_r(&t, &g) : localtime_r(&t, &g);
      strftime(buf, MAX_BUF_SIZE, "%a, %d %b %Y %H:%M:%S %z", &g);
    }

    printf("%s\n", buf);
    exit(EXIT_SUCCESS);
  }

  if (action.format) {
    if (!action.gregorian) {
      action.utc ? jgmtime_r(&t, &j) : jlocaltime_r(&t, &j);
      jstrftime(buf, MAX_BUF_SIZE, action.format_ptr, &j);
    } else {
      action.utc ? gmtime_r(&t, &g) : localtime_r(&t, &g);
      strftime(buf, MAX_BUF_SIZE, action.format_ptr, &g);
    }

    printf("%s\n", buf);
    exit(EXIT_SUCCESS);
  }

  if (action.normal) {
    if (!action.gregorian) {
      action.utc ? jgmtime_r(&t, &j) : jlocaltime_r(&t, &j);
      jstrftime(buf, MAX_BUF_SIZE, "%h %b %d %H:%M:%S %Z %Y", &j);
    } else {
      action.utc ? gmtime_r(&t, &g) : localtime_r(&t, &g);
      strftime(buf, MAX_BUF_SIZE, "%a %b %d %H:%M:%S %Z %Y", &g);
    }

    printf("%s\n", buf);
    exit(EXIT_SUCCESS);
  }

  if (action.help) {
    printf("%s\n", HELP_STR);
    exit(EXIT_SUCCESS);
  }

  if (action.version) {
    printf("jdate %s (libjalali-%s)\n", JDATE_VERSION, LIBJALALI_VERSION);
    printf("Written by Ashkan Ghassemi.\n");
    exit(EXIT_SUCCESS);
  }

  return 0;
}
