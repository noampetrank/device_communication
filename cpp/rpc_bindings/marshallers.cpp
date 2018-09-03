#include "marshallers.h"

template <>
MarshalledObject marshal<std::string>(const std::string &p) {
    return std::make_shared<std::string>(p);
}

template <>
std::string unmarshal<std::string>(const MarshalledObject &buf) {
    return *buf;
}
