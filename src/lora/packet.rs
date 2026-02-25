//! # Procesamiento de paquetes LoRa
//!
//! Maneja el parsing y procesamiento de paquetes LoRa.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Representa un paquete LoRa recibido
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LoRaPacket {
    /// ID del dispositivo origen
    pub device_id: String,
    /// Payload del paquete como bytes
    pub payload: Vec<u8>,
    /// Payload como string (si es válido UTF-8)
    pub payload_string: Option<String>,
    /// RSSI del paquete
    pub rssi: Option<i16>,
    /// SNR del paquete
    pub snr: Option<f32>,
    /// Frecuencia de recepción
    pub frequency: Option<f64>,
    /// Factor de dispersión usado
    pub spreading_factor: Option<u8>,
    /// Timestamp de recepción
    pub timestamp: DateTime<Utc>,
}

impl LoRaPacket {
    /// Crea un nuevo paquete LoRa
    pub fn new(device_id: String, payload: Vec<u8>) -> Self {
        let payload_string = String::from_utf8(payload.clone()).ok();
        
        Self {
            device_id,
            payload,
            payload_string,
            rssi: None,
            snr: None,
            frequency: None,
            spreading_factor: None,
            timestamp: Utc::now(),
        }
    }
    
    /// Intenta parsear el payload como JSON
    pub fn parse_json(&self) -> serde_json::Result<serde_json::Value> {
        match &self.payload_string {
            Some(s) => serde_json::from_str(s),
            None => Err(<serde_json::Error as serde::de::Error>::custom("Payload is not valid UTF-8")),
        }
    }
    
    /// Convierte el paquete a formato JSON para logging
    pub fn to_json(&self) -> serde_json::Result<String> {
        serde_json::to_string(self)
    }
}

/// Parser para diferentes formatos de paquetes LoRa
pub struct PacketParser;

impl PacketParser {
    /// Intenta parsear un mensaje MQTT como paquete LoRa
    pub fn parse_from_mqtt(topic: &str, payload: &[u8]) -> Option<LoRaPacket> {
        // Extraer device_id del tópico
        // Formato esperado: lora/{device_id}/data o similar
        let device_id = Self::extract_device_id_from_topic(topic)?;
        
        let mut packet = LoRaPacket::new(device_id, payload.to_vec());
        
        // Intentar extraer metadatos si el payload es JSON
        if let Ok(json_value) = packet.parse_json() {
            if let Some(obj) = json_value.as_object() {
                packet.rssi = obj.get("rssi")
                    .and_then(|v| v.as_i64())
                    .map(|v| v as i16);
                
                packet.snr = obj.get("snr")
                    .and_then(|v| v.as_f64())
                    .map(|v| v as f32);
                
                packet.frequency = obj.get("frequency")
                    .and_then(|v| v.as_f64());
                
                packet.spreading_factor = obj.get("sf")
                    .and_then(|v| v.as_u64())
                    .map(|v| v as u8);
            }
        }
        
        Some(packet)
    }
    
    /// Extrae el device_id de un tópico MQTT
    fn extract_device_id_from_topic(topic: &str) -> Option<String> {
        // Patrones comunes: lora/{device_id}/*, devices/{device_id}/*, etc.
        let parts: Vec<&str> = topic.split('/').collect();
        
        if parts.len() >= 2 {
            // Buscar patrones conocidos
            for (i, part) in parts.iter().enumerate() {
                if matches!(*part, "lora" | "device" | "devices" | "node" | "nodes") {
                    if i + 1 < parts.len() {
                        return Some(parts[i + 1].to_string());
                    }
                }
            }
        }
        
        // Fallback: usar el segundo segmento del tópico
        parts.get(1).map(|s| s.to_string())
    }
}