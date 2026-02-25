//! # Gestión de conexiones MQTT
//!
//! Maneja conexiones y configuración MQTT.

use rumqttc::{AsyncClient, EventLoop, MqttOptions};
use tokio::time::Duration;
use crate::utils::{WaveError, Result, helpers::*};

/// Representa una conexión MQTT completa con cliente y eventloop.
pub struct MqttConnection {
    pub client: AsyncClient,
    pub eventloop: EventLoop,
}

impl MqttConnection {
    /// Crea una nueva conexión MQTT
    pub fn new(broker_url: &str, port: u16) -> Result<Self> {
        if !validate_broker_url(broker_url) {
            return Err(WaveError::Config("Invalid broker URL".to_string()));
        }
        
        if !validate_port(port) {
            return Err(WaveError::Config("Invalid port number".to_string()));
        }
        
        let broker_host = normalize_broker_host(broker_url);
        if broker_host.is_empty() {
            return Err(WaveError::Config("Invalid broker host".to_string()));
        }

        let client_id = generate_client_id();
        let mut mqtt_options = MqttOptions::new(&client_id, broker_host, port);
        
        // Configuración optimizada
        mqtt_options.set_keep_alive(Duration::from_secs(30));
        mqtt_options.set_max_packet_size(1024 * 1024, 1024 * 1024); // 1MB
        
        let (client, eventloop) = AsyncClient::new(mqtt_options, 100);
        
        Ok(MqttConnection {
            client,
            eventloop,
        })
    }
}