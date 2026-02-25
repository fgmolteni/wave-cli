//! # Gestión de dispositivos LoRa
//!
//! Maneja el tracking y estado de dispositivos LoRa.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Representa un dispositivo LoRa en la red
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LoRaDevice {
    /// ID único del dispositivo
    pub device_id: String,
    /// Nombre amigable del dispositivo
    pub name: Option<String>,
    /// Último RSSI medido
    pub last_rssi: Option<i16>,
    /// Último SNR medido
    pub last_snr: Option<f32>,
    /// Timestamp del último mensaje
    pub last_seen: Option<DateTime<Utc>>,
    /// Número total de mensajes recibidos
    pub message_count: u64,
    /// Estado del dispositivo
    pub status: DeviceStatus,
}

/// Estados posibles de un dispositivo LoRa
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum DeviceStatus {
    /// Dispositivo activo y enviando datos
    Active,
    /// Dispositivo inactivo (sin mensajes recientes)
    Inactive,
    /// Dispositivo con problemas de conectividad
    Warning,
    /// Dispositivo fuera de línea
    Offline,
}

impl LoRaDevice {
    /// Crea un nuevo dispositivo LoRa
    pub fn new(device_id: String) -> Self {
        Self {
            device_id,
            name: None,
            last_rssi: None,
            last_snr: None,
            last_seen: None,
            message_count: 0,
            status: DeviceStatus::Offline,
        }
    }
    
    /// Actualiza las estadísticas del dispositivo con un nuevo mensaje
    pub fn update_stats(&mut self, rssi: Option<i16>, snr: Option<f32>) {
        self.last_rssi = rssi;
        self.last_snr = snr;
        self.last_seen = Some(Utc::now());
        self.message_count += 1;
        self.status = DeviceStatus::Active;
    }
}

/// Manager para el tracking de dispositivos LoRa
pub struct DeviceManager {
    devices: HashMap<String, LoRaDevice>,
}

impl DeviceManager {
    /// Crea un nuevo manager de dispositivos
    pub fn new() -> Self {
        Self {
            devices: HashMap::new(),
        }
    }
    
    /// Registra o actualiza un dispositivo
    pub fn update_device(&mut self, device_id: String, rssi: Option<i16>, snr: Option<f32>) {
        let device = self.devices.entry(device_id.clone())
            .or_insert_with(|| LoRaDevice::new(device_id));
        
        device.update_stats(rssi, snr);
    }
    
    /// Obtiene todos los dispositivos
    pub fn get_devices(&self) -> Vec<&LoRaDevice> {
        self.devices.values().collect()
    }
    
    /// Obtiene un dispositivo específico
    pub fn get_device(&self, device_id: &str) -> Option<&LoRaDevice> {
        self.devices.get(device_id)
    }
}