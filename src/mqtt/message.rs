//! # Estructuras de mensajes MQTT
//!
//! Define los tipos de datos para mensajes MQTT.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Representa un mensaje MQTT recibido del broker.
///
/// Esta estructura encapsula toda la información relevante de un mensaje MQTT,
/// incluyendo metadatos como timestamp y QoS (Quality of Service).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MqttMessage {
    /// El tópico MQTT donde fue publicado el mensaje
    pub topic: String,
    /// Contenido del mensaje como string UTF-8
    pub payload: String,
    /// Momento exacto cuando el mensaje fue recibido (UTC)
    pub timestamp: DateTime<Utc>,
    /// Nivel de Quality of Service (0, 1, o 2)
    pub qos: u8,
}

impl MqttMessage {
    /// Crea un nuevo mensaje MQTT
    pub fn new(topic: String, payload: String, qos: u8) -> Self {
        Self {
            topic,
            payload,
            timestamp: Utc::now(),
            qos,
        }
    }
    
    /// Convierte el mensaje a formato JSON
    pub fn to_json(&self) -> serde_json::Result<String> {
        serde_json::to_string(self)
    }
    
    /// Crea un mensaje desde JSON
    pub fn from_json(json: &str) -> serde_json::Result<Self> {
        serde_json::from_str(json)
    }
}