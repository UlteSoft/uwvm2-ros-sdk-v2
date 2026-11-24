#include <stdlib.h>
#include <ctype.h>
#ifdef __wasilibc_unmodified_upstream // Changes to optimize printf/scanf when long double isn't needed
#else
#include "printscan.h"
#define __NEED_locale_t
#include <bits/alltypes.h>
#endif
#include "shgetc.h"
#include "floatscan.h"
#include "stdio_impl.h"

#if defined(__wasilibc_printscan_no_long_double)
static long_double strtox(const char *s, char **p, int prec)
#else
static long double strtox(const char *s, char **p, int prec)
#endif
{
	FILE f;
	sh_fromstring(&f, s);
	shlim(&f, 0);
#if defined(__wasilibc_printscan_no_long_double)
	long_double y = __floatscan(&f, prec, 1);
#else
	long double y = __floatscan(&f, prec, 1);
#endif
	off_t cnt = shcnt(&f);
	if (p) *p = cnt ? (char *)s + cnt : (char *)s;
	return y;
}

float strtof(const char *restrict s, char **restrict p)
{
	return strtox(s, p, 0);
}

/* Only the general scanner needs an addressable FILE on the Wasm stack. */
static __attribute__((__noinline__)) double strtod_slow(const char *s, char **p)
{
	return strtox(s, p, 1);
}

double strtod(const char *restrict s, char **restrict p)
{
	const unsigned char *q = (const unsigned char *)s;
	int neg = *q == '-';
	if (neg || *q == '+') q++;

	/* At most nine digits keep the significand and decimal divisor exact
	 * in both uint32_t and binary64. Division rounds the signed result once. */
	unsigned digits = 0, significand = 0, divisor = 1;
	while (isdigit(*q) && digits < 9) {
		significand = significand * 10 + (*q++ - '0');
		digits++;
	}
	if (*q == '.') {
		q++;
		while (isdigit(*q) && digits < 9) {
			significand = significand * 10 + (*q++ - '0');
			divisor *= 10;
			digits++;
		}
	}
	if (!digits || isdigit(*q) || (*q|32) == 'e' || (*q|32) == 'x')
		return strtod_slow(s, p);

	if (p) *p = (char *)q;
	double value = neg ? -(double)significand : (double)significand;
	return value / divisor;
}

long double strtold(const char *restrict s, char **restrict p)
{
#if defined(__wasilibc_printscan_no_long_double)
	long_double_not_supported();
#else
	return strtox(s, p, 2);
#endif
}
