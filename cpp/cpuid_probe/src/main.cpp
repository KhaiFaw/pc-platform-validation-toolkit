#include <array>
#include <cstdint>
#include <exception>
#include <iostream>
#include <optional>
#include <string_view>

#include "platval_cpuid/cpuid_access.hpp"
#include "platval_cpuid/decoder.hpp"
#include "platval_cpuid/json.hpp"
#include "platval_cpuid/version.hpp"

namespace {

constexpr int exit_unsupported_architecture = 2;
constexpr int exit_invalid_arguments = 3;
constexpr int exit_internal_failure = 4;

platval::cpuid::ProbeData collect_probe_data() {
    using platval::cpuid::CpuidAccess;
    const auto basic = CpuidAccess::read(0);
    const auto extended = CpuidAccess::read(0x80000000U);

    platval::cpuid::ProbeData data{};
    data.architecture = platval::cpuid::compiled_architecture();
    data.vendor_id = platval::cpuid::decode_vendor(basic);
    data.max_basic_leaf = basic.eax;
    data.max_extended_leaf = extended.eax;

    if (data.max_extended_leaf >= 0x80000004U) {
        const std::array brand_leaves{
            CpuidAccess::read(0x80000002U),
            CpuidAccess::read(0x80000003U),
            CpuidAccess::read(0x80000004U),
        };
        const auto brand = platval::cpuid::decode_brand(brand_leaves);
        if (!brand.empty()) {
            data.brand_string = brand;
        }
    }

    const auto leaf_one = data.max_basic_leaf >= 1 ? CpuidAccess::read(1) : platval::cpuid::Registers{};
    std::optional<platval::cpuid::Registers> leaf_seven;
    if (data.max_basic_leaf >= 7) {
        leaf_seven = CpuidAccess::read(7, 0);
    }
    std::optional<platval::cpuid::Registers> extended_leaf_one;
    if (data.max_extended_leaf >= 0x80000001U) {
        extended_leaf_one = CpuidAccess::read(0x80000001U);
    }
    const bool has_xsave = (leaf_one.ecx & (1U << 27U)) != 0;
    const bool avx_os_enabled = has_xsave && (CpuidAccess::read_xcr0() & 0x6U) == 0x6U;
    data.features =
        platval::cpuid::decode_features(leaf_one, leaf_seven, extended_leaf_one, avx_os_enabled);

    if (data.max_basic_leaf >= 4) {
        constexpr std::uint32_t maximum_cache_subleaves = 64;
        for (std::uint32_t subleaf = 0; subleaf < maximum_cache_subleaves; ++subleaf) {
            const auto cache = platval::cpuid::decode_deterministic_cache(CpuidAccess::read(4, subleaf));
            if (!cache.has_value()) {
                break;
            }
            data.caches.push_back(*cache);
        }
    }
    return data;
}

}  // namespace

int main(const int argc, const char* const argv[]) {
    if (argc != 2) {
        std::cerr << "usage: cpuid_probe --json|--pretty|--version\n";
        return exit_invalid_arguments;
    }
    const std::string_view argument{argv[1]};
    if (argument == "--version") {
        std::cout << "cpuid_probe " << platval::cpuid::probe_version << '\n';
        return 0;
    }
    if (argument != "--json" && argument != "--pretty") {
        std::cerr << "invalid argument: expected --json, --pretty, or --version\n";
        return exit_invalid_arguments;
    }
    if (!platval::cpuid::CpuidAccess::supported()) {
        std::cerr << "cpuid_probe requires an x86 or x86-64 target\n";
        return exit_unsupported_architecture;
    }

    try {
        std::cout << platval::cpuid::render_json(collect_probe_data(), argument == "--pretty");
        return 0;
    } catch (const std::exception& exception) {
        std::cerr << "internal failure: " << exception.what() << '\n';
        return exit_internal_failure;
    } catch (...) {
        std::cerr << "internal failure\n";
        return exit_internal_failure;
    }
}
