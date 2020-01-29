#include <iostream>
#include <string>
#include <sstream> // std::stringstream
#include <td/telegram/td_json_client.h>

#include "tdlib_api.h"

inline tdapi_client_type tdapi_init (program_options_type& program_options) {
    // configure TDLib logging
    std::stringstream ss;
    ss << "{\"@type\":\"setLogVerbosityLevel\",\"new_verbosity_level\":" << 3 << "}"; //todo take from program_options.log_verbosity_level
    td_json_client_execute(nullptr, ss.str().c_str());

    //create client
    return td_json_client_create();
}

inline void tdapi_send_request (tdapi_client_type client, const char* request_json) {
    td_json_client_send(client, request_json);
}

inline tdapi_json_result_type tdapi_poll_for_update (tdapi_client_type client, tdapi_poll_duration_seconds_type poll_duration) {
    return td_json_client_receive(client, poll_duration);
}

inline void tdapi_destroy(tdapi_client_type client) {
    td_json_client_destroy(client);
}
