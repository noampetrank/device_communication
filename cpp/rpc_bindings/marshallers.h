#ifndef CPP_MARSHALLERS_H
#define CPP_MARSHALLERS_H

#include <memory>
#include <string>
#include "../rpc_bindings/remote_procedure_execution.h"


template <>
MarshalledObject marshal<std::string>(const std::string &p);

template <>
std::string unmarshal<std::string>(const MarshalledObject &buf);

#endif //CPP_MARSHALLERS_H
