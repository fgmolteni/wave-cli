# CLAUDE.md

Este archivo proporciona guía a Claude Code (claude.ai/code) cuando trabaja con código en este repositorio.

## Descripción del Proyecto

Wave CLI es un visualizador de mensajes y sistema de monitoreo para dispositivos LoRa basado en una arquitectura híbrida:

- **Core (Rust)**: Cliente MQTT compilado como librería Python mediante PyO3 para recibir mensajes de broker externo
- **UI (Python CLI)**: Interfaz interactiva con streaming en tiempo real de mensajes LoRa

El sistema funciona como centro de administración para dispositivos IoT LoRa que publican datos vía MQTT, proporcionando visualización y monitoreo centralizado.

## Comandos de Desarrollo

### Desarrollo del Core (Rust)
- `cargo build` - Compilar librería Rust
- `cargo test` - Ejecutar tests del core
- `maturin develop` - Compilar y instalar extensión Python localmente
- `maturin build --release` - Build optimizado para distribución

### Desarrollo de la UI (Python)
- `uv run main.py` - Ejecutar CLI en modo interactivo
- `uv run main.py <comando>` - Ejecutar comando directo
- `uv run main.py --version` - Mostrar información de versión
- `uv install` - Instalar dependencias Python
- `uv sync` - Sincronizar entorno con lockfile

## Comandos del Modo Interactivo

### Comandos de Monitoreo
- `monitor [--topic <topic>] [--filter <filtro>]` - Iniciar streaming de mensajes MQTT
- `devices` - Listar dispositivos LoRa conectados/activos
- `messages [--limit <num>] [--device <id>]` - Ver mensajes recientes
- `status <device_id>` - Estado detallado de dispositivo específico

### Comandos de Configuración
- `connect <broker_url> [--port <puerto>]` - Conectar a broker MQTT
- `subscribe <topic>` - Suscribirse a tópico MQTT adicional
- `config [parámetro] [valor]` - Ver/modificar configuración

### Comandos de Utilidad
- `help` - Mostrar comandos disponibles
- `clear` - Limpiar pantalla
- `history` - Historial de comandos
- `export [--format json|csv] [--file <ruta>]` - Exportar datos de sesión
- `exit`/`quit`/`q` - Salir

## Arquitectura del Proyecto

### Estructura Propuesta
```
wave-cli/
├── src-rust/                    # Core Rust
│   ├── lib.rs                  # Entrada PyO3
│   ├── mqtt/
│   │   ├── mod.rs             # Módulo MQTT
│   │   ├── client.rs          # Cliente MQTT
│   │   └── message.rs         # Estructuras de mensajes
│   ├── lora/
│   │   ├── mod.rs             # Módulo LoRa
│   │   ├── device.rs          # Gestión de dispositivos
│   │   └── packet.rs          # Procesamiento de paquetes
│   └── utils/
│       └── mod.rs             # Utilidades comunes
├── src-python/                 # UI Python
│   ├── main.py                # CLI principal
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── interactive.py     # Modo interactivo
│   │   ├── streaming.py       # Visualización en tiempo real
│   │   └── formatters.py      # Formato de salida
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── monitor.py         # Comando monitor
│   │   ├── devices.py         # Gestión dispositivos
│   │   └── export.py          # Exportación datos
│   └── config/
│       ├── __init__.py
│       └── settings.py        # Configuración global
├── constant/                   # Constantes compartidas
├── Cargo.toml                 # Configuración Rust
├── pyproject.toml            # Configuración Python + Maturin
└── README.md
```

### Componentes del Core (Rust)

#### Cliente MQTT (`mqtt/client.rs`)
- Conexión asíncrona a broker externo usando tokio-mqtt
- Manejo de reconexión automática
- Gestión de suscripciones múltiples
- Callbacks para mensajes recibidos

#### Procesador LoRa (`lora/device.rs`)
- Parsing de payloads LoRa desde mensajes MQTT
- Tracking de dispositivos activos en memoria
- Estadísticas de dispositivos (RSSI, último mensaje, etc.)
- Filtrado y clasificación de mensajes

#### Interfaz PyO3 (`lib.rs`)
- Wrapper Python para cliente MQTT
- Callbacks desde Rust a Python para streaming
- Gestión de threading entre Rust async y Python

### Componentes de la UI (Python)

#### Motor Interactivo (`ui/interactive.py`)
- Bucle principal con soporte para comandos directos
- Parser de comandos mejorado
- Integración con core Rust vía PyO3

#### Streaming en Tiempo Real (`ui/streaming.py`)
- Display continuo de mensajes usando Rich
- Filtros dinámicos por dispositivo/tópico
- Rate limiting para evitar spam visual

#### Sistema de Comandos (`commands/`)
- Comandos modulares siguiendo patrón Command
- Cada comando como clase independiente
- Validación y ayuda contextual

### Flujo de Datos
1. Dispositivos LoRa → Gateway → Broker MQTT
2. Core Rust suscribe a tópicos MQTT
3. Rust procesa y filtra mensajes LoRa
4. Callbacks PyO3 envían datos a Python
5. UI Python actualiza display en tiempo real

### Estado Actual vs Objetivo
- **Actual**: Simulación completa en Python
- **Objetivo**: Core real en Rust + UI Python optimizada
- **Migración**: Gradual, manteniendo compatibilidad de comandos
- no incluyas referencias a claude-code en los commit, issus y documentacion