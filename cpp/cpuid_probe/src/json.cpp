#include "platval_cpuid/json.hpp"

#include <iomanip>
#include <sstream>
#include <string_view>

#include "platval_cpuid/version.hpp"

namespace platval::cpuid {
namespace {

std::string escape_json(const std::string_view input) {
    std::ostringstream output;
    for (const unsigned char character : input) {
        switch (character) {
            case '"':
                output << "\\\"";
                break;
            case '\\':
                output << "\\\\";
                break;
            case '\b':
                output << "\\b";
                break;
            case '\f':
                output << "\\f";
                break;
            case '\n':
                output << "\\n";
                break;
            case '\r':
                output << "\\r";
                break;
            case '\t':
                output << "\\t";
                break;
            default:
                if (character < 0x20) {
                    output << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                           << static_cast<unsigned int>(character) << std::dec;
                } else {
                    output << character;
                }
        }
    }
    return output.str();
}

const char* boolean(const bool value) noexcept { return value ? "true" : "false"; }

}  // namespace

std::string render_json(const ProbeData& data, const bool pretty) {
    const std::string newline = pretty ? "\n" : "";
    const std::string one = pretty ? "  " : "";
    const std::string two = pretty ? "    " : "";
    std::ostringstream output;
    output << '{' << newline;
    output << one << "\"schema_version\":" << (pretty ? " " : "") << schema_version << ','
           << newline;
    output << one << "\"probe_version\":" << (pretty ? " " : "") << '"' << probe_version << "\","
           << newline;
    output << one << "\"architecture\":" << (pretty ? " " : "") << '"'
           << escape_json(data.architecture) << "\"," << newline;
    output << one << "\"vendor_id\":" << (pretty ? " " : "") << '"'
           << escape_json(data.vendor_id) << "\"," << newline;
    output << one << "\"brand_string\":" << (pretty ? " " : "");
    if (data.brand_string.has_value()) {
        output << '"' << escape_json(*data.brand_string) << '"';
    } else {
        output << "null";
    }
    output << ',' << newline;
    output << one << "\"max_basic_leaf\":" << (pretty ? " " : "") << data.max_basic_leaf << ','
           << newline;
    output << one << "\"max_extended_leaf\":" << (pretty ? " " : "")
           << data.max_extended_leaf << ',' << newline;
    output << one << "\"features\":" << (pretty ? " " : "") << '{' << newline;
    output << two << "\"sse2\":" << (pretty ? " " : "") << boolean(data.features.sse2) << ','
           << newline;
    output << two << "\"sse41\":" << (pretty ? " " : "") << boolean(data.features.sse41) << ','
           << newline;
    output << two << "\"sse42\":" << (pretty ? " " : "") << boolean(data.features.sse42) << ','
           << newline;
    output << two << "\"avx_hardware\":" << (pretty ? " " : "")
           << boolean(data.features.avx_hardware) << ',' << newline;
    output << two << "\"avx2_hardware\":" << (pretty ? " " : "")
           << boolean(data.features.avx2_hardware) << ',' << newline;
    output << two << "\"avx_os_enabled\":" << (pretty ? " " : "")
           << boolean(data.features.avx_os_enabled) << ',' << newline;
    output << two << "\"aes\":" << (pretty ? " " : "") << boolean(data.features.aes) << ','
           << newline;
    output << two << "\"vmx\":" << (pretty ? " " : "") << boolean(data.features.vmx) << ','
           << newline;
    output << two << "\"svm\":" << (pretty ? " " : "") << boolean(data.features.svm) << ','
           << newline;
    output << two << "\"virtualization_hardware\":" << (pretty ? " " : "")
           << boolean(data.features.virtualization_hardware()) << newline;
    output << one << "}," << newline;
    output << one << "\"caches\":" << (pretty ? " " : "") << '[';
    if (!data.caches.empty()) {
        output << newline;
    }
    for (std::size_t index = 0; index < data.caches.size(); ++index) {
        const auto& cache = data.caches[index];
        output << two << '{'
               << "\"level\":" << cache.level << ','
               << "\"kind\":\"" << cache_kind_name(cache.kind) << "\","
               << "\"size_bytes\":" << cache.size_bytes << ','
               << "\"line_size_bytes\":" << cache.line_size_bytes << ','
               << "\"sets\":" << cache.sets << ','
               << "\"ways\":" << cache.ways << ','
               << "\"partitions\":" << cache.partitions << '}';
        if (index + 1 < data.caches.size()) {
            output << ',';
        }
        output << newline;
    }
    if (!data.caches.empty()) {
        output << one;
    }
    output << ']' << newline << '}' << newline;
    return output.str();
}

}  // namespace platval::cpuid
