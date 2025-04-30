#include <stdio.h>
#include <time.h>

#include <readline/history.h>
#include <readline/readline.h>

#include "jalali.h"
#include "jtime.h"

int main() {
  setlocale_from_env();

  char *s;
  char *fmt;
  s = readline("string > ");
  fmt = readline("format > ");
  struct jtm j;
  jstrptime(s, fmt, &j);
  jalali_show_time(&j);
  return 0;
}
