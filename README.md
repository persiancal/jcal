# jcal

<a href="https://repology.org/project/jcal/versions">
    <img src="https://repology.org/badge/vertical-allrepos/jcal.svg" alt="Packaging status" align="right">
</a>

Jalali calendar is a small and portable free software library to manipulate date and time in [Jalali calendar system][jalali-calendar-system].

It's written in C and has absolutely zero dependencies. It works on top of any POSIX.1-2001 (and later) compatible libc implementations. Jalali calendar provides an API similar to that of libc's timezone, date and time functions.

Jalali calendar package consists of a library namely [libjalali][libjalali] and two simple and easy to use terminal tools, `jcal` and `jdate` with functionality similar to UNIX `cal` and `date`.

---

## Install from Source

```bash
git clone https://github.com/persiancal/jcal.git
```

`cd jcal/sources`

```bash
./autogen.sh
```

The above step generates the `configure`, then invoke

```bash
./configure
```

The above step generates the `Makefile`, last step for installation invoke:

```bash
make install
```

---
This library was written and maintained by Ashkan Ghasemi, he passed away in an [accident](https://jadi.net/2017/10/ashkan-ghasemi/).
Therefore there is no way to migrate the original repository to another person, so this fork is for keep the project alive.


[jalali-calendar-system]: https://en.wikipedia.org/wiki/Jalali_calendar
[libjalali]: ./sources/libjalali/jalali.c
