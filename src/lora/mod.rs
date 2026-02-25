//! # Módulo LoRa
//!
//! Este módulo maneja toda la lógica específica de LoRa:
//! - Gestión de dispositivos LoRa
//! - Procesamiento de paquetes
//! - Configuración de parámetros LoRa

pub mod device;
pub mod packet;
pub mod config;

pub use device::LoRaDevice;
pub use packet::LoRaPacket;
pub use config::LoRaConfig;