#include <iostream>
#include <string>
#include <sstream> // std::stringstream
#include <td/telegram/td_json_client.h>

#include "tdlib_api.h"

void tdapi_set_log_verbosity_level(const int level) {
    std::cout << "calling tdapi_set_log_verbosity_level: level=" << level << "\n";
    std::stringstream ss;
    ss << "{\"@type\":\"setLogVerbosityLevel\",\"new_verbosity_level\":" << level << "}"; 
    td_json_client_execute(nullptr, ss.str().c_str());
    std::cout << "exited tdapi_set_log_verbosity_level().\n";
}

tdapi_client_type tdapi_init (program_options_type& program_options) {
    // configure TDLib logging
    tdapi_set_log_verbosity_level(3); //todo read from program_options.log_verbosity_level

    //create client
    std::cout << "calling td_json_client_create()...\n";
    void* client = td_json_client_create();
    std::cout << "exited from td_json_client_create().\n";
    return  client;
}

void tdapi_send_request (tdapi_client_type client, const char* request_json) {
    std::cout << "calling td_json_client_send(client, request_json='"<<request_json<<"'...\n";
    td_json_client_send(client, request_json);
    std::cout << "exited from td_json_client_send().\n";
}

tdapi_json_result_type tdapi_poll_for_update (tdapi_client_type client, tdapi_poll_duration_seconds_type poll_duration) {
    std::cout << "calling td_json_client_receive(client, poll_duration="<<poll_duration<<" seconds...\n";
    auto result = td_json_client_receive(client, poll_duration);
    std::cout << "exited td_json_client_receive(), result is '"<<result<<"'.\n";
    return result;
}

void tdapi_destroy(tdapi_client_type client) {
    std::cout << "calling td_json_client_destroy(client)...\n";
    td_json_client_destroy(client);
    std::cout << "exited td_json_client_destroy(client).\n";
}
