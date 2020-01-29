#include <iostream>
#include <string>
#include <sstream> // std::stringstream
#include <td/telegram/td_json_client.h>

#include "tdlib_api.h"

void tdapi_set_log_verbosity_level(const int level) {
    std::stringstream ss;
    ss << "{\"@type\":\"setLogVerbosityLevel\",\"new_verbosity_level\":" << level << "}"; 
    td_json_client_execute(nullptr, ss.str().c_str());
}

tdapi_client_type tdapi_init (program_options_type& program_options) {
    // configure TDLib logging
    tdapi_set_log_verbosity_level(3); //todo read from program_options.log_verbosity_level

    //create client
    return td_json_client_create();
}

void tdapi_send_request (tdapi_client_type client, const char* request_json) {
    td_json_client_send(client, request_json);
}

tdapi_json_result_type tdapi_poll_for_update (tdapi_client_type client, tdapi_poll_duration_seconds_type poll_duration) {
    return td_json_client_receive(client, poll_duration);
}

void tdapi_destroy(tdapi_client_type client) {
    td_json_client_destroy(client);
}
