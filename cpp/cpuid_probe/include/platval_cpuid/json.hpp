#pragma once

#include <string>

#include "platval_cpuid/decoder.hpp"

namespace platval::cpuid {

[[nodiscard]] std::string render_json(const ProbeData& data, bool pretty);

}  // namespace platval::cpuid
