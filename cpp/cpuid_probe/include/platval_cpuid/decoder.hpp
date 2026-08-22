#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "platval_cpuid/cpuid_access.hpp"

namespace platval::cpuid {

enum class CacheKind { data, instruction, unified };

struct CacheInfo {
    std::uint32_t level{};
    CacheKind kind{};
    std::uint64_t size_bytes{};
    std::uint32_t line_size_bytes{};
    std::uint32_t sets{};
    std::uint32_t ways{};
    std::uint32_t partitions{};
};

struct FeatureSet {
    bool sse2{};
    bool sse41{};
    bool sse42{};
    bool avx_hardware{};
    bool avx2_hardware{};
    bool avx_os_enabled{};
    bool aes{};
    bool vmx{};
    bool svm{};

    [[nodiscard]] bool virtualization_hardware() const noexcept { return vmx || svm; }
};

struct ProbeData {
    std::string architecture;
    std::string vendor_id;
    std::optional<std::string> brand_string;
    std::uint32_t max_basic_leaf{};
    std::uint32_t max_extended_leaf{};
    FeatureSet features;
    std::vector<CacheInfo> caches;
};

[[nodiscard]] std::string decode_vendor(const Registers& leaf_zero);
[[nodiscard]] std::string decode_brand(const std::array<Registers, 3>& brand_leaves);
[[nodiscard]] FeatureSet decode_features(
    const Registers& leaf_one,
    const std::optional<Registers>& leaf_seven,
    const std::optional<Registers>& extended_leaf_one,
    bool avx_os_enabled);
[[nodiscard]] std::optional<CacheInfo> decode_deterministic_cache(const Registers& registers);
[[nodiscard]] const char* cache_kind_name(CacheKind kind) noexcept;

}  // namespace platval::cpuid
