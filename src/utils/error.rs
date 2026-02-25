//! # Gestión de errores
//!
//! Tipos de error unificados para todo el proyecto Wave CLI.

use pyo3::prelude::*;
use std::fmt;

/// Enumera los tipos de errores que pueden ocurrir en Wave CLI.
#[derive(Debug)]
pub enum WaveError {
    /// Error durante operaciones MQTT
    Mqtt(String),
    /// Error en operaciones LoRa
    LoRa(String),
    /// Error de configuración
    Config(String),
    /// Error de I/O
    Io(String),
    /// Error de serialización/deserialización
    Serialization(String),
    /// Error genérico
    Generic(String),
}

impl fmt::Display for WaveError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            WaveError::Mqtt(msg) => write!(f, "MQTT error: {}", msg),
            WaveError::LoRa(msg) => write!(f, "LoRa error: {}", msg),
            WaveError::Config(msg) => write!(f, "Configuration error: {}", msg),
            WaveError::Io(msg) => write!(f, "I/O error: {}", msg),
            WaveError::Serialization(msg) => write!(f, "Serialization error: {}", msg),
            WaveError::Generic(msg) => write!(f, "Error: {}", msg),
        }
    }
}

impl std::error::Error for WaveError {}

impl From<WaveError> for PyErr {
    fn from(err: WaveError) -> PyErr {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(err.to_string())
    }
}

/// Alias para Result con WaveError
pub type Result<T> = std::result::Result<T, WaveError>;

/// Trait para conversión a WaveError
pub trait IntoWaveError<T> {
    fn into_wave_error(self) -> Result<T>;
}

impl<T, E> IntoWaveError<T> for std::result::Result<T, E> 
where 
    E: fmt::Display 
{
    fn into_wave_error(self) -> Result<T> {
        self.map_err(|e| WaveError::Generic(e.to_string()))
    }
}