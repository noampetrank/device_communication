#include "marshallers.h"

template <>
MarshaledObject marshal<std::string>(const std::string &p) {
    return std::make_shared<std::string>(p);
}

template <>
std::string unmarshal<std::string>(const MarshaledObject &buf) {
    return *buf;
}
