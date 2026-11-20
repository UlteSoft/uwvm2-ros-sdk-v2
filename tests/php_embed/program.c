#include <setjmp.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include "php_embed.h"

static char output[48];
static size_t output_length;
static bool saw_log;
static jmp_buf bailout_target;
static volatile unsigned bailout_steps;

static size_t capture(const char *data, size_t size)
{
    if (size > sizeof(output) - output_length) return 0;
    memcpy(output + output_length, data, size);
    output_length += size;
    return size;
}

static void flush(void *context) {}
static void message(const char *text, int level) { saw_log = true; }
static int deactivate(void) { return SUCCESS; }

__attribute__((noinline, noreturn))
static void jump_to_bailout_target(void)
{
    ++bailout_steps;
    longjmp(bailout_target, 23);
}

static bool exercise_bailout(void)
{
    switch (setjmp(bailout_target)) {
    case 0:
        jump_to_bailout_target();
    case 23:
        return bailout_steps == 1;
    default:
        return false;
    }
}

static const char program[] =
    "(function () {"
    " $samples = [7, 11, 13, 17];"
    " $sum = 0;"
    " foreach ($samples as $reading) { $sum += $reading * 3; }"
    " try { throw new Exception('bounded'); }"
    " catch (Exception $error) { $sum += strlen($error->getMessage()); }"
    " if (getenv('WROS_PHP_HOST_ONLY') !== false || @fopen('/etc/os-release', 'rb') !== false) {"
    "   return -1;"
    " }"
    " echo 'wros-php';"
    " return $sum;"
    "})()";

void _start(void)
{
    if (!exercise_bailout()) __builtin_trap();
    if (setenv("USE_ZEND_ALLOC", "0", 1)) __builtin_trap();
    php_embed_module.ub_write = capture;
    php_embed_module.flush = flush;
    php_embed_module.log_message = message;
    php_embed_module.deactivate = deactivate;
    php_embed_module.php_ini_ignore = 1;
    php_embed_module.php_ini_ignore_cwd = 1;
    if (php_embed_init(0, NULL) != SUCCESS) __builtin_trap();

    zval value;
    ZVAL_UNDEF(&value);
    int status = zend_eval_stringl(program, sizeof(program) - 1, &value, "wros://php-probe");
    const bool passed = status == SUCCESS && Z_TYPE(value) == IS_LONG && Z_LVAL(value) == 151
        && output_length == 8 && memcmp(output, "wros-php", 8) == 0 && !saw_log;
    zval_ptr_dtor(&value);
    php_embed_shutdown();
    if (!passed) __builtin_trap();
}
