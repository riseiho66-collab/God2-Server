#include "net/WebClientGateway.h"
#include <algorithm>
#include <array>
#include <cctype>
#include <deque>
#include <map>
#include <set>
#include <span>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <utility>
#ifdef _WIN32
#include <windows.h>
#include <bcrypt.h>
#endif

namespace god2 {
namespace {
using Bytes=std::vector<std::uint8_t>;
using Tcp=asio::ip::tcp;
using Clock=std::chrono::steady_clock;
#include "net/WebSocketHandshake.inc"
bool utf8(std::span<const std::uint8_t> s) {
    for(std::size_t i=0;i<s.size();) {
        const auto b=s[i++];if(b<128)continue;
        unsigned n=0,value=0,minimum=0;
        if(b>=0xC2&&b<=0xDF){n=1;value=b&31;minimum=128;}
        else if(b>=0xE0&&b<=0xEF){n=2;value=b&15;minimum=2048;}
        else if(b>=0xF0&&b<=0xF4){n=3;value=b&7;minimum=65536;}
        else return false;
        if(s.size()-i<n)return false;
        while(n--){const auto c=s[i++];if((c&0xC0)!=0x80)return false;value=(value<<6)|(c&63);}
        if(value<minimum||value>0x10FFFF||(value>=0xD800&&value<=0xDFFF))return false;
    }return true;
}
bool valid_close(const Bytes& p) {
    if(p.empty())return true;if(p.size()==1)return false;
    const auto code=(unsigned(p[0])<<8)|p[1];
    if(!((code>=1000&&code<=1014&&code!=1004&&code!=1005&&code!=1006)||(code>=3000&&code<=4999)))return false;
    return utf8(std::span<const std::uint8_t>(p).subspan(2));
}
std::optional<std::uint8_t> indexed_channel(std::string_view path) {
    constexpr std::string_view prefix="/tw/native-game/";
    if(path.size()==prefix.size()+1&&path.starts_with(prefix)&&path.back()>='0'&&path.back()<='2')
        return static_cast<std::uint8_t>(path.back()-'0');
    return {};
}
std::string json_string(std::string_view text) {
    std::string result="\"";
    constexpr char digits[]="0123456789abcdef";
    for(const unsigned char c:text) {
        if(c=='\"'||c=='\\'){result.push_back('\\');result.push_back(static_cast<char>(c));}
        else if(c<32){result+="\\u00";result.push_back(digits[c>>4]);result.push_back(digits[c&15]);}
        else result.push_back(static_cast<char>(c));
    }
    result.push_back('\"');return result;
}
bool set_deadline(asio::steady_timer& timer,std::chrono::seconds duration) {
    // Policy validation guarantees the conversion. A later clock near its
    // representable end still must not overflow when adding that duration.
    const auto delta=std::chrono::duration_cast<Clock::duration>(duration);
    const auto now=Clock::now();
    if(now.time_since_epoch().count()>Clock::duration::max().count()-delta.count())return false;
    timer.expires_at(now+delta);return true;
}
}
void validate_web_gateway_policy(const WebGatewayPolicy& policy) {
    constexpr auto largest_timeout=std::chrono::duration_cast<std::chrono::seconds>(Clock::duration::max());
    if(!policy.listen.address().is_loopback()||policy.origins.empty()||
       !policy.max_sessions||!policy.sessions_per_address||!policy.accepts_per_second||
       !policy.message_bytes||policy.message_bytes>16*1024*1024||policy.queue_bytes<65546||
       !policy.queue_frames||!policy.frames_per_second||!policy.bytes_per_second||
       policy.handshake_timeout.count()<=0||policy.idle_timeout.count()<=0||
       policy.message_timeout.count()<=0||policy.close_timeout.count()<=0||
       policy.handshake_timeout>largest_timeout||policy.idle_timeout>largest_timeout||
       policy.message_timeout>largest_timeout||policy.close_timeout>largest_timeout)
        throw std::invalid_argument("Web gateway requires explicit loopback/origin/budgets");
    std::set<std::string> origins;
    for(const auto& origin:policy.origins)
        if((!origin.starts_with("http://")&&!origin.starts_with("https://"))||
           origin.find_first_of("\r\n \t")!=std::string::npos||
           std::any_of(origin.begin(),origin.end(),[](unsigned char c){return c<32||c==127;})||
           !origins.insert(origin).second)
            throw std::invalid_argument("Web gateway Origin must be explicit and unique");
}
void validate_web_native_routes(std::span<const WebNativeRoute> routes) {
    if(routes.empty()||routes.size()>4)
        throw std::invalid_argument("Web gateway requires bounded actual native routes");
    std::set<std::string> paths;
    std::vector<Tcp::endpoint> endpoints;
    std::optional<std::uint8_t> group;
    std::array<bool,3> indexed{};
    bool account=false,legacy=false,has_indexed=false;
    for(const auto& route:routes) {
        const auto channel=indexed_channel(route.path);
        if((route.path!="/tw/native"&&route.path!="/tw/native-game"&&!channel)||
           !route.endpoint.port()||route.endpoint.address().is_unspecified()||
           !paths.insert(route.path).second||
           std::find(endpoints.begin(),endpoints.end(),route.endpoint)!=endpoints.end())
            throw std::invalid_argument("Web gateway requires unique fixed assigned native routes");
        endpoints.push_back(route.endpoint);
        if(channel) {
            if(!route.group||!route.subgroup||*route.group>=10||*route.subgroup!=*channel||
               (group&&group!=route.group))
                throw std::invalid_argument("Web channel metadata must match its actual fixed route");
            group=route.group;indexed[*channel]=true;has_indexed=true;
        } else {
            if(route.group||route.subgroup)
                throw std::invalid_argument("Legacy web paths cannot invent channel metadata");
            if(route.path=="/tw/native")account=true;else legacy=true;
        }
    }
    if(has_indexed&&(!account||legacy||routes.size()!=4||
       !std::all_of(indexed.begin(),indexed.end(),[](bool value){return value;})))
        throw std::invalid_argument("Web channels require account and all three actual G endpoints");
}
std::string web_native_routes_manifest(std::span<const WebNativeRoute> routes) {
    validate_web_native_routes(routes);
    const bool account=std::any_of(routes.begin(),routes.end(),[](const auto& route){return route.path=="/tw/native";});
    std::vector<const WebNativeRoute*> games;
    for(const auto& route:routes)if(route.path!="/tw/native")games.push_back(&route);
    std::sort(games.begin(),games.end(),[](const auto* a,const auto* b){return a->path<b->path;});
    std::string result="{\"version\":1,\"account\":";
    result+=account?"{\"path\":\"/tw/native\"}":"null";
    result+=",\"games\":[";
    bool comma=false;
    for(const auto* route:games) {
        if(comma)result.push_back(',');comma=true;
        result+="{\"path\":"+json_string(route->path)+",\"native_address\":"+
            json_string(route->endpoint.address().to_string())+",\"native_port\":"+std::to_string(route->endpoint.port());
        if(route->group)result+=",\"group\":"+std::to_string(*route->group)+",\"subgroup\":"+std::to_string(*route->subgroup);
        result.push_back('}');
    }
    result+="]}";
    if(result.size()>4096)throw std::invalid_argument("Web native route metadata exceeds its fixed budget");
    return result;
}
struct WebClientGateway::State:std::enable_shared_from_this<State> {
    struct Peer;
    asio::strand<asio::io_context::executor_type> strand;
    Tcp::acceptor acceptor;
    asio::steady_timer retry;
    const WebGatewayPolicy policy;
    const std::vector<WebNativeRoute> routes;
    const std::string manifest;
    std::set<std::shared_ptr<Peer>> peers;
    std::map<asio::ip::address,std::size_t> addresses;
    Clock::time_point accept_window=Clock::now();
    std::size_t accepted=0;
    std::uint16_t bound_port=0;
    bool started=false,stopping=false;
    State(asio::io_context& io,WebGatewayPolicy p,std::vector<WebNativeRoute> r)
        :strand(asio::make_strand(io)),acceptor(strand),retry(strand),policy(std::move(p)),routes(std::move(r)),
         manifest(web_native_routes_manifest(routes)) {
        validate_web_gateway_policy(policy);
        for(const auto& route:routes)if(route.endpoint==policy.listen)
            throw std::invalid_argument("Web/native listener endpoint conflict");
        acceptor.open(policy.listen.protocol());acceptor.bind(policy.listen);acceptor.listen();
        bound_port=acceptor.local_endpoint().port();
        for(const auto& route:routes)
            if(route.endpoint.port()==bound_port)throw std::invalid_argument("Web/native listener port conflict");
    }
    void accept();
    void stop();
};
struct WebClientGateway::State::Peer:std::enable_shared_from_this<Peer> {
    struct Write {std::shared_ptr<const Bytes> bytes;bool terminal=false;};
    std::weak_ptr<State> owner;
    const WebGatewayPolicy policy;
    const asio::ip::address address;
    Tcp::socket browser,native;
    asio::steady_timer timeout,message_deadline;
    asio::streambuf input{8192};
    std::array<std::uint8_t,65536> native_input{};
    std::deque<Write> writes;
    std::size_t queued=0,frames=0,bytes=0;
    Clock::time_point window=Clock::now();
    bool closed=false,closing=false,fragmented=false,native_reading=false;
    Bytes fragment;
    Peer(std::shared_ptr<State> s,Tcp::socket socket,asio::ip::address a)
        :owner(s),policy(s->policy),address(a),browser(std::move(socket)),native(s->strand),
         timeout(s->strand),message_deadline(s->strand) {}
    void close() {
        if(closed)return;closed=true;
        asio::error_code ec;
        try{timeout.cancel();}catch(...){}
        try{message_deadline.cancel();}catch(...){}
        browser.cancel(ec);browser.close(ec);native.cancel(ec);native.close(ec);
        writes.clear();fragment.clear();queued=0;
        if(auto s=owner.lock()){
            auto it=s->addresses.find(address);if(it!=s->addresses.end()&&!--it->second)s->addresses.erase(it);
            s->peers.erase(shared_from_this());
        }
    }
    bool arm(std::chrono::seconds duration) {
        try {
            if(!set_deadline(timeout,duration)){close();return false;}
            timeout.async_wait([self=shared_from_this()](const asio::error_code& ec){if(!ec)self->close();});
            return true;
        }catch(...){close();return false;}
    }
    void begin() {
        if(!arm(policy.handshake_timeout))return;
        asio::error_code ec;browser.set_option(Tcp::no_delay(true),ec);
        asio::async_read_until(browser,input,"\r\n\r\n",[self=shared_from_this()](const asio::error_code& ec,std::size_t n){
            if(self->closed)return;if(ec){self->close();return;}
            try{self->request(n);}catch(...){self->close();}
        });
    }
    void reject(unsigned status,const char* label) {
        if(closed)return;closing=true;
        auto data=std::make_shared<std::string>("HTTP/1.1 "+std::to_string(status)+" "+label+
            "\r\nContent-Length: 0\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n");
        asio::async_write(browser,asio::buffer(*data),[self=shared_from_this(),data](const asio::error_code&,std::size_t){self->close();});
    }
    void send_manifest(const std::shared_ptr<State>& state,const std::optional<std::string>& origin) {
        closing=true;if(!arm(policy.close_timeout))return;
        auto reply=std::make_shared<std::string>("HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n"
            "Cache-Control: no-store\r\nConnection: close\r\nContent-Length: "+std::to_string(state->manifest.size())+"\r\n");
        if(origin)*reply+="Access-Control-Allow-Origin: "+*origin+"\r\nVary: Origin\r\n";
        *reply+="\r\n"+state->manifest;
        // Metadata never opens a native socket. The small immutable response
        // is retained through its one write and then the browser peer closes.
        asio::async_write(browser,asio::buffer(*reply),[self=shared_from_this(),reply](const asio::error_code&,std::size_t){self->close();});
    }
    void request(std::size_t n) {
        auto s=owner.lock();if(!s){close();return;}
        std::string header(n,'\0');std::istream stream(&input);stream.read(header.data(),static_cast<std::streamsize>(n));
        if(header.find('\0')!=std::string::npos){reject(400,"Bad Request");return;}
        std::istringstream lines(header);std::string line,method,path,version,extra;
        std::getline(lines,line);std::istringstream first(line);first>>method>>path>>version;
        if(method!="GET"||version!="HTTP/1.1"||(first>>extra)){reject(400,"Bad Request");return;}
        std::map<std::string,std::string> fields;
        while(std::getline(lines,line)&&line!="\r") {
            const auto colon=line.find(':');
            if(colon==std::string::npos||colon==0||line.front()==' '||line.front()=='\t') {reject(400,"Bad Request");return;}
            const auto key=lower(line.substr(0,colon));
            if(key.find_first_of(" \t\r\n")!=std::string::npos||!fields.emplace(key,trim(line.substr(colon+1))).second){reject(400,"Bad Request");return;}
        }
        if(fields["host"].empty()||fields.contains("transfer-encoding")||
           (fields.contains("content-length")&&fields["content-length"]!="0")) {reject(400,"Bad Request");return;}
        if(path=="/tw/native-routes") {
            if(input.size()||fields.contains("upgrade")||fields.contains("sec-websocket-key")||
               fields.contains("sec-websocket-version")||fields.contains("sec-websocket-protocol")||
               fields.contains("sec-websocket-extensions")||token(fields["connection"],"upgrade")) {
                reject(400,"Bad Request");return;
            }
            std::optional<std::string> origin;
            if(const auto found=fields.find("origin");found!=fields.end()) {
                if(std::find(policy.origins.begin(),policy.origins.end(),found->second)==policy.origins.end()){
                    reject(403,"Forbidden");return;
                }
                origin=found->second;
            }
            send_manifest(s,origin);return;
        }
        if(lower(fields["upgrade"])!="websocket"||!token(fields["connection"],"upgrade")||
           fields["sec-websocket-version"]!="13"||!nonce(fields["sec-websocket-key"])) {
            reject(400,"Bad Request");return;
        }
        if(std::find(policy.origins.begin(),policy.origins.end(),fields["origin"])==policy.origins.end()){reject(403,"Forbidden");return;}
        // Exact targets only: no query host/port, redirects, DNS or path decoding.
        auto route=std::find_if(s->routes.begin(),s->routes.end(),[&](const auto& r){return r.path==path;});
        if(route==s->routes.end()){reject(404,"Not Found");return;}
        const auto key=fields["sec-websocket-key"];
        native.async_connect(route->endpoint,[self=shared_from_this(),key](const asio::error_code& ec){
            if(self->closed)return;if(ec){self->reject(503,"Service Unavailable");return;}
            try {
                asio::error_code ignored;self->native.set_option(Tcp::no_delay(true),ignored);
                auto reply=std::make_shared<std::string>("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "+accept_key(key)+"\r\n\r\n");
                asio::async_write(self->browser,asio::buffer(*reply),[self,reply](const asio::error_code& error,std::size_t){
                    if(self->closed)return;if(error){self->close();return;}
                    if(!self->arm(self->policy.idle_timeout))return;
                    self->read_header();self->read_native();
                });
            }catch(...){self->close();}
        });
    }
    template<class Handler> void take(std::size_t size,Handler handler) {
        if(closed||closing)return;
        auto data=std::make_shared<Bytes>(size);const auto buffered=std::min(size,input.size());
        if(buffered){std::istream stream(&input);stream.read(reinterpret_cast<char*>(data->data()),static_cast<std::streamsize>(buffered));}
        if(buffered==size){
            // Queue buffered transitions: never recurse through a pipeline of frames.
            asio::post(browser.get_executor(),[self=shared_from_this(),data,handler=std::move(handler)]()mutable{
                if(!self->closed&&!self->closing)handler(std::move(data));
            });return;
        }
        asio::async_read(browser,asio::buffer(data->data()+buffered,size-buffered),
            [self=shared_from_this(),data,handler=std::move(handler)](const asio::error_code& ec,std::size_t)mutable{
                if(self->closed||self->closing)return;if(ec){self->close();return;}handler(std::move(data));
            });
    }
    void finish(Bytes payload) {
        if(closed||closing)return;closing=true;fragment.clear();message_deadline.cancel();
        asio::error_code ec;native.cancel(ec);native.close(ec);if(!arm(policy.close_timeout))return;
        enqueue(8,std::move(payload),true);
    }
    void fail(std::uint16_t code) {finish(Bytes{static_cast<std::uint8_t>(code>>8),static_cast<std::uint8_t>(code)});}
    bool charge(std::size_t n) {
        const auto now=Clock::now();if(now-window>=std::chrono::seconds(1)){window=now;frames=0;bytes=0;}
        if(frames>=policy.frames_per_second||n>policy.bytes_per_second-bytes){fail(1008);return false;}
        ++frames;bytes+=n;return true;
    }
    void read_header() {
        take(2,[self=shared_from_this()](auto h){
            const auto first=(*h)[0],second=(*h)[1];const auto op=first&15;const bool fin=(first&128)!=0;
            if((first&0x70)||!(second&128)||!(op==0||op==2||op==8||op==9||op==10)||
               (op>=8&&(!fin||(second&127)>125))||
               (op==0&&!self->fragmented)||(op==2&&self->fragmented)){self->fail(1002);return;}
            const auto len=second&127;if(len<126){self->read_payload(first,len);return;}
            self->take(len==126?2:8,[self,first,len](auto ext){
                std::uint64_t size=0;for(auto b:*ext)size=(size<<8)|b;
                if((len==126&&size<126)||(len==127&&(size<65536||((*ext)[0]&128)))){self->fail(1002);return;}
                if(size>self->policy.message_bytes){self->fail(1009);return;}
                self->read_payload(first,static_cast<std::size_t>(size));
            });
        });
    }
    void read_payload(std::uint8_t first,std::size_t n) {
        const auto op=first&15;const bool fin=(first&128)!=0;
        if(op<8&&(n>policy.message_bytes-fragment.size())){fail(1009);return;}
        if(!charge(n))return;
        if(op==2) {
            try {
                if(!set_deadline(message_deadline,policy.message_timeout)){close();return;}
                message_deadline.async_wait([self=shared_from_this()](const asio::error_code& ec){if(!ec)self->fail(1008);});
            }catch(...){close();return;}
        }
        take(n+4,[self=shared_from_this(),op,fin,n](auto raw){
            if(!self->arm(self->policy.idle_timeout))return;
            Bytes payload(n);
            for(std::size_t i=0;i<n;++i)payload[i]=(*raw)[i+4]^(*raw)[i&3];
            if(op==8){if(!valid_close(payload)){self->fail(1002);return;}self->finish(std::move(payload));return;}
            if(op==9){self->enqueue(10,std::move(payload));self->read_header();return;}
            if(op==10){self->read_header();return;}
            self->fragment.insert(self->fragment.end(),payload.begin(),payload.end());self->fragmented=!fin;
            if(!fin){self->read_header();return;}
            // WS message boundary does not delimit native packets. The native
            // receiver owns framing; each full message contributes stream bytes.
            auto data=std::make_shared<Bytes>(std::move(self->fragment));self->fragment.clear();
            asio::async_write(self->native,asio::buffer(*data),[self,data](const asio::error_code& ec,std::size_t){
                if(self->closed||self->closing)return;if(ec){self->fail(1011);return;}
                self->message_deadline.cancel();self->read_header();
            });
        });
    }
    void enqueue(std::uint8_t op,Bytes payload,bool terminal=false) {
        if(closed||(!terminal&&closing))return;
        Bytes frame{static_cast<std::uint8_t>(128|op)};const auto n=payload.size();
        if(n<126)frame.push_back(static_cast<std::uint8_t>(n));
        else if(n<65536){frame.push_back(126);frame.push_back(static_cast<std::uint8_t>(n>>8));frame.push_back(static_cast<std::uint8_t>(n));}
        else{frame.push_back(127);for(int shift=56;shift>=0;shift-=8)frame.push_back(static_cast<std::uint8_t>(std::uint64_t(n)>>shift));}
        frame.insert(frame.end(),payload.begin(),payload.end());
        if(frame.size()>policy.queue_bytes-queued||writes.size()>=policy.queue_frames){close();return;}
        const bool idle=writes.empty();queued+=frame.size();writes.push_back({std::make_shared<const Bytes>(std::move(frame)),terminal});
        if(idle)write();
    }
    void write() {
        if(closed||writes.empty())return;const auto item=writes.front();
        asio::async_write(browser,asio::buffer(*item.bytes),[self=shared_from_this(),item](const asio::error_code& ec,std::size_t){
            if(self->closed)return;if(ec||item.terminal){self->close();return;}
            self->queued-=item.bytes->size();self->writes.pop_front();self->write();self->read_native();
        });
    }
    void read_native() {
        // Reserve room for one worst-case TCP read plus its WS header. Suspend
        // native reads when the browser stalls rather than buffer without bound.
        if(closed||closing||native_reading||policy.queue_bytes-queued<65546||writes.size()>=policy.queue_frames)return;
        native_reading=true;
        native.async_read_some(asio::buffer(native_input),[self=shared_from_this()](const asio::error_code& ec,std::size_t n){
            self->native_reading=false;if(self->closed||self->closing)return;
            if(n){self->enqueue(2,Bytes(self->native_input.begin(),self->native_input.begin()+n));if(!self->arm(self->policy.idle_timeout))return;}
            if(ec){self->fail(ec==asio::error::eof?1001:1011);return;}self->read_native();
        });
    }
};
void WebClientGateway::State::accept() {
    if(stopping)return;
    acceptor.async_accept(strand,[self=shared_from_this()](const asio::error_code& ec,Tcp::socket socket){
        if(self->stopping)return;
        if(ec){self->retry.expires_after(std::chrono::milliseconds(250));self->retry.async_wait([self](const asio::error_code& error){if(!error)self->accept();});return;}
        const auto now=Clock::now();if(now-self->accept_window>=std::chrono::seconds(1)){self->accept_window=now;self->accepted=0;}
        asio::error_code error;const auto address=socket.remote_endpoint(error).address();
        const auto it=self->addresses.find(address);const auto count=it==self->addresses.end()?0:it->second;
        if(!error&&self->accepted<self->policy.accepts_per_second&&self->peers.size()<self->policy.max_sessions&&count<self->policy.sessions_per_address){
            ++self->accepted;
            auto peer=std::make_shared<Peer>(self,std::move(socket),address);self->peers.insert(peer);++self->addresses[address];
            try{peer->begin();}catch(...){peer->close();}
        }
        self->accept();
    });
}
void WebClientGateway::State::stop() {
    if(stopping)return;stopping=true;asio::error_code ec;acceptor.close(ec);
    try{retry.cancel();}catch(...){}
    // close() removes its exact peer. Avoid allocating a second peer set while
    // retiring an already resource-bounded listener.
    while(!peers.empty()){const auto peer=*peers.begin();peer->close();}
}
WebClientGateway::WebClientGateway(asio::io_context& io,WebGatewayPolicy p,std::vector<WebNativeRoute> r)
    :state_(std::make_shared<State>(io,std::move(p),std::move(r))) {}
WebClientGateway::~WebClientGateway(){stop();}
void WebClientGateway::start(){asio::post(state_->strand,[s=state_]{if(s->started||s->stopping)return;s->started=true;s->accept();});}
void WebClientGateway::stop(){asio::post(state_->strand,[s=state_]{s->stop();});}
std::uint16_t WebClientGateway::port()const noexcept{return state_->bound_port;}
}
