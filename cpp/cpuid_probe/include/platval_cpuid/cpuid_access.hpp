#pragma once

#include <cstdint>

namespace platval::cpuid {

struct Registers {
    std::uint32_t eax{};
    std::uint32_t ebx{};
    std::uint32_t ecx{};
    std::uint32_t edx{};
};

class CpuidAccess {
public:
    [[nodiscard]] static bool supported() noexcept;
    [[nodiscard]] static Registers read(std::uint32_t leaf, std::uint32_t subleaf = 0) noexcept;
    [[nodiscard]] static std::uint64_t read_xcr0() noexcept;
};

[[nodiscard]] const char* compiled_architecture() noexcept;

}  // namespace platval::cpuid
