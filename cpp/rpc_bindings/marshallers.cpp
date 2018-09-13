#include "marshallers.h"
#include "nlohmann/json.hpp"

//TODO Check if to/from_cbor is efficient (does it use intermediate JSON representation?)

template <>
MarshalledObject marshal<std::string>(const std::string &p) {
    const std::vector<std::uint8_t>& cbor = nlohmann::json::to_cbor({{"val", p}});
    return std::make_shared<Buffer>(cbor.begin(), cbor.end());
}

template <>
std::string unmarshal<std::string>(const MarshalledObject &buf) {
    std::vector<uint8_t> buf_bytes(buf->begin(), buf->end());
    const auto &json = nlohmann::json::from_cbor(buf_bytes);
    return json["val"];
}
