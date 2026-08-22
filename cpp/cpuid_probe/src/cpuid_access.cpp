#include "platval_cpuid/cpuid_access.hpp"

#if defined(_MSC_VER) && (defined(_M_IX86) || defined(_M_X64))
#include <immintrin.h>
#include <intrin.h>
#elif (defined(__GNUC__) || defined(__clang__)) && (defined(__i386__) || defined(__x86_64__))
#include <cpuid.h>
#include <immintrin.h>
#endif

namespace platval::cpuid {

#if (defined(__GNUC__) || defined(__clang__)) && (defined(__i386__) || defined(__x86_64__))
__attribute__((target("xsave"))) static std::uint64_t read_xcr0_intrinsic() noexcept {
    return __builtin_ia32_xgetbv(0);
}
#endif

bool CpuidAccess::supported() noexcept {
#if defined(_M_IX86) || defined(_M_X64) || defined(__i386__) || defined(__x86_64__)
    return true;
#else
    return false;
#endif
}

Registers CpuidAccess::read(const std::uint32_t leaf, const std::uint32_t subleaf) noexcept {
#if defined(_MSC_VER) && (defined(_M_IX86) || defined(_M_X64))
    int values[4]{};
    __cpuidex(values, static_cast<int>(leaf), static_cast<int>(subleaf));
    return {
        static_cast<std::uint32_t>(values[0]),
        static_cast<std::uint32_t>(values[1]),
        static_cast<std::uint32_t>(values[2]),
        static_cast<std::uint32_t>(values[3]),
    };
#elif (defined(__GNUC__) || defined(__clang__)) && (defined(__i386__) || defined(__x86_64__))
    Registers result{};
    __cpuid_count(leaf, subleaf, result.eax, result.ebx, result.ecx, result.edx);
    return result;
#else
    static_cast<void>(leaf);
    static_cast<void>(subleaf);
    return {};
#endif
}

std::uint64_t CpuidAccess::read_xcr0() noexcept {
#if defined(_MSC_VER) && (defined(_M_IX86) || defined(_M_X64))
    return _xgetbv(0);
#elif (defined(__GNUC__) || defined(__clang__)) && (defined(__i386__) || defined(__x86_64__))
    return read_xcr0_intrinsic();
#else
    return 0;
#endif
}

const char* compiled_architecture() noexcept {
#if defined(_M_X64) || defined(__x86_64__)
    return "x86_64";
#elif defined(_M_IX86) || defined(__i386__)
    return "x86";
#else
    return "unsupported";
#endif
}

}  // namespace platval::cpuid
