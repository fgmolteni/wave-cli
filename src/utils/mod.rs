//! # Módulo Utils
//!
//! Utilidades compartidas en todo el proyecto:
//! - Manejo de errores
//! - Logging y configuración
//! - Funciones auxiliares

pub mod error;
pub mod logging;
pub mod helpers;

pub use error::{WaveError, Result};
pub use logging::setup_logging;