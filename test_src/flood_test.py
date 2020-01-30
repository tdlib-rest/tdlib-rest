#!/usr/bin/env python3

import requests, json
from urllib.parse import quote as urlencode
from time import sleep

import local_vars

TEST_DC_BOOL_STR="false"
tdhost = local_vars.tdlib_rest_hostname_str
tdport = local_vars.tdlib_rest_port_str

def clamp(i, a, b):
    minimum = min (a, b)
    maximum = max (a, b)
    ret = max (i, minimum)
    return min (ret, maximum)

def cooljson(somejson):
    return json.dumps(somejson, indent=2, sort_keys=True)

def http_request(http_method, request_url):
    url = "http://%s:%s%s" % (tdhost,tdport,request_url,)
    if http_method == "post":
        resp = requests.post(url, data = None)
        print()
        print("resp.text: '%s'" % resp.text)
        print()
        resp_json = json.loads(resp.text)
        print("resp json: %s" % cooljson(resp_json))
        print()
        return resp_json
    else: raise Error("unknown http method: '%s'" % http_method)

def td_json_client_send(client, request_json):
    print("calling td_json_client_send, json='%s'" % cooljson(json.loads(request_json)))
    resp_json = http_request ("post", "/?request=send&request_json=%s" % urlencode(request_json))
    if "ok" in resp_json and resp_json["ok"]: return
    else: raise Error("send failed: %s" % cooljson(resp_json))

def td_json_client_execute(client, json):
    print("not-impl: td_json_client_execute, json='%s'" % json)

#no-op
def td_json_client_create():
    return None

def td_json_client_receive(client, wait_timeout):
    print("calling td_json_client_receive, wait_timeout=%s" % wait_timeout)
    resp_json = http_request ("post", "/?request=poll") # todo use wait_timeout??
    if "is_empty" in resp_json and resp_json["is_empty"]:
        print("sleeping %s seconds..." % wait_timeout)
        sleep(wait_timeout)
        return None
    return resp_json

#no-op
def td_json_client_destroy(client):
    pass
    

def sendTdlibParameters(client):
    td_json_client_send(client, "{\"@type\":\"setTdlibParameters\", \"@extra\":1, \"parameters\":{\"@type\":\"tdlibParameters\", \"use_test_dc\":%s, \"use_file_database\":true, \"use_chat_info_database\":true, \"use_message_database\":true, \"api_id\":%s, \"api_hash\":\"%s\", \"system_language_code\":\"%s\", \"device_model\":\"unknown\", \"system_version\":\"unknown\", \"application_version\":\"https://github.com/tdlib-rest/tdlib-rest/test_src/flood_test.py/unknown-version\", \"ignore_file_names\":false, \"enable_storage_optimizer\":true}}" % (TEST_DC_BOOL_STR, local_vars.LOCAL_API_ID_STR,local_vars.LOCAL_API_HASH_STR,local_vars.LOCAL_LANG_CODE,))

def sendDbEncryptionKey(client):
    td_json_client_send(client, "{\"@type\":\"checkDatabaseEncryptionKey\", \"@extra\":1, \"encryption_key\":\"%s\"}" % local_vars.LOCAL_DB_ENCRYPTION_KEY_STR)

def sendBotHashAuth(client):
    td_json_client_send(client, "{\"@type\":\"checkAuthenticationBotToken\", \"@extra\":2, \"token\":\"%s\"}" % local_vars.LOCAL_BOT_TOKEN_STR)

def main():
    # enable TDLib logging
    td_json_client_execute(None, "{\"@type\":\"setLogVerbosityLevel\", \"new_verbosity_level\":3}")

    client = td_json_client_create()

    #td_json_client_send(client, "{\"@type\":\"setProxy\", \"@extra\":1, \"proxy\":{\"@type\":\"proxySocks5\", \"server\":\"" LOCAL_SOCKS5_HOSTNAME_STR "\", \"port\":" LOCAL_SOCKS5_PORT_STR ", \"username\":\"" LOCAL_SOCKS5_USERNAME_STR "\",  \"password\":\"" LOCAL_SOCKS5_PASSWORD_STR "\"}}")
    #error { code = 400, message = "Failed to parse JSON object as TDLib request: Unknown class "setProxy"" }

    td_json_client_send(client, "{\"@type\":\"addProxy\", \"@extra\":1, \"server\":\"%s\", \"port\":%s, \"enable\":true, \"type\":{\"@type\":\"proxyTypeSocks5\", \"username\":\"%s\",  \"password\":\"%s\"}}" % (local_vars.LOCAL_SOCKS5_HOSTNAME_STR,local_vars.LOCAL_SOCKS5_PORT_STR,local_vars.LOCAL_SOCKS5_USERNAME_STR,local_vars.LOCAL_SOCKS5_PASSWORD_STR,))

    test_incorrect_queries = False
    if test_incorrect_queries:
        td_json_client_execute(None, "{\"@type\":\"setLogVerbosityLevel\", \"new_verbosity_level\":3}")
        td_json_client_execute(None, "")
        td_json_client_execute(None, "test")
        td_json_client_execute(None, "\"test\"")
        td_json_client_execute(None, "{\"@type\":\"test\", \"@extra\":1}")

        td_json_client_send(client, "{\"@type\":\"getFileMimeType\"}")
        td_json_client_send(client, "{\"@type\":\"getFileMimeType\", \"@extra\":1}")
        td_json_client_send(client, "{\"@type\":\"getFileMimeType\", \"@extra\":null}")
        td_json_client_send(client, "{\"@type\":\"test\"}")
        td_json_client_send(client, "[]")
        td_json_client_send(client, "{\"@type\":\"test\", \"@extra\":1}")
        td_json_client_send(client, "{\"@type\":\"sendMessage\", \"chat_id\":true, \"@extra\":1}")
        td_json_client_send(client, "test")

    WAIT_TIMEOUT = 1.0 # seconds
    while True:
        result = td_json_client_receive(client, WAIT_TIMEOUT)
        if result:
            #if (result is UpdateAuthorizationState with authorizationStateClosed) {
            #   break
            #}
            print("result: '%s'" % cooljson(result))
            res_type = result["@type"]
            if res_type == "updateAuthorizationState":
                authorization_state=result["authorization_state"]
                auth_type=authorization_state["@type"]
                if auth_type == "authorizationStateWaitTdlibParameters":
                    sendTdlibParameters(client)
                    continue
                if auth_type == "authorizationStateWaitEncryptionKey":
                    sendDbEncryptionKey(client)
                    continue
                if auth_type == "authorizationStateWaitPhoneNumber":
                    sendBotHashAuth(client)
                    continue
                if auth_type == "authorizationStateReady":
                    print("\n\n\n\n\nLOGGED_IN\n\n\n\n\n")
                    td_json_client_send(client, "{\"@type\":\"sendMessage\", \"chat_id\":%s, \"@extra\":3, \"input_message_content\":{\"@type\":\"inputMessageText\", \"text\":{\"@type\":\"formattedText\",\"text\":\"td flood test py bot logged in\"}}}" % local_vars.LOCAL_CHAT_ID_STR)
                    continue 

                print("unknown auth state update, exiting.")
                break

            """
            {
              "@type": "updateNewMessage",
              "message": {
                "@type": "message",
                "author_signature": "",
                "can_be_deleted_for_all_users": false,
                "can_be_deleted_only_for_self": false,
                "can_be_edited": false,
                "can_be_forwarded": true,
                "chat_id": 123,
                "contains_unread_mention": false,
                "content": {
                  "@type": "messageText",
                  "text": {
                    "@type": "formattedText",
                    "entities": [],
                    "text": "some ping"
                  }
                },
                "date": 1580340018,
                "edit_date": 0,
                "id": 2513436672,
                "is_channel_post": false,
                "is_outgoing": false,
                "media_album_id": "0",
                "reply_to_message_id": 0,
                "restriction_reason": "",
                "sender_user_id": 123,
                "ttl": 0,
                "ttl_expires_in": 0.0,
                "via_bot_user_id": 0,
                "views": 0
              }
            }
            """
            if res_type=="updateNewMessage":
                msg = result["message"]
                if not msg["is_outgoing"]:# and not "messageSendingStatePending" in result:
                    sender_user_id = msg["sender_user_id"]
                    if int(local_vars.LOCAL_BOT_USER_ID_STR) != int(sender_user_id): #skip messages from self
                        reply_with_text = True
                        if "content" in msg:
                            content = msg["content"]
                            content_at_type = content["@type"]
                            if "text" in content:
                                content_text = content["text"]
                                if "text" in content_text:
                                    msg_text = content_text["text"]
                                    reply_text = "A message received with text `\"%s\"`" % msg_text
                                else:
                                    reply_text = "Some message received with no `text` field in `content.text`, `content.text`=`\"%s\"`" % json.dumps(content_text)
                            else:
                                #reply_text = "Some message received with no `text` field in `content`"
                                if content_at_type == "messageSticker":
                                    try:
                                        input_message_content = {
                                            "@type": "inputMessageSticker", # https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1input_message_sticker.html#a32993a144616da02b107492376eae63a
                                            "sticker": {
                                                "@type": "inputFileRemote",
                                                "id": content["sticker"]["sticker"]["remote"]["id"]
                                            },
                                            "thumbnail": {
                                                "@type": "inputThumbnail",
                                                "width": int(content["sticker"]["thumbnail"]["width"]*0.5),
                                                "height": int(content["sticker"]["thumbnail"]["height"]*0.5),
                                                "thumbnail": {
                                                    "@type": "inputFileRemote",
                                                    "id": content["sticker"]["thumbnail"]["photo"]["remote"]["id"]
                                                }
                                            },
                                            "width": content["sticker"]["width"],
                                            "height": content["sticker"]["height"]
                                        }
                                        reply_with_text = False
                                    except Exception as ex:
                                        print ("Exception while `Failed to format `inputMessageSticker` in reply to incoming `messageSticker``:", ex)
                                        from traceback import print_exc as tb
                                        tb()
                                        reply_with_text = True
                                        reply_text = "Failed to format `inputMessageSticker` in reply to incoming `messageSticker`"
                        else:
                            reply_text = "Some message received with no `content` field in `message`"
                        if reply_with_text:
                            input_message_content = {
                                "@type": "inputMessageText", 
                                "text": {
                                    "@type":"formattedText",
                                    "text": reply_text
                                }
                            }
                        reply = {
                            "@type": "sendMessage",
                            "chat_id": local_vars.LOCAL_CHAT_ID_STR,
                            "@extra": 3,
                            "input_message_content": input_message_content,
                        }
                        td_json_client_send(client, json.dumps(reply))
                        continue
            if res_type=="updateMessageSendFailed":
                try:
                    code = int ( result ["error_code"] )
                    error_message = result ["error_message"]
                    prefix = "FLOOD_WAIT_"
                    """
                        for (auto prefix :
                             {Slice("FLOOD_WAIT_"), Slice("SLOWMODE_WAIT_"), Slice("2FA_CONFIRM_WAIT_"), Slice("TAKEOUT_INIT_DELAY_")}) {
                          if (begins_with(msg, prefix)) {
                            timeout = clamp(to_integer<int>(msg.substr(prefix.size())), 1, 14 * 24 * 60 * 60);
                            break;
                          }
                        }
                    """
                    if code == 429 and error_message.startswith(prefix): # todo also implement the above C++ code here
                        seconds = clamp (int (error_message [len(prefix) : ]), 1, 14 * 24 * 60 * 60)
                        print ("updateMessageSendFailed: 429 %s, sleeping %s sec." % ( error_message, str(seconds), ) )
                        sleep(seconds)
                        timewait_sec = seconds
                    else:
                        timewait_sec = float (result["message"]["sending_state"]["retry_after"])
                        print ("updateMessageSendFailed: %s %s, sleeping %s sec." % ( str(code), error_message, str(timewait_sec) ))
                        sleep(timewait_sec)
                    if result["message"]["sending_state"]["can_retry"]:
                        msg_text = result["message"]["content"]["text"]["text"]
                        retry_sendmsg_request = { 
                            "@type": "sendMessage", 
                            "chat_id": result["message"]["chat_id"], 
                            "@extra": 4, 
                            "input_message_content": {
                                "@type": "inputMessageText", 
                                "text": {
                                    "@type":"formattedText",
                                    "text": """[overslept after sleeping %s seconds; redelivery after error %s %s]; failed msg text:

%s""" % (
                                        str(timewait_sec), str(code), error_message, msg_text
                                    )
                                }
                            } 
                        }
                        td_json_client_send(client, json.dumps(retry_sendmsg_request))
                except Exception as ex:
                    print("Exception:", ex, "sleeping infinity")
                    while True: sleep(10*3600) #one hour
            """
            updateMessageSendFailed {
              message = message {
                id = 2592079874
                sender_user_id = 680736482
                chat_id = -1001289380798
                sending_state = messageSendingStateFailed {
                  error_code = 429
                  error_message = "Too Many Requests: retry after 4"
                  can_retry = true
                  retry_after = 3.999928
                }
                scheduling_state = null
                is_outgoing = true
                can_be_edited = false
                can_be_forwarded = true
                can_be_deleted_only_for_self = true
                can_be_deleted_for_all_users = false
                is_channel_post = false
                contains_unread_mention = false
                date = 1580341008
                edit_date = 0
                forward_info = null
                reply_to_message_id = 0
                ttl = 0
                ttl_expires_in = 0.000000
                via_bot_user_id = 0
                author_signature = ""
                views = 0
                media_album_id = 0
                restriction_reason = ""
                content = messageText {
                  text = formattedText {
                    text = "some message received with text 'ы'"
                    entities = vector[0] {
                    }
                  }
                  web_page = null
                }
                reply_markup = null
              }
              old_message_id = 2592079873
              error_code = 429
              error_message = "Too Many Requests: retry after 4"
            }

            // after hypn-dirty-fix at NetQueryDispatcher.cpp :
            {
              "@type": "updateMessageSendFailed",
              "error_code": 429,
              "error_message": "FLOOD_WAIT_4",
              "message": {
                "@type": "message",
                "author_signature": "",
                "can_be_deleted_for_all_users": false,
                "can_be_deleted_only_for_self": true,
                "can_be_edited": false,
                "can_be_forwarded": true,
                "chat_id": 123,
                "contains_unread_mention": false,
                "content": {
                  "@type": "messageText",
                  "text": {
                    "@type": "formattedText",
                    "entities": [],
                    "text": "td flood test py bot logged in"
                  }
                },
                "date": 1580350693,
                "edit_date": 0,
                "id": 3711959570,
                "is_channel_post": false,
                "is_outgoing": true,
                "media_album_id": "0",
                "reply_to_message_id": 0,
                "restriction_reason": "",
                "sender_user_id": 123,
                "sending_state": {
                  "@type": "messageSendingStateFailed",
                  "can_retry": true,
                  "error_code": 429,
                  "error_message": "FLOOD_WAIT_4",
                  "retry_after": 0.0
                },
                "ttl": 0,
                "ttl_expires_in": 0.0,
                "via_bot_user_id": 0,
                "views": 0
              },
              "old_message_id": 3711959569
            }
            """
    td_json_client_destroy(client)

main()
