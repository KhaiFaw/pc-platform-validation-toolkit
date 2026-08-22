#include "platval_cpuid/decoder.hpp"

#include <array>
#include <cstring>

namespace platval::cpuid {
namespace {

constexpr bool bit_set(const std::uint32_t value, const unsigned int bit) noexcept {
    return (value & (std::uint32_t{1} << bit)) != 0;
}

std::string trim_cpu_string(std::string value) {
    const auto first = value.find_first_not_of(' ');
    if (first == std::string::npos) {
        return {};
    }
    const auto last = value.find_last_not_of(' ');
    value = value.substr(first, last - first + 1);
    std::string normalized;
    normalized.reserve(value.size());
    bool previous_space = false;
    for (const char character : value) {
        const bool is_space = character == ' ';
        if (!is_space || !previous_space) {
            normalized.push_back(character);
        }
        previous_space = is_space;
    }
    return normalized;
}

}  // namespace

std::string decode_vendor(const Registers& leaf_zero) {
    std::array<char, 13> vendor{};
    std::memcpy(vendor.data(), &leaf_zero.ebx, sizeof(leaf_zero.ebx));
    std::memcpy(vendor.data() + 4, &leaf_zero.edx, sizeof(leaf_zero.edx));
    std::memcpy(vendor.data() + 8, &leaf_zero.ecx, sizeof(leaf_zero.ecx));
    return std::string(vendor.data());
}

std::string decode_brand(const std::array<Registers, 3>& brand_leaves) {
    std::array<char, 49> brand{};
    std::size_t offset = 0;
    for (const auto& registers : brand_leaves) {
        for (const auto value : {registers.eax, registers.ebx, registers.ecx, registers.edx}) {
            std::memcpy(brand.data() + offset, &value, sizeof(value));
            offset += sizeof(value);
        }
    }
    return trim_cpu_string(std::string(brand.data()));
}

FeatureSet decode_features(
    const Registers& leaf_one,
    const std::optional<Registers>& leaf_seven,
    const std::optional<Registers>& extended_leaf_one,
    const bool avx_os_enabled) {
    FeatureSet result{};
    result.sse2 = bit_set(leaf_one.edx, 26);
    result.sse41 = bit_set(leaf_one.ecx, 19);
    result.sse42 = bit_set(leaf_one.ecx, 20);
    result.avx_hardware = bit_set(leaf_one.ecx, 28);
    result.aes = bit_set(leaf_one.ecx, 25);
    result.vmx = bit_set(leaf_one.ecx, 5);
    result.avx2_hardware = leaf_seven.has_value() && bit_set(leaf_seven->ebx, 5);
    result.svm = extended_leaf_one.has_value() && bit_set(extended_leaf_one->ecx, 2);
    result.avx_os_enabled = result.avx_hardware && avx_os_enabled;
    return result;
}

std::optional<CacheInfo> decode_deterministic_cache(const Registers& registers) {
    const auto type = registers.eax & 0x1FU;
    if (type == 0 || type > 3) {
        return std::nullopt;
    }

    const auto line_size = (registers.ebx & 0xFFFU) + 1U;
    const auto partitions = ((registers.ebx >> 12U) & 0x3FFU) + 1U;
    const auto ways = ((registers.ebx >> 22U) & 0x3FFU) + 1U;
    const auto sets = registers.ecx + 1U;
    const auto size = static_cast<std::uint64_t>(line_size) * partitions * ways * sets;

    return CacheInfo{
        .level = (registers.eax >> 5U) & 0x7U,
        .kind = type == 1 ? CacheKind::data
                         : (type == 2 ? CacheKind::instruction : CacheKind::unified),
        .size_bytes = size,
        .line_size_bytes = line_size,
        .sets = sets,
        .ways = ways,
        .partitions = partitions,
    };
}

const char* cache_kind_name(const CacheKind kind) noexcept {
    switch (kind) {
        case CacheKind::data:
            return "data";
        case CacheKind::instruction:
            return "instruction";
        case CacheKind::unified:
            return "unified";
    }
    return "unified";
}

}  // namespace platval::cpuid
