#pragma once
#include <string>
#include <variant>
namespace god2 {
struct Error { std::string message; };
template<class T> using Result = std::variant<T, Error>;
}
