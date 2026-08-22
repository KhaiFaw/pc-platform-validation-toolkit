#include <cstdint>
#include <iostream>
#include <optional>
#include <string>

#include "platval_cpuid/decoder.hpp"
#include "platval_cpuid/json.hpp"

namespace {

int failures = 0;

void expect(const bool condition, const std::string& message) {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        ++failures;
    }
}

}  // namespace

int main() {
    using platval::cpuid::Registers;

    const Registers vendor{
        .eax = 7,
        .ebx = 0x756E6547U,
        .ecx = 0x6C65746EU,
        .edx = 0x49656E69U,
    };
    expect(platval::cpuid::decode_vendor(vendor) == "GenuineIntel", "vendor byte ordering");

    Registers leaf_one{};
    leaf_one.edx = 1U << 26U;
    leaf_one.ecx = (1U << 5U) | (1U << 19U) | (1U << 20U) | (1U << 25U) | (1U << 28U);
    Registers leaf_seven{};
    leaf_seven.ebx = 1U << 5U;
    Registers extended_one{};
    extended_one.ecx = 1U << 2U;
    const auto features = platval::cpuid::decode_features(
        leaf_one, std::optional{leaf_seven}, std::optional{extended_one}, true);
    expect(features.sse2 && features.sse41 && features.sse42, "SSE feature bits");
    expect(features.avx_hardware && features.avx2_hardware, "AVX hardware bits");
    expect(features.avx_os_enabled, "operating-system AVX state");
    expect(features.aes, "AES feature bit");
    expect(features.vmx && features.svm && features.virtualization_hardware(), "virtualization bits");

    const Registers cache{
        .eax = 3U | (3U << 5U),
        .ebx = 63U | (7U << 22U),
        .ecx = 1023U,
        .edx = 0,
    };
    const auto decoded_cache = platval::cpuid::decode_deterministic_cache(cache);
    expect(decoded_cache.has_value(), "deterministic cache is present");
    if (decoded_cache.has_value()) {
        expect(decoded_cache->level == 3, "cache level");
        expect(decoded_cache->size_bytes == 524288U, "cache size calculation");
        expect(decoded_cache->line_size_bytes == 64, "cache line size");
        expect(decoded_cache->ways == 8, "cache associativity");
    }
    expect(!platval::cpuid::decode_deterministic_cache(Registers{}).has_value(),
           "null cache terminates enumeration");

    if (decoded_cache.has_value()) {
        platval::cpuid::ProbeData probe_data{};
        probe_data.architecture = "x86_64";
        probe_data.vendor_id = "GenuineIntel";
        probe_data.brand_string = "Synthetic CPU";
        probe_data.max_basic_leaf = 7;
        probe_data.max_extended_leaf = 0x80000004U;
        probe_data.features = features;
        probe_data.caches.push_back(*decoded_cache);
        const auto json = platval::cpuid::render_json(probe_data, false);
        expect(json.find("\"schema_version\":1") != std::string::npos, "JSON schema version");
        expect(json.find("\"vendor_id\":\"GenuineIntel\"") != std::string::npos,
               "JSON vendor field");
        expect(json.find("\"avx_os_enabled\":true") != std::string::npos,
               "JSON operating-system AVX field");
        expect(json.find("\"size_bytes\":524288") != std::string::npos, "JSON cache field");
    }

    if (failures == 0) {
        std::cout << "decoder tests passed\n";
    }
    return failures == 0 ? 0 : 1;
}
