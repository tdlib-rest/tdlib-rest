#include <iostream> //for cerr/cout

#include <unistd.h> //for sleep()

#include <inttypes.h>
#include <string>
#include <memory>
#include <map>
#include <thread>
#include <boost/asio.hpp>
#include <sstream>

#include <iomanip>
#include <sstream>
#include <thread>
#include <memory>

#include <boost/asio.hpp>
#include <boost/bind.hpp>
#include <boost/algorithm/string.hpp>


#include "tdlib_api.h"
#include "program_options.h"
#include "http.h"
#include "httpd.h"
#include "util.h"
#include "base.h"

tdapi_poll_duration_seconds_type WAIT_TIMEOUT_SECONDS = 10.0;  // double
tdapi_poll_duration_seconds_type WAIT_TIMEOUT_0_SECONDS = 0.0;  // double

namespace http
{
	const size_t HTTP_CONNECTION_BUFFER_SIZE = 8192;
	const int TOKEN_EXPIRATION_TIMEOUT = 30; // in seconds

	class HTTPConnection: public std::enable_shared_from_this<HTTPConnection>
	{
		public:

			HTTPConnection (std::string serverhost, std::shared_ptr<boost::asio::ip::tcp::socket> socket, program_options_type program_options, tdapi_client_type tdclient);
			void Receive ();

		private:

			void HandleReceive (const boost::system::error_code& ecode, std::size_t bytes_transferred);
			void Terminate     (const boost::system::error_code& ecode);

			void RunRequest ();
			bool CheckAuth     (const HTTPReq & req);
			void HandleRequest (const HTTPReq & req);
			void HandleCommand (const HTTPReq & req, HTTPRes & res, std::stringstream& data, const URL& url, std::map<std::string, std::string>& params, const std::string& cmd);
			void SendReply     (HTTPRes & res, std::string & content);

		private:

			std::shared_ptr<boost::asio::ip::tcp::socket> m_Socket;
			char m_Buffer[HTTP_CONNECTION_BUFFER_SIZE + 1];
			size_t m_BufferLen;
			std::string m_SendBuffer;
			bool needAuth;
			std::string user;
			std::string pass;
			std::string expected_host;

            tdapi_client_type m_tdclient;

			static std::map<uint32_t, uint32_t> m_Tokens; // token->timestamp in seconds
	};

	class HTTPServer
	{
		public:

			HTTPServer (const std::string& address, int port, program_options_type program_options, tdapi_client_type tdclient);
			~HTTPServer ();

			void Start ();
			void Stop ();

		private:

			void Run ();
			void Accept ();
			void HandleAccept(const boost::system::error_code& ecode,
				std::shared_ptr<boost::asio::ip::tcp::socket> newSocket);
			void CreateConnection(std::shared_ptr<boost::asio::ip::tcp::socket> newSocket);

		private:

			bool m_IsRunning;
			std::unique_ptr<std::thread> m_Thread;
			boost::asio::io_service m_Service;
			boost::asio::io_service::work m_Work;
			boost::asio::ip::tcp::acceptor m_Acceptor;
			std::string m_Hostname;

            program_options_type m_program_options;

            tdapi_client_type m_tdclient;
	};

    void ShowJsonResponse (std::stringstream& s, std::string json_response);

	static void ShowError(std::stringstream& s, const std::string& string) {
		s << string;
	}
} // namespace http





//#ifdef WIN32_APP
//#include "Win32/Win32App.h"
//#endif

namespace http {
	const char HTTP_PAGE_SEND_REQUEST[] = "send";
	const char HTTP_PAGE_POLL_FOR_UPDATE[] = "poll";
	const char HTTP_COMMAND_LOG_LEVEL[] = "set_log_verbosity_level";

	static std::string ConvertTime (uint64_t time);

	static bool SetLogLevel (const std::string& level_str) {
        std::stringstream s(level_str);
        int level;
        s >> level;
        if (s.fail()) {
            std::cout << "httpd: set_log_verbosity_level: not an int: level='" << level_str << "'\n";
            return false;
        }

        tdapi_set_log_verbosity_level(level);
        return true;
	}

    void ShowJsonResponse (std::stringstream& s, std::string json_response) {
        s << json_response;
	}

	std::string ConvertTime (uint64_t time)
	{
		ldiv_t divTime = ldiv(time,1000);
		time_t t = divTime.quot;
		struct tm *tm = localtime(&t);
		char date[128];
		snprintf(date, sizeof(date), "%02d/%02d/%d %02d:%02d:%02d.%03ld", tm->tm_mday, tm->tm_mon + 1, tm->tm_year + 1900, tm->tm_hour, tm->tm_min, tm->tm_sec, divTime.rem);
		return date;
	}

	HTTPConnection::HTTPConnection (std::string hostname, std::shared_ptr<boost::asio::ip::tcp::socket> socket, program_options_type program_options, tdapi_client_type tdclient):
		m_Socket (socket), m_BufferLen (0), expected_host(hostname), m_tdclient(tdclient)
	{
		/* cache options */
		needAuth = false; //todo program_options.http_basic_auth;
        user = "x"; //todo program_options.http_basic_auth_username;
		pass = "x"; //todo program_options.http_basic_auth_password;
	}

	void HTTPConnection::Receive ()
	{
		m_Socket->async_read_some (boost::asio::buffer (m_Buffer, HTTP_CONNECTION_BUFFER_SIZE),
			 std::bind(&HTTPConnection::HandleReceive, shared_from_this (),
				 std::placeholders::_1, std::placeholders::_2));
	}

	void HTTPConnection::HandleReceive (const boost::system::error_code& ecode, std::size_t bytes_transferred)
	{
		if (ecode) {
			if (ecode != boost::asio::error::operation_aborted)
				Terminate (ecode);
			return;
		}
		m_Buffer[bytes_transferred] = '\0';
		m_BufferLen = bytes_transferred;
		RunRequest();
		Receive ();
	}

	void HTTPConnection::RunRequest ()
	{
        std::cout << "httpd: HTTPConnection::RunRequest\n";
		HTTPReq request;
		int ret = request.parse(m_Buffer);
		if (ret < 0) {
			m_Buffer[0] = '\0';
			m_BufferLen = 0;
            std::cerr << "httpd: HTTPConnection::RunRequest: error: bad request\n";
			return; /* error */
		}
		if (ret == 0) {
            std::cout << "httpd: HTTPConnection::RunRequest: waiting for more data\n";
			return; /* need more data */
        }

        std::cout << "httpd: HTTPConnection::RunRequest: calling HandleRequest\n";
		HandleRequest (request);
	}

	void HTTPConnection::Terminate (const boost::system::error_code& ecode)
	{
		if (ecode == boost::asio::error::operation_aborted)
			return;
		boost::system::error_code ignored_ec;
		m_Socket->shutdown(boost::asio::ip::tcp::socket::shutdown_both, ignored_ec);
		m_Socket->close ();
	}

	bool HTTPConnection::CheckAuth (const HTTPReq & req) {
		/* method #1: http://user:pass@127.0.0.1:7070/ */
		if (req.uri.find('@') != std::string::npos) {
			URL url;
			if (url.parse(req.uri) && url.user == user && url.pass == pass)
				return true;
		}
		/* method #2: 'Authorization' header sent */
		auto provided = req.GetHeader ("Authorization");
		if (provided.length () > 0)
		{
			std::string expected = "Basic " + data::ToBase64Standard (user + ":" + pass);
			if (expected == provided) return true;
		}

		std::cerr << "HTTPServer: auth failure from " << m_Socket->remote_endpoint().address () << "\n";
		return false;
	}

	void HTTPConnection::HandleRequest (const HTTPReq & req) {
		std::cout << "httpd: HTTPConnection::HandleRequest entered\n";

		std::stringstream s;
		std::string content;
		HTTPRes res;

		std::cout << "httpd: HTTPConnection::HandleRequest: request.uri: " << req.uri << "\n";

		if (needAuth && !CheckAuth(req)) {
			res.code = 401;
			res.add_header("WWW-Authenticate", "Basic realm=\"tdlib-rest\"");
			SendReply(res, content);
			return;
		}
		const bool strictheaders = false;
		//config::GetOption("http.strictheaders", strictheaders);
		if (strictheaders)
		{
			std::string http_hostname;
			//todo config::GetOption("http.hostname", http_hostname);
			std::string host = req.GetHeader("Host");
			auto idx = host.find(':');
			/* strip out port so it's just host */
			if (idx != std::string::npos && idx > 0)
			{
				host = host.substr(0, idx);
			}
			if (!(host == expected_host || host == http_hostname))
			{
				/* deny request as it's from a non whitelisted hostname */
				res.code = 403;
				content = "{\"error\":\"host-header-mismatch\"}";
				SendReply(res, content);
				return;
			}
		}
	    std::map<std::string, std::string> params;
	    URL url;

	    url.parse(req.uri);
	    url.parse_query(params);
  		std::string request = params["request"];
		std::cout << "httpd: request='"<<request<<"'\n";
        if(request == HTTP_COMMAND_LOG_LEVEL) {
			HandleCommand (req, res, s, url, params, request);
		} else {
            if(request == HTTP_PAGE_SEND_REQUEST) { 
          		std::string request_json = http::UrlDecode(params["request_json"]);
        		std::cout << "httpd: request_json='"<<request_json<<"'\n";
                tdapi_send_request (m_tdclient, request_json.c_str());
                ShowJsonResponse (s, "{\"ok\":true}");
            } else {
                if(request == HTTP_PAGE_POLL_FOR_UPDATE) {
                    // Might return nullptr
                    auto json_result = tdapi_poll_for_update (m_tdclient, WAIT_TIMEOUT_0_SECONDS);
                    if (!json_result) {
                        json_result = "{\"is_empty\":true}";
                    }
                    ShowJsonResponse (s, json_result); 
                } else {
			        res.code = 400;
            		std::cerr << "httpd: Error: Unknown request='"<<request<<"'\n";
			        ShowError(s, "{\"error\": \"unknown_request\"}");
            		content = s.str ();
            		SendReply (res, content);
			        return;
                }
            }
		}

		content = s.str ();
   		std::cerr << "httpd: sending HTTP 200, content='"<<content<<"'\n";
		res.code = 200;
		SendReply (res, content);
	}

	std::map<uint32_t, uint32_t> HTTPConnection::m_Tokens;

	void HTTPConnection::HandleCommand (const HTTPReq& req, HTTPRes& res, std::stringstream& s, const URL& url, std::map<std::string, std::string>& params, const std::string& cmd)
	{
		if (cmd == HTTP_COMMAND_LOG_LEVEL) {
			auto level = params["level"];
			bool ok = SetLogLevel (level);
    		if(ok) {
                res.code = 200;
                s << "{\"ok\":true}";
            } else {
    			res.code = 400;
       			ShowError(s, "{\"error\": \"invalid-level\"}");
            }
		} else {
			res.code = 400;
			ShowError(s, "{\"error\": \"unknown-request\"}");
		}
		auto content = s.str ();
		SendReply (res, content);
	}

	void HTTPConnection::SendReply (HTTPRes& reply, std::string& content)
	{
		reply.add_header("X-Frame-Options", "SAMEORIGIN");
		reply.add_header("Content-Type", "text/json");
		reply.body = content;

		m_SendBuffer = reply.to_string();
		boost::asio::async_write (*m_Socket, boost::asio::buffer(m_SendBuffer),
			std::bind (&HTTPConnection::Terminate, shared_from_this (), std::placeholders::_1));
	}

	HTTPServer::HTTPServer (const std::string& address, int port, program_options_type program_options, tdapi_client_type tdclient):
		m_IsRunning (false), m_Thread (nullptr), m_Work (m_Service),
		m_Acceptor (m_Service, boost::asio::ip::tcp::endpoint (boost::asio::ip::address::from_string(address), port)),
		m_Hostname(address), m_program_options(program_options), m_tdclient(tdclient)
	{
	}

	HTTPServer::~HTTPServer ()
	{
		Stop ();
	}

	void HTTPServer::Start ()
	{
		//bool needAuth=false; //todo config::GetOption("http.auth", needAuth);
		//std::string user=""; //todo config::GetOption("http.user", user);
		//std::string pass=""; //todo config::GetOption("http.pass", pass);
		m_IsRunning = true;
		m_Thread = std::unique_ptr<std::thread>(new std::thread (std::bind (&HTTPServer::Run, this)));
		m_Acceptor.listen ();
		Accept ();
	}

	void HTTPServer::Stop ()
	{
		m_IsRunning = false;
		m_Acceptor.close();
		m_Service.stop ();
		if (m_Thread)
		{
			m_Thread->join ();
			m_Thread = nullptr;
		}
	}

	void HTTPServer::Run ()
	{
		while (m_IsRunning)
		{
			try
			{
				m_Service.run ();
			}
			catch (std::exception& ex)
			{
				std::cerr << "httpd.run: runtime exception: " << ex.what () << "\n";
			}
		}
	}

	void HTTPServer::Accept ()
	{
		auto newSocket = std::make_shared<boost::asio::ip::tcp::socket> (m_Service);
		m_Acceptor.async_accept (*newSocket, boost::bind (&HTTPServer::HandleAccept, this,
			boost::asio::placeholders::error, newSocket));
	}

	void HTTPServer::HandleAccept(const boost::system::error_code& ecode,
		std::shared_ptr<boost::asio::ip::tcp::socket> newSocket)
	{
		if (ecode)
		{
			if(newSocket) newSocket->close();
			std::cerr << "httpd: error handling accept " << ecode.message() << "\n";
			if(ecode != boost::asio::error::operation_aborted)
				Accept();
			return;
		}
        std::cout << "httpd: new_conn\n";
		CreateConnection(newSocket);
		Accept ();
	}

	void HTTPServer::CreateConnection(std::shared_ptr<boost::asio::ip::tcp::socket> newSocket)
	{
		auto conn = std::make_shared<HTTPConnection> (m_Hostname, newSocket, m_program_options, m_tdclient);
		conn->Receive ();
	}
} // http


//td

// eternal loop
void httpd_init_and_loop (program_options_type& program_options) {
    auto port = 12222;
    auto host = "127.0.0.1";

    std::cout << "Starting tdapi...\n";
    tdapi_client_type client = tdapi_init (program_options);
    std::cout << "Started tdapi.\n";

    std::cout << "Starting httpd on host '"<<host<<"', port "<<port<<"...\n";
    http::HTTPServer httpd (host, port, program_options, client); //todo read port and host from program_options
    httpd.Start ();
    std::cout << "Started httpd. Entering httpd eternal loop...\n";
    while(true) {
        sleep(60); //seconds
    }

    //std::cout << "Stopping httpd...\n";
    //httpd.Stop ();
    //std::cout << "httpd exited.\n";
}

