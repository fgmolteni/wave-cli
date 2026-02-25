//! # Configuración LoRa
//!
//! Maneja la configuración de parámetros LoRa.

use serde::{Deserialize, Serialize};

/// Configuración de parámetros LoRa
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LoRaConfig {
    /// Frecuencia de operación en MHz
    pub frequency: f64,
    /// Potencia de transmisión en dBm
    pub power: i8,
    /// Ancho de banda en kHz
    pub bandwidth: u32,
    /// Factor de dispersión (7-12)
    pub spreading_factor: u8,
    /// Tasa de codificación
    pub coding_rate: CodingRate,
}

/// Tasas de codificación LoRa disponibles
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum CodingRate {
    CR45, // 4/5
    CR46, // 4/6
    CR47, // 4/7
    CR48, // 4/8
}

impl Default for LoRaConfig {
    fn default() -> Self {
        Self {
            frequency: 915.0,
            power: 14,
            bandwidth: 125,
            spreading_factor: 7,
            coding_rate: CodingRate::CR45,
        }
    }
}

impl LoRaConfig {
    /// Crea una nueva configuración con valores por defecto
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Valida que la configuración sea válida
    pub fn validate(&self) -> Result<(), String> {
        if !(860.0..=928.0).contains(&self.frequency) {
            return Err("Frequency must be between 860.0 and 928.0 MHz".to_string());
        }
        
        if !(-18..=20).contains(&self.power) {
            return Err("Power must be between -18 and 20 dBm".to_string());
        }
        
        if ![125, 250, 500].contains(&self.bandwidth) {
            return Err("Bandwidth must be 125, 250, or 500 kHz".to_string());
        }
        
        if !(7..=12).contains(&self.spreading_factor) {
            return Err("Spreading factor must be between 7 and 12".to_string());
        }
        
        Ok(())
    }
    
    /// Convierte la configuración a JSON
    pub fn to_json(&self) -> serde_json::Result<String> {
        serde_json::to_string_pretty(self)
    }
    
    /// Carga la configuración desde JSON
    pub fn from_json(json: &str) -> serde_json::Result<Self> {
        serde_json::from_str(json)
    }
}

impl CodingRate {
    /// Convierte a string para display
    pub fn to_string(&self) -> &'static str {
        match self {
            CodingRate::CR45 => "4/5",
            CodingRate::CR46 => "4/6", 
            CodingRate::CR47 => "4/7",
            CodingRate::CR48 => "4/8",
        }
    }
}