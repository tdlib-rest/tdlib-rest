#pragma once

#include "program_options.h"

typedef void * tdapi_client_type;
typedef const char * tdapi_json_result_type;

// Can be 0.0
// Can be 10.0
typedef const double tdapi_poll_duration_seconds_type;

void tdapi_set_log_verbosity_level(const int level);

tdapi_client_type tdapi_init (program_options_type& program_options);

void tdapi_send_request (tdapi_client_type client, const char* request_json);

// Might return nullptr
tdapi_json_result_type tdapi_poll_for_update (tdapi_client_type client, tdapi_poll_duration_seconds_type poll_duration);

void tdapi_destroy(tdapi_client_type client);
