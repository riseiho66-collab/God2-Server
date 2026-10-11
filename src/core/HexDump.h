#pragma once
#include <span>
#include <string>
#include <cstdint>
namespace god2 { std::string hex_dump(std::span<const std::uint8_t> bytes); }
