"""
Motor de recomendaciones inteligentes para DevMind.

Analiza los resultados del diagnostico y genera recomendaciones
contextuales basadas en el hardware, software y configuracion
del sistema del usuario.
"""

from __future__ import annotations

from devmind.models.diagnostic import (
    DiagnosticCheck,
    DiagnosticReport,
    Recommendation,
    Severity,
)


def generate_recommendations(report: DiagnosticReport) -> list[Recommendation]:
    """Genera recomendaciones basadas en el reporte de diagnostico.

    Analiza cada check y los datos del sistema para producir
    recomendaciones inteligentes, priorizadas y con acciones concretas.
    """
    recs: list[Recommendation] = []

    # Shorthand para buscar checks
    def find_check(name: str) -> DiagnosticCheck | None:
        for c in report.checks:
            if c.name == name:
                return c
        return None

    # Datos del sistema
    ram = report.system.ram_total_gb or 0
    has_gpu = find_check("GPU Dedicada") and find_check("GPU Dedicada").status == "ok"
    has_nvidia = find_check("NVIDIA GPU") and find_check("NVIDIA GPU").status == "ok"
    ollama_installed = find_check("Ollama") and find_check("Ollama").status != "missing"
    ollama_running = find_check("Ollama Server") and find_check("Ollama Server").status == "ok"
    ollama_models = find_check("Ollama Modelos")
    docker_installed = find_check("Docker") and find_check("Docker").status != "missing"
    docker_running = find_check("Docker Daemon") and find_check("Docker Daemon").status == "ok"
    has_compose = find_check("Docker Compose") and find_check("Docker Compose").status == "ok"
    has_cuda = find_check("CUDA Toolkit") and find_check("CUDA Toolkit").status == "ok"
    has_vulkan = find_check("Vulkan") and find_check("Vulkan").status == "ok"
    py_ver = report.system.python_version
    disk = report.system.disk_free_gb or 0

    # ── GPU y aceleracion ─────────────────────────────────────────────
    if not has_gpu:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="gpu",
            title="No se detecto GPU dedicada",
            message=(
                "El sistema opera en modo CPU-only. El rendimiento para inferencia "
                "y entrenamiento de modelos sera significativamente menor. Para "
                "workloads pesados de IA, considera instalar una GPU NVIDIA (RTX 3060 "
                "o superior con al menos 8GB VRAM)."
            ),
            action="Instalar una GPU dedicada o usar servicios cloud (RunPod, Lambda Labs)",
        ))
    elif has_nvidia and not has_cuda:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="gpu",
            title="NVIDIA GPU sin CUDA Toolkit",
            message=(
                "Se detecto una GPU NVIDIA pero el CUDA Toolkit no esta instalado. "
                "Sin CUDA Toolkit no puedes compilar extensiones CUDA custom ni "
                "instalar versiones GPU de PyTorch/TensorFlow desde source."
            ),
            action="Instalar CUDA Toolkit desde developer.nvidia.com/cuda-downloads",
            command="sudo apt install nvidia-cuda-toolkit",
        ))

    if has_vulkan and not has_gpu:
        recs.append(Recommendation(
            severity=Severity.INFO,
            category="gpu",
            title="Vulkan detectado (GPU integrada)",
            message=(
                "Vulkan esta disponible a traves de la GPU integrada (Intel/AMD). "
                "Algunos frameworks pueden usar Vulkan compute shaders, pero el "
                "rendimiento es limitado comparado con CUDA o ROCm."
            ),
        ))

    # ── RAM ───────────────────────────────────────────────────────────
    if ram > 0 and ram < 8:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="system",
            title=f"RAM limitada ({ram} GB)",
            message=(
                f"Con {ram} GB de RAM, hay restricciones importantes para modelos de IA. "
                "Los modelos de 7B+ parametros requieren al menos 8GB solo para inferencia. "
                "Se recomienda usar modelos pequenos (1B-4B parametros) como llama3.2:1b, "
                "phi3:mini, o gemma2:2b. Para entrenamiento, es probable que necesites "
                "cuantizacion (Q4) o LoRA/QLoRA para ajuste fino."
            ),
            action="Considerar upgrade de RAM o usar quantization para modelos grandes",
        ))
    elif ram >= 16:
        recs.append(Recommendation(
            severity=Severity.INFO,
            category="system",
            title=f"RAM adecuada ({ram} GB)",
            message=(
                f"Con {ram} GB de RAM puedes ejecutar modelos de hasta 13B parametros "
                "en cuantizacion Q4, o modelos de 7B en precisiion completa. Esto permite "
                "usar Llama 3, Mistral, Qwen y otros modelos de tamano medio."
            ),
        ))

    # ── Disco ─────────────────────────────────────────────────────────
    if 0 < disk < 30:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="system",
            title=f"Espacio en disco limitado ({disk} GB libres)",
            message=(
                "Los modelos de IA ocupan entre 2GB (modelos 3B Q4) y 40GB+ "
                "(modelos 70B). Con menos de 30GB libres, tendras espacio para "
                "muy pocos modelos. Los modelos se almacenan en ~/.ollama/models."
            ),
            action="Liberar espacio o agregar almacenamiento",
        ))

    # ── Ollama ────────────────────────────────────────────────────────
    if not ollama_installed:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="ollama",
            title="Ollama no esta instalado",
            message=(
                "Ollama es el motor de inferencia local mas popular para Linux. "
                "Permite ejecutar modelos como Llama 3, Mistral, Phi y mas "
                "directamente en tu maquina sin dependencias complejas."
            ),
            action="Instalar Ollama para ejecucion de modelos locales",
            command="curl -fsSL https://ollama.com/install.sh | sh",
            repairable=True,
        ))
    else:
        if not ollama_running:
            recs.append(Recommendation(
                severity=Severity.ERROR,
                category="ollama",
                title="Ollama instalado pero servidor no responde",
                message=(
                    "El binario de Ollama esta instalado pero el servidor no esta "
                    "ejecutandose. Sin el servidor, no puedes ejecutar ni descargar "
                    "modelos. Esto suele pasar si Ollama no se inicio automaticamente."
                ),
                action="Iniciar el servidor de Ollama",
                command="ollama serve",
                repairable=True,
            ))

        has_models = ollama_models and ollama_models.value and "Ninguno" not in (ollama_models.value or "")
        if ollama_running and not has_models:
            # Recomendar modelo basado en RAM y GPU
            if has_nvidia:
                model_rec = "llama3.1:8b" if ram >= 16 else "llama3.2:3b"
            elif ram >= 8:
                model_rec = "llama3.2:3b"
            elif ram >= 4:
                model_rec = "phi3:mini"
            else:
                model_rec = "llama3.2:1b"

            recs.append(Recommendation(
                severity=Severity.WARNING,
                category="ollama",
                title="Ningun modelo Ollama instalado",
                message=(
                    f"Ollama esta listo pero no hay modelos descargados. Se recomienda "
                    f"instalar {model_rec} como primer modelo — es optimo para tu "
                    f"configuracion de hardware ({ram} GB RAM"
                    + (", GPU NVIDIA)" if has_nvidia else ", CPU-only)")
                    + f". Una vez instalado, puedes chatear con: ollama run {model_rec}"
                ),
                action=f"Descargar modelo {model_rec}",
                command=f"ollama pull {model_rec}",
                repairable=True,
            ))

    # ── Docker ────────────────────────────────────────────────────────
    if not docker_installed:
        recs.append(Recommendation(
            severity=Severity.WARNING,
            category="docker",
            title="Docker no esta instalado",
            message=(
                "Docker es esencial para el desarrollo de IA. Permite ejecutar "
                "contenedores con herramientas como Jupyter, TensorFlow Serving, "
                "vLLM, TGI, y bases de datos vectoriales sin contaminar tu sistema."
            ),
            action="Instalar Docker Engine",
            command="curl -fsSL https://get.docker.com | sh",
            repairable=True,
        ))
    else:
        if not docker_running:
            recs.append(Recommendation(
                severity=Severity.ERROR,
                category="docker",
                title="Docker instalado pero daemon no esta ejecutando",
                message=(
                    "Docker esta instalado pero el daemon no esta activo. Los "
                    "contenedores no pueden arrancar sin el daemon. Esto suele "
                    "ocurrir si el servicio no se inicio con el sistema."
                ),
                action="Iniciar el daemon de Docker",
                command="sudo systemctl start docker",
                repairable=True,
            ))

        if docker_running and not has_compose:
            recs.append(Recommendation(
                severity=Severity.WARNING,
                category="docker",
                title="Docker Compose no disponible",
                message=(
                    "Docker Compose permite definir stacks multi-contenedor con YAML. "
                    "Es muy util para levantar entornos completos de IA (API + DB + "
                    "vector store) con un solo comando."
                ),
                action="Instalar Docker Compose plugin",
                command="sudo apt install docker-compose-plugin",
                repairable=True,
            ))

    # ── Python ────────────────────────────────────────────────────────
    if py_ver:
        major, minor = py_ver.split(".")[:2]
        major, minor = int(major), int(minor)
        if major == 3 and minor >= 14:
            recs.append(Recommendation(
                severity=Severity.WARNING,
                category="system",
                title=f"Python {py_ver} (version muy reciente)",
                message=(
                    f"Python {py_ver} fue lanzado recientemente y muchos frameworks de IA "
                    "como PyTorch, TensorFlow y scikit-learn pueden no tener compatibilidad "
                    "oficial aun. Se recomienda usar Python 3.11 o 3.12 (LTS) como version "
                    "principal para desarrollo de IA, y reservar 3.14 para testing."
                ),
                action="Considerar usar Python 3.12 como version principal para IA",
                command="pyenv install 3.12.8 && pyenv global 3.12.8",
            ))

    # ── Git ───────────────────────────────────────────────────────────
    git_check = find_check("Git")
    if git_check and git_check.status == "missing":
        recs.append(Recommendation(
            severity=Severity.ERROR,
            category="tools",
            title="Git no esta instalado",
            message=(
                "Git es indispensable para el desarrollo de software y especialmente "
                "para proyectos de IA donde necesitas versionar datasets, modelos y "
                "experimentos. Sin Git, no puedes usar devmind init ni colaborar."
            ),
            action="Instalar Git",
            command="sudo apt install git",
            repairable=True,
        ))

    # ── Ordenar por severidad (CRITICAL primero, INFO ultimo) ──────────
    priority = {Severity.CRITICAL: 0, Severity.ERROR: 1, Severity.WARNING: 2, Severity.INFO: 3}
    recs.sort(key=lambda r: (priority[r.severity], r.category))

    return recs
