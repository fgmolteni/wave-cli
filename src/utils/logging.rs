//! # Sistema de logging
//!
//! Configuración unificada de logging para el proyecto.

use log::LevelFilter;
use std::sync::Once;

static LOGGING_INIT: Once = Once::new();

/// Configura el sistema de logging desde Python.
///
/// ## Parámetros
///
/// - `level`: Nivel de logging ("debug", "info", "warn", "error")
///
/// ## Comportamiento
///
/// Esta función es idempotente - la primera llamada inicializa el logger,
/// las posteriores son ignoradas silenciosamente.
///
/// ## Ejemplo
///
/// ```rust
/// use wave_core::utils::setup_logging;
///
/// setup_logging(Some("debug".to_string()));
/// setup_logging(Some("info".to_string())); // Será ignorada
/// ```
pub fn setup_logging(level: Option<String>) {
    let log_level = match level.as_deref() {
        Some("debug") => LevelFilter::Debug,
        Some("info") => LevelFilter::Info,
        Some("warn") => LevelFilter::Warn,
        Some("error") => LevelFilter::Error,
        _ => LevelFilter::Info,
    };

    // Usar Once para garantizar que solo se ejecute una sola vez en el programa
    LOGGING_INIT.call_once(|| {
        let _ = env_logger::Builder::from_default_env()
            .filter_level(log_level)
            .try_init();
    });
}
