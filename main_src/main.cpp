#include "program_options.h"
#include "httpd.h"

int main (int argc, char *argv[]) {
    auto program_options = program_options_init (argc, argv);

    // eternal loop
    httpd_init_and_loop (program_options);
}
