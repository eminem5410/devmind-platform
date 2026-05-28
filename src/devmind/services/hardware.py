"""Service: Hardware - Tabla de GPUs y soporte de precision."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class HardwareSpec:
    name: str
    vendor: str
    vram_gb: float
    tdp_w: int
    price_usd: float
    fp4: bool = False
    fp8: bool = False
    fp16: bool = False
    bf16: bool = False
    fp32: bool = True
    use_case: str = ""
    notes: str = ""


HARDWARE_TABLE: list[HardwareSpec] = [
    HardwareSpec("H100 SXM5", "NVIDIA", 80, 700, 30000, fp4=True, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="FP4 nativo con ThriftAttention"),
    HardwareSpec("H100 PCIe", "NVIDIA", 80, 350, 25000, fp4=True, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="FP4 nativo con ThriftAttention"),
    HardwareSpec("B200", "NVIDIA", 192, 1000, 35000, fp4=True, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="Blackwell, FP4 nativo"),
    HardwareSpec("RTX 4090", "NVIDIA", 24, 450, 1600, fp8=True, fp16=True, bf16=True, use_case="Workstation", notes="FP8 nativo"),
    HardwareSpec("RTX 4080 Super", "NVIDIA", 16, 320, 1000, fp8=True, fp16=True, bf16=True, use_case="Workstation", notes="FP8 nativo"),
    HardwareSpec("RTX 4070 Ti Super", "NVIDIA", 16, 285, 800, fp8=True, fp16=True, bf16=True, use_case="Gaming/AI", notes="FP8 nativo"),
    HardwareSpec("RTX 4070", "NVIDIA", 12, 200, 600, fp8=True, fp16=True, bf16=True, use_case="Gaming/AI", notes="FP8 nativo"),
    HardwareSpec("RTX 4060 Ti 16GB", "NVIDIA", 16, 160, 450, fp8=True, fp16=True, bf16=True, use_case="Budget AI", notes="FP8 nativo, 16GB ideal"),
    HardwareSpec("RTX 4060 Ti 8GB", "NVIDIA", 8, 160, 400, fp8=True, fp16=True, bf16=True, use_case="Budget Gaming", notes="FP8 nativo"),
    HardwareSpec("RTX 3090", "NVIDIA", 24, 350, 700, fp16=True, bf16=True, use_case="Workstation", notes="24GB, popular para IA"),
    HardwareSpec("RTX 3080 10GB", "NVIDIA", 10, 320, 500, fp16=True, bf16=True, use_case="Gaming/AI", notes="10GB limitado"),
    HardwareSpec("RTX 3070", "NVIDIA", 8, 220, 400, fp16=True, bf16=True, use_case="Gaming", notes="8GB suficiente para 7B Q4"),
    HardwareSpec("RTX 3060 12GB", "NVIDIA", 12, 170, 250, fp16=True, bf16=True, use_case="Budget AI", notes="12GB, excelente precio"),
    HardwareSpec("RTX 2060 Super", "NVIDIA", 8, 175, 200, fp16=True, bf16=False, use_case="Budget", notes="FP16, sin BF16 nativo"),
    HardwareSpec("GTX 1650", "NVIDIA", 4, 75, 100, fp16=True, bf16=False, use_case="Entry", notes="4GB, modelos chicos only"),
    HardwareSpec("A100 80GB", "NVIDIA", 80, 300, 15000, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="FP8 via firmware update"),
    HardwareSpec("V100 32GB", "NVIDIA", 32, 250, 3000, fp16=True, bf16=False, use_case="Datacenter", notes="FP16 sin FP8/FP4"),
    HardwareSpec("RX 7900 XTX", "AMD", 24, 355, 900, fp16=True, bf16=True, use_case="Workstation", notes="ROCm soporte parcial"),
    HardwareSpec("RX 7900 XT", "AMD", 20, 315, 750, fp16=True, bf16=True, use_case="Gaming/AI", notes="ROCm soporte parcial"),
    HardwareSpec("RX 7800 XT", "AMD", 16, 263, 500, fp16=True, bf16=True, use_case="Budget", notes="ROCm mejorando"),
    HardwareSpec("MI300X", "AMD", 192, 750, 15000, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="CDNA3, FP8 nativo"),
    HardwareSpec("Arc A770 16GB", "Intel", 16, 225, 300, fp16=True, bf16=True, use_case="Budget AI", notes="OpenVINO, SYCL"),
    HardwareSpec("Arc A750 8GB", "Intel", 8, 225, 200, fp16=True, bf16=True, use_case="Budget", notes="OpenVINO"),
    HardwareSpec("M4 Max 128GB", "Apple", 128, 0, 2500, fp16=True, bf16=True, fp32=True, use_case="Laptop/Desktop", notes="Unified memory"),
    HardwareSpec("M3 Max 64GB", "Apple", 64, 0, 2000, fp16=True, bf16=True, fp32=True, use_case="Laptop", notes="Unified memory"),
    HardwareSpec("Intel Gaudi 3", "Intel", 128, 900, 12000, fp8=True, fp16=True, bf16=True, use_case="Datacenter", notes="FP8 nativo"),
]


def get_hardware(max_price=None, min_vram=None, vendor=None, use_case=None, supports_fp4=False, supports_fp8=False) -> list[HardwareSpec]:
    results = HARDWARE_TABLE
    if max_price is not None:
        results = [h for h in results if h.price_usd <= max_price]
    if min_vram is not None:
        results = [h for h in results if h.vram_gb >= min_vram]
    if vendor is not None:
        results = [h for h in results if h.vendor.lower() == vendor.lower()]
    if use_case is not None:
        results = [h for h in results if use_case.lower() in h.use_case.lower()]
    if supports_fp4:
        results = [h for h in results if h.fp4]
    if supports_fp8:
        results = [h for h in results if h.fp8]
    return results


def check_precision_support(gpu_name: str) -> dict:
    gpu_lower = gpu_name.lower()
    matched = None
    for hw in HARDWARE_TABLE:
        if hw.name.lower() == gpu_lower:
            matched = hw
            break
    if matched is None:
        for hw in HARDWARE_TABLE:
            if hw.name.lower() in gpu_lower or gpu_lower in hw.name.lower():
                matched = hw
                break
    if matched is None:
        return {"gpu": gpu_name, "found": False, "precision": {},
                "message": f"GPU '{gpu_name}' no encontrado en la base de datos."}
    precisions = {}
    if matched.fp4:
        precisions["FP4"] = "Soportado (ThriftAttention / hardware nativo)"
    if matched.fp8:
        precisions["FP8"] = "Soportado (hardware nativo)"
    if matched.fp16:
        precisions["FP16"] = "Soportado"
    if matched.bf16:
        precisions["BF16"] = "Soportado"
    if matched.fp32:
        precisions["FP32"] = "Soportado (default training)"
    return {"gpu": matched.name, "vendor": matched.vendor, "vram_gb": matched.vram_gb,
            "found": True, "precision": precisions, "notes": matched.notes}


def get_precision_summary() -> dict:
    summary = {
        "total_gpus": len(HARDWARE_TABLE),
        "fp4_count": sum(1 for h in HARDWARE_TABLE if h.fp4),
        "fp8_count": sum(1 for h in HARDWARE_TABLE if h.fp8),
        "fp16_count": sum(1 for h in HARDWARE_TABLE if h.fp16),
        "bf16_count": sum(1 for h in HARDWARE_TABLE if h.bf16),
    }
    budget = [h for h in HARDWARE_TABLE if h.price_usd <= 300 and h.vram_gb >= 8]
    midrange = [h for h in HARDWARE_TABLE if 300 < h.price_usd <= 1000 and h.vram_gb >= 12]
    highend = [h for h in HARDWARE_TABLE if h.price_usd > 1000]
    if budget:
        b = max(budget, key=lambda h: h.vram_gb)
        summary["best_budget"] = {"name": b.name, "vram_gb": b.vram_gb, "price_usd": b.price_usd}
    if midrange:
        m = max(midrange, key=lambda h: h.vram_gb)
        summary["best_midrange"] = {"name": m.name, "vram_gb": m.vram_gb, "price_usd": m.price_usd}
    if highend:
        hi = max(highend, key=lambda h: h.vram_gb)
        summary["best_highend"] = {"name": hi.name, "vram_gb": hi.vram_gb, "price_usd": hi.price_usd}
    return summary
