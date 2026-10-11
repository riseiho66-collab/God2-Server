// Public RFC6455 checksum helpers, derived from the pinned frontend candidate.
std::string base64(std::span<const std::uint8_t> input) {
    constexpr char alphabet[]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string out;
    for(std::size_t i=0;i<input.size();i+=3){const auto n=std::min<std::size_t>(3,input.size()-i);
        const auto v=(unsigned(input[i])<<16)|(n>1?unsigned(input[i+1])<<8:0)|(n>2?input[i+2]:0);
        out+=alphabet[(v>>18)&63];out+=alphabet[(v>>12)&63];out+=n>1?alphabet[(v>>6)&63]:'=';out+=n>2?alphabet[v&63]:'=';
    }return out;
}
std::string accept_key(const std::string& key) {
    // RFC6455 SHA1 is a public upgrade checksum, never password hashing.
    const auto input=key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA1_ALGORITHM,nullptr,0)<0)throw std::runtime_error("WebSocket SHA1 unavailable");
    struct Close {BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE& h;~Close(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}} close{algorithm,hash};
    DWORD length=0,got=0;
    if(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&length),sizeof(length),&got,0)<0)throw std::runtime_error("WebSocket hash properties failed");
    Bytes object(length);std::array<std::uint8_t,20> result{};
    if(BCryptCreateHash(algorithm,&hash,object.data(),length,nullptr,0,0)<0 ||
       BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(input.data())),static_cast<ULONG>(input.size()),0)<0 ||
       BCryptFinishHash(hash,result.data(),static_cast<ULONG>(result.size()),0)<0)throw std::runtime_error("WebSocket hash failed");
    return base64(result);
#else
    throw std::runtime_error("Web gateway SHA1 provider requires Windows BCrypt");
#endif
}
std::string lower(std::string value){for(auto& c:value)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return value;}
std::string trim(std::string value){const auto first=value.find_first_not_of(" \t\r\n"),last=value.find_last_not_of(" \t\r\n");return first==std::string::npos?std::string{}:value.substr(first,last-first+1);}
bool token(const std::string& value,const std::string& expected){std::istringstream stream(lower(value));std::string part;while(std::getline(stream,part,','))if(trim(part)==expected)return true;return false;}
bool nonce(const std::string& value){
    if(value.size()!=24||value.substr(22)!="=="||std::string("AQgw").find(value[21])==std::string::npos)return false;
    return std::all_of(value.begin(),value.begin()+22,[](unsigned char c){return (c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='+'||c=='/';});
}
