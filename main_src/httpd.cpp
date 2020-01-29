#include "httpd.h"
#include "httpd_worker_thread.h"

#include "tdlib_api.h"

tdapi_poll_duration_seconds_type WAIT_TIMEOUT_SECONDS = 10.0;  // double
tdapi_poll_duration_seconds_type WAIT_TIMEOUT_0_SECONDS = 0.0;  // double

// eternal loop
void httpd_init_and_loop (program_options_type& program_options) {
    //todo
}
