//! # Wave CLI - Cliente MQTT Core
//!
//! Este módulo implementa el núcleo en Rust del sistema Wave CLI, proporcionando
//! un cliente MQTT asíncrono compilado como extensión Python mediante PyO3.
//!
//! ## Arquitectura
//!
//! El módulo está diseñado para funcionar como backend de alto rendimiento para
//! la interfaz Python, manejando:
//!
//! - **Conexiones MQTT asíncronas** con reconexión automática
//! - **Gestión de mensajes en tiempo real** con buffer circular
//! - **Threading seguro** entre el runtime de Tokio y Python
//! - **Manejo robusto de errores** con tipos específicos
//!
//! ## Uso desde Python
//!
//! ```python
//! import wave_core
//!
//! # Crear cliente
//! client = wave_core.create_mqtt_client()
//!
//! # Conectar a broker
//! success = client.connect("localhost", 1883)
//! if success:
//!     # Suscribirse a tópicos
//!     client.subscribe("sensor/+/data")
//!     
//!     # Iniciar escucha de mensajes
//!     client.start_listening()
//!     
//!     # Obtener mensajes recientes
//!     messages = client.get_messages(limit=10)
//! ```

use pyo3::prelude::*;

// Módulos del proyecto
pub mod mqtt;
pub mod lora;
pub mod utils;

// Re-exports para facilitar uso
pub use mqtt::{MqttClient, MqttMessage};
pub use utils::{WaveError, Result, setup_logging as setup_rust_logging};

/// Función factory para crear instancias del cliente MQTT desde Python.
///
/// Esta es la función principal que debe usar el código Python para obtener
/// una instancia del cliente MQTT. Encapsula la lógica de inicialización
/// y manejo de errores del constructor.
///
/// ## Valor de retorno
///
/// Retorna una nueva instancia de `MqttClient` lista para usar.
///
/// ## Errores
///
/// Puede fallar si no se puede crear el runtime de Tokio subyacente.
/// En este caso se lanza `PyRuntimeError`.
///
/// ## Ejemplo desde Python
///
/// ```python
/// import wave_core
///
/// # Forma recomendada de crear cliente
/// client = wave_core.create_mqtt_client()
///
/// # Alternativamente (equivalente)
/// client = wave_core.MqttClient()
/// ```
#[pyfunction]
fn create_mqtt_client() -> PyResult<MqttClient> {
    MqttClient::new()
}

/// Configura el sistema de logging del núcleo Rust desde Python.
///
/// Inicializa el logger `env_logger` que permite ver los logs internos
/// del cliente MQTT, útil para debugging y monitoreo de operaciones.
///
/// ## Parámetros
///
/// - `level`: Nivel de logging opcional ("debug", "info", "warn", "error")
///   - Por defecto: "info"
///   - "debug": Logs muy detallados, incluye cada mensaje MQTT
///   - "info": Logs de operaciones importantes (conexiones, suscripciones)
///   - "warn": Solo advertencias y errores
///   - "error": Solo errores críticos
///
/// ## Configuración del entorno
///
/// También respeta la variable de entorno `RUST_LOG` si está configurada:
/// - `RUST_LOG=debug`: Equivalente a level="debug"
/// - `RUST_LOG=wave_core=info`: Logging específico del módulo
///
/// ## Ejemplo desde Python
///
/// ```python
/// import wave_core
///
/// # Configurar logging detallado para debugging
/// wave_core.setup_logging("debug")
///
/// # Configurar solo errores para producción
/// wave_core.setup_logging("error")
///
/// # Usar configuración por defecto (info)
/// wave_core.setup_logging()
///
/// # Ahora los logs aparecerán en stderr cuando uses el cliente
/// client = wave_core.create_mqtt_client()
/// client.connect("localhost", 1883)  # Verás: "Successfully connected to MQTT broker..."
/// ```
///
/// ## Nota importante
///
/// Esta función debe llamarse una sola vez al inicio del programa.
/// Llamadas posteriores serán ignoradas debido a limitaciones de `env_logger`.
#[pyfunction]
fn setup_logging(level: Option<String>) -> PyResult<()> {
    setup_rust_logging(level);
    Ok(())
}

/// Módulo PyO3 que expone la funcionalidad Rust a Python.
///
/// Este es el punto de entrada principal del módulo `wave_core` cuando se
/// importa desde Python. Define todas las clases, funciones y constantes
/// disponibles para el código Python.
///
/// ## Exports disponibles
///
/// - **MqttClient**: Clase principal para operaciones MQTT
/// - **create_mqtt_client()**: Función factory para crear clientes
/// - **setup_logging()**: Configuración del sistema de logging
/// - **__version__**: Versión del módulo
///
/// ## Uso desde Python
///
/// ```python
/// import wave_core
///
/// # Ver versión del módulo
/// print(f"Wave Core versión: {wave_core.__version__}")
///
/// # Configurar logging
/// wave_core.setup_logging("info")
///
/// # Crear y usar cliente MQTT
/// client = wave_core.create_mqtt_client()
/// # ... usar cliente ...
/// ```
#[pymodule]
fn wave_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<MqttClient>()?;
    m.add_function(wrap_pyfunction!(create_mqtt_client, m)?)?;
    m.add_function(wrap_pyfunction!(setup_logging, m)?)?;
    m.add("__version__", "0.1.0")?;
    Ok(())
}