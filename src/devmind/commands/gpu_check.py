"""
Comando: devmind gpu check
Verifica GPUs, drivers CUDA y Vulkan.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devmind.utils.gpu import detect_all_gpus, detect_cuda_toolkit, detect_vulkan

console = Console()


def run_gpu_check() -> None:
    """Verifica el estado de las GPUs del sistema."""
    console.print()
    console.print(Panel(
        "[bold cyan]DevMind GPU Check[/bold cyan] — Analisis de hardware GPU",
        border_style="cyan",
    ))
    console.print()

    gpus = detect_all_gpus()

    if not gpus:
        console.print("[yellow]No se detectaron GPUs en el sistema.[/yellow]")
        console.print()

        # Sugerencias
        console.print("[dim]Posibles causas:[/dim]")
        console.print("  - No hay GPU dedicada instalada")
        console.print("  - Los drivers no estan instalados")
        console.print("  - Para NVIDIA: instalar el driver con [bold]sudo apt install nvidia-driver-535[/bold]")
        console.print("  - Para AMD: instalar ROCm desde [bold]https://rocm.amd.com[/bold]")

        # Vulkan fallback
        vulkan = detect_vulkan()
        if vulkan:
            console.print()
            console.print(f"[dim]Vulkan detectado: {vulkan}[/dim]")

        return

    # Tabla principal de GPUs
    table = Table(title="GPUs Detectadas", show_lines=True)
    table.add_column("Propiedad", style="bold", width=18)
    for i in range(len(gpus)):
        table.add_column(f"GPU {i}", width=28)

    props = [
        ("Vendor", [g.vendor for g in gpus]),
        ("Modelo", [g.name for g in gpus]),
        ("Driver", [g.driver_version or "N/A" for g in gpus]),
        ("VRAM Total", [f"{g.vram_total_mb} MB" if g.vram_total_mb else "N/A" for g in gpus]),
        ("VRAM Usada", [f"{g.vram_used_mb} MB" if g.vram_used_mb else "N/A" for g in gpus]),
        ("Temperatura", [f"{g.temperature_c} C" if g.temperature_c else "N/A" for g in gpus]),
        ("Utilizacion", [f"{g.utilization_pct}%" if g.utilization_pct else "N/A" for g in gpus]),
    ]

    for prop_name, values in props:
        row = [prop_name] + values
        table.add_row(*row)

    console.print(table)
    console.print()

    # CUDA
    cuda_ver = detect_cuda_toolkit()
    console.print("[bold]CUDA Toolkit[/bold]")
    if cuda_ver:
        console.print(f"  [green]Version detectada: {cuda_ver}[/green]")
    else:
        console.print("  [yellow]CUDA Toolkit no detectado[/yellow]")
        console.print("  [dim]nvidia-smi puede funcionar sin CUDA Toolkit instalado.[/dim]")
        console.print("  [dim]Para desarrollo CUDA: https://developer.nvidia.com/cuda-downloads[/dim]")
    console.print()

    # Vulkan
    vulkan = detect_vulkan()
    console.print("[bold]Vulkan[/bold]")
    if vulkan:
        console.print(f"  [green]{vulkan}[/green]")
    else:
        console.print("  [dim]Vulkan no detectado (opcional para algunos workloads)[/dim]")
    console.print()

    # Recomendaciones
    console.print("[bold]Compatibilidad AI[/bold]")
    nvidia_count = sum(1 for g in gpus if g.vendor == "NVIDIA")
    if nvidia_count > 0:
        console.print("  [green]Compatible con:[/green] PyTorch (CUDA), TensorFlow (CUDA), Ollama, vLLM, TensorRT")
    else:
        console.print("  [yellow]Sin NVIDIA:[/yellow] Considera ROCm (AMD) o CPU-only con Ollama")
    if cuda_ver:
        console.print("  [green]CUDA Toolkit:[/green] Listo para compilacion de extensiones custom")
