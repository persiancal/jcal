#include "jalali.h"
#include <stdio.h>
#include <stdlib.h>

// Known leap years in the range of 1206 to 1498
int known_leap_years[] = {
    1210, 1214, 1218, 1222, 1226, 1230, 1234, 1238, 1243, 1247, 1251, 1255,
    1259, 1263, 1267, 1271, 1276, 1280, 1284, 1288, 1292, 1296, 1300, 1304,
    1309, 1313, 1317, 1321, 1325, 1329, 1333, 1337, 1342, 1346, 1350, 1354,
    1358, 1362, 1366, 1370, 1375, 1379, 1383, 1387, 1391, 1395, 1399, 1403,
    1408, 1412, 1416, 1420, 1424, 1428, 1432, 1436, 1441, 1445, 1449, 1453,
    1457, 1461, 1465, 1469, 1474, 1478, 1482, 1486, 1490, 1494, 1498};
const int num_known_leap_years =
    sizeof(known_leap_years) / sizeof(known_leap_years[0]);

int is_expected_leap(int year) {
  for (int i = 0; i < num_known_leap_years; i++) {
    if (known_leap_years[i] == year) {
      return 1;
    }
  }
  return 0;
}

int main() {
  int start_year = 1206;
  int end_year = 1498;
  int failed = 0;
  int total = 0;

  printf("Testing Jalali leap years from %d to %d...\n\n", start_year,
         end_year);

  for (int year = start_year; year <= end_year; year++) {
    int is_leap = jalali_is_jleap(year);
    int should_be_leap = is_expected_leap(year);
    total++;

    if (is_leap != should_be_leap) {
      printf("Year %d: Expected leap=%d, Leap detected=%d\n", year,
             should_be_leap, is_leap);
      failed++;
    } else if (should_be_leap) {
      printf("Year %d correctly identified as leap year\n", year);
    }
  }

  printf("\nTest Summary:\n");
  printf("Total years tested: %d\n", total);
  printf("Failed tests: %d\n", failed);
  printf("Passed tests: %d\n", total - failed);
  printf("Success rate: %.2f%%\n", ((float)(total - failed) / total) * 100);

  return failed > 0 ? 1 : 0;
}