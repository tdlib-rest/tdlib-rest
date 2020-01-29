
import local_vars

TEST_DC_BOOL_STR="false"

def td_json_client_send(client, json):
    print("td_json_client_send, json='%s'" % json)

def sendTdlibParameters(client) {
    td_json_client_send(client, "{\"@type\":\"setTdlibParameters\", \"@extra\":1, \"parameters\":{\"@type\":\"tdlibParameters\", \"use_test_dc\":%s, \"use_file_database\":true, \"use_chat_info_database\":true, \"use_message_database\":true, \"api_id\":%s, \"api_hash\":\"%s\", \"system_language_code\":\"%s\", \"device_model\":\"unknown\", \"system_version\":\"unknown\", \"application_version\":\"https://github.com/tdlib-rest/tdlib-rest/cpp-json-example/unknown-version\", \"ignore_file_names\":false, \"enable_storage_optimizer\":true}}" % (TEST_DC_BOOL_STR, local_vars.LOCAL_API_ID_STR,local_vars.LOCAL_API_HASH_STR,local_vars.LOCAL_LANG_CODE,));
}

void sendDbEncryptionKey(void *client) {
    td_json_client_send(client, "{\"@type\":\"checkDatabaseEncryptionKey\", \"@extra\":1, \"encryption_key\":\"" LOCAL_DB_ENCRYPTION_KEY_STR "\"}");
}

void sendBotHashAuth(void *client) {
    td_json_client_send(client, "{\"@type\":\"checkAuthenticationBotToken\", \"@extra\":2, \"token\":\"" LOCAL_BOT_TOKEN_STR "\"}");
}

int main() {
    // enable TDLib logging
    td_json_client_execute(nullptr, "{\"@type\":\"setLogVerbosityLevel\", \"new_verbosity_level\":3}");

    void *client = td_json_client_create();
    // somehow share the client with other threads, which will be able to send requests via td_json_client_send

    //td_json_client_send(client, "{\"@type\":\"setProxy\", \"@extra\":1, \"proxy\":{\"@type\":\"proxySocks5\", \"server\":\"" LOCAL_SOCKS5_HOSTNAME_STR "\", \"port\":" LOCAL_SOCKS5_PORT_STR ", \"username\":\"" LOCAL_SOCKS5_USERNAME_STR "\",  \"password\":\"" LOCAL_SOCKS5_PASSWORD_STR "\"}}");
    //error { code = 400, message = "Failed to parse JSON object as TDLib request: Unknown class "setProxy"" }

    td_json_client_send(client, "{\"@type\":\"addProxy\", \"@extra\":1, \"server\":\"" LOCAL_SOCKS5_HOSTNAME_STR "\", \"port\":" LOCAL_SOCKS5_PORT_STR ", \"enable\":true, \"type\":{\"@type\":\"proxyTypeSocks5\", \"username\":\"" LOCAL_SOCKS5_USERNAME_STR "\",  \"password\":\"" LOCAL_SOCKS5_PASSWORD_STR "\"}}");

    const bool test_incorrect_queries = false;
    if (test_incorrect_queries) {
        td_json_client_execute(nullptr, "{\"@type\":\"setLogVerbosityLevel\", \"new_verbosity_level\":3}");
        td_json_client_execute(nullptr, "");
        td_json_client_execute(nullptr, "test");
        td_json_client_execute(nullptr, "\"test\"");
        td_json_client_execute(nullptr, "{\"@type\":\"test\", \"@extra\":1}");

        td_json_client_send(client, "{\"@type\":\"getFileMimeType\"}");
        td_json_client_send(client, "{\"@type\":\"getFileMimeType\", \"@extra\":1}");
        td_json_client_send(client, "{\"@type\":\"getFileMimeType\", \"@extra\":null}");
        td_json_client_send(client, "{\"@type\":\"test\"}");
        td_json_client_send(client, "[]");
        td_json_client_send(client, "{\"@type\":\"test\", \"@extra\":1}");
        td_json_client_send(client, "{\"@type\":\"sendMessage\", \"chat_id\":true, \"@extra\":1}");
        td_json_client_send(client, "test");
    }

    const double WAIT_TIMEOUT = 10.0;  // seconds
    while (true) {
        const char *result = td_json_client_receive(client, WAIT_TIMEOUT);
        if (result != nullptr) {
          // parse the result as a JSON object and process it as an incoming update or an answer to a previously sent request

          //if (result is UpdateAuthorizationState with authorizationStateClosed) {
          //   break;
          //}
            std::cout << result << std::endl;
            auto result_str = std::string(result);
            //todo parse json
            if(result_str.find("\"updateAuthorizationState\"")!=std::string::npos) {
                if(result_str.find("\"authorizationStateWaitTdlibParameters\"")!=std::string::npos) { sendTdlibParameters(client); continue; }
                if(result_str.find("\"authorizationStateWaitEncryptionKey\"")!=std::string::npos) { sendDbEncryptionKey(client); continue; }
                if(result_str.find("\"authorizationStateWaitPhoneNumber\"")!=std::string::npos) { sendBotHashAuth(client); continue; }
                if(result_str.find("\"authorizationStateReady\"")!=std::string::npos) {
                    std::cout << "\n\n\n\n\nLOGGED_IN\n\n\n\n\n"; 
                    td_json_client_send(client, "{\"@type\":\"sendMessage\", \"chat_id\":" LOCAL_CHAT_ID_STR ", \"@extra\":3, \"input_message_content\":{\"@type\":\"inputMessageText\", \"text\":{\"@type\":\"formattedText\",\"text\":\"td example c++ bot logged in\"}}}");
                    continue; 
                }

                std::cout << "unknown auth state update, exiting." << std::endl;
                break;
            }

            //{"@type":"updateNewMessage","message":{"@type":"message","id":123,"sender_user_id":123,"chat_id":123,"is_outgoing":false,"can_be_edited":false,"can_be_forwarded":true,"can_be_deleted_only_for_self":false,"can_be_deleted_for_all_users":false,"is_channel_post":false,"contains_unread_mention":false,"date":123,"edit_date":0,"reply_to_message_id":0,"ttl":0,"ttl_expires_in":0.000000,"via_bot_user_id":0,"author_signature":"","views":0,"media_album_id":"0","restriction_reason":"","content":{"@type":"messageText","text":{"@type":"formattedText","text":"msg text","entities":[]}}}}
            if(result_str.find("\"updateNewMessage\"")!=std::string::npos && 
                result_str.find("\"is_outgoing\":true")==std::string::npos && 
                result_str.find("messageSendingStatePending")==std::string::npos) {
                    auto clause = std::string("\"sender_user_id\":")+LOCAL_BOT_USER_ID_STR;
                    if(result_str.find(clause)!=std::string::npos)continue; //skip messages from self
                    size_t index_text = result_str.find("{\"@type\":\"formattedText\",\"text\"");
                    size_t index_text2 = index_text==std::string::npos?std::string::npos:result_str.find(":", index_text+1);//skip "text"
                    size_t index_text3 = index_text2==std::string::npos?std::string::npos:result_str.find("\"", index_text2+1);//skip :
                    size_t index_text4 = index_text3==std::string::npos?std::string::npos:index_text3+1; //skip opening "
                    size_t index_text5 = index_text4==std::string::npos?std::string::npos:result_str.find("\"", index_text4);//find closing "
                    size_t len = index_text4==std::string::npos||index_text5==std::string::npos?0:index_text5-index_text4;
                    if(index_text4==std::string::npos||index_text5==std::string::npos || len<0) {
                        std::cout << "\ncannot parse or is not a text message, sending static msg\n";
                        //td_json_client_send(client, "{\"@type\":\"sendMessage\", \"chat_id\":" LOCAL_CHAT_ID_STR ", \"@extra\":3, \"input_message_content\":{\"@type\":\"inputMessageText\", \"text\":{\"@type\":\"formattedText\",\"text\":\"some message received; cannot parse or is not a text message\"}}}");
                        continue;
                    }
                    std::cout << "\nextracted some text, sending it as text msg\n";
                    
                    auto json_message = std::string("{\"@type\":\"sendMessage\", \"chat_id\":" LOCAL_CHAT_ID_STR ", \"@extra\":3, \"input_message_content\":{\"@type\":\"inputMessageText\", \"text\":{\"@type\":\"formattedText\",\"text\":\"some message received with text '")+result_str.substr(/*pos*/index_text4, len)+"'\"}}}";
                    //td_json_client_send(client, json_message.c_str());
                    continue;
            }
        }
    }

    td_json_client_destroy(client);
}
