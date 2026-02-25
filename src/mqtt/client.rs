//! # Cliente MQTT
//!
//! Implementación del cliente MQTT con threading y gestión de mensajes.

use pyo3::prelude::*;
use rumqttc::{Event, Packet, QoS};
use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::{Mutex, RwLock};
use tokio::time::{sleep, Duration};
use tokio::task::JoinHandle;
use log::{error, info, warn, debug};

use super::{MqttConnection, MqttMessage};
use crate::utils::WaveError;

/// Cliente MQTT asíncrono optimizado para integración con Python.
#[pyclass]
pub struct MqttClient {
    /// Conexión MQTT compartida (cliente + eventloop) protegida por Arc<Mutex>
    connection: Arc<Mutex<Option<MqttConnection>>>,
    /// Buffer circular thread-safe para almacenar mensajes recibidos
    messages: Arc<Mutex<VecDeque<MqttMessage>>>,
    /// Estado de conexión compartido entre threads
    is_connected: Arc<RwLock<bool>>,
    /// URL del broker MQTT configurado
    broker_url: Arc<RwLock<String>>,
    /// Puerto del broker MQTT
    port: Arc<RwLock<u16>>,
    /// Runtime de Tokio para operaciones asíncronas
    runtime: Arc<tokio::runtime::Runtime>,
    /// Handle del task de escucha de mensajes en background
    listener_handle: Arc<Mutex<Option<JoinHandle<()>>>>,
    /// Límite máximo de mensajes en buffer
    max_messages: usize,
}

#[pymethods]
impl MqttClient {
    /// Crea una nueva instancia del cliente MQTT.
    #[new]
    pub fn new() -> PyResult<Self> {
        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                format!("Failed to create tokio runtime: {}", e)
            ))?;

        Ok(Self {
            connection: Arc::new(Mutex::new(None)),
            messages: Arc::new(Mutex::new(VecDeque::new())),
            is_connected: Arc::new(RwLock::new(false)),
            broker_url: Arc::new(RwLock::new(String::new())),
            port: Arc::new(RwLock::new(1883)),
            runtime: Arc::new(runtime),
            listener_handle: Arc::new(Mutex::new(None)),
            max_messages: 1000,
        })
    }

    /// Establece conexión con el broker MQTT especificado.
    fn connect(&mut self, py: Python, broker_url: String, port: Option<u16>) -> PyResult<bool> {
        let port_val = port.unwrap_or(1883);
        
        let runtime = self.runtime.clone();
        let broker_url_arc = self.broker_url.clone();
        let port_arc = self.port.clone();
        let is_connected = self.is_connected.clone();
        let connection_arc = self.connection.clone();
        
        Ok(py.allow_threads(|| {
            runtime.block_on(async {
                // Actualizar configuración
                *broker_url_arc.write().await = broker_url.clone();
                *port_arc.write().await = port_val;
                *is_connected.write().await = false;

                // Crear nueva conexión
                let mqtt_connection = match MqttConnection::new(&broker_url, port_val) {
                    Ok(conn) => conn,
                    Err(e) => {
                        error!("Failed to create MQTT connection: {}", e);
                        return false;
                    }
                };

                // Intentar establecer conexión inicial con timeout
                match tokio::time::timeout(
                    Duration::from_secs(10), 
                    async {
                        let mut eventloop = mqtt_connection.eventloop;
                        loop {
                            match eventloop.poll().await {
                                Ok(Event::Incoming(Packet::ConnAck(connack))) => {
                                    if connack.code == rumqttc::ConnectReturnCode::Success {
                                        info!("Successfully connected to MQTT broker: {}:{}", broker_url, port_val);
                                        return Ok(eventloop);
                                    } else {
                                        error!("Connection refused: {:?}", connack.code);
                                        return Err(WaveError::Mqtt(format!("Connection refused: {:?}", connack.code)));
                                    }
                                }
                                Ok(Event::Outgoing(_)) => continue,
                                Err(e) => {
                                    error!("Connection error: {}", e);
                                    return Err(WaveError::Mqtt(e.to_string()));
                                }
                                _ => continue,
                            }
                        }
                    }
                ).await {
                    Ok(Ok(eventloop)) => {
                        let new_connection = MqttConnection {
                            client: mqtt_connection.client,
                            eventloop,
                        };
                        *connection_arc.lock().await = Some(new_connection);
                        *is_connected.write().await = true;
                        true
                    }
                    Ok(Err(e)) => {
                        error!("Failed to connect: {}", e);
                        false
                    }
                    Err(_) => {
                        error!("Connection timeout after 10 seconds");
                        false
                    }
                }
            })
        }))
    }

    /// Se suscribe a un tópico MQTT específico.
    fn subscribe(&mut self, py: Python, topic: String) -> PyResult<bool> {
        let runtime = self.runtime.clone();
        let is_connected = self.is_connected.clone();
        let connection_arc = self.connection.clone();
        
        py.allow_threads(|| {
            runtime.block_on(async {
                let connected = *is_connected.read().await;
                if !connected {
                    return Err(WaveError::Mqtt("Client not connected".to_string()));
                }

                let connection_guard = connection_arc.lock().await;
                let connection = match connection_guard.as_ref() {
                    Some(conn) => conn,
                    None => return Err(WaveError::Mqtt("No active connection".to_string())),
                };

                match connection.client.subscribe(&topic, QoS::AtMostOnce).await {
                    Ok(_) => {
                        info!("Successfully subscribed to topic: {}", topic);
                        Ok(true)
                    }
                    Err(e) => {
                        error!("Failed to subscribe to topic {}: {}", topic, e);
                        Err(WaveError::Mqtt(format!("Failed to subscribe to {}: {}", topic, e)))
                    }
                }
            })
        }).map_err(|e: WaveError| e.into())
    }

    /// Inicia el listener de mensajes MQTT en background.
    fn start_listening(&mut self, py: Python) -> PyResult<()> {
        let runtime = self.runtime.clone();
        let is_connected = self.is_connected.clone();
        let connection_arc = self.connection.clone();
        let messages = self.messages.clone();
        let listener_handle = self.listener_handle.clone();
        let max_messages = self.max_messages;
        
        py.allow_threads(|| {
            runtime.block_on(async {
                let connected = *is_connected.read().await;
                if !connected {
                    return Err(WaveError::Mqtt("Client not connected".to_string()));
                }

                // Detener listener anterior si existe
                let mut handle_guard = listener_handle.lock().await;
                if let Some(handle) = handle_guard.take() {
                    handle.abort();
                    info!("Stopped previous message listener");
                }

                // Tomar ownership de la conexión para el listener
                let mut connection_guard = connection_arc.lock().await;
                let mut mqtt_connection = match connection_guard.take() {
                    Some(conn) => conn,
                    None => return Err(WaveError::Mqtt("No active connection".to_string())),
                };
                
                // Spawning del task de escucha
                let handle = tokio::spawn(async move {
                    info!("Starting MQTT message listener");
                    
                    let mut reconnect_attempts = 0;
                    const MAX_RECONNECT_ATTEMPTS: u32 = 5;
                    
                    loop {
                        match mqtt_connection.eventloop.poll().await {
                            Ok(Event::Incoming(Packet::ConnAck(connack))) => {
                                if connack.code == rumqttc::ConnectReturnCode::Success {
                                    info!("Message listener connected");
                                    reconnect_attempts = 0;
                                }
                            }
                            Ok(Event::Incoming(Packet::Publish(publish))) => {
                                debug!("Received message on topic: {}", publish.topic);
                                
                                let message = MqttMessage::new(
                                    publish.topic.clone(),
                                    String::from_utf8_lossy(&publish.payload).to_string(),
                                    publish.qos as u8,
                                );

                                let mut msgs = messages.lock().await;
                                msgs.push_back(message);
                                
                                if msgs.len() > max_messages {
                                    msgs.pop_front();
                                }
                            }
                            Ok(_) => {} // Otros eventos MQTT
                            Err(e) => {
                                error!("Error in message listener: {}", e);
                                reconnect_attempts += 1;
                                
                                if reconnect_attempts <= MAX_RECONNECT_ATTEMPTS {
                                    warn!("Attempting to reconnect... (attempt {}/{})", 
                                          reconnect_attempts, MAX_RECONNECT_ATTEMPTS);
                                    sleep(Duration::from_secs(2_u64.pow(reconnect_attempts.min(5)))).await;
                                } else {
                                    error!("Max reconnection attempts reached. Listener stopping.");
                                    break;
                                }
                            }
                        }
                    }
                    
                    warn!("MQTT message listener stopped");
                });
                
                *handle_guard = Some(handle);
                info!("MQTT message listener started successfully");
                Ok(())
            })
        }).map_err(|e: WaveError| e.into())
    }

    /// Obtiene los mensajes MQTT más recientes del buffer interno.
    fn get_messages(&self, py: Python, limit: Option<usize>) -> PyResult<Vec<PyObject>> {
        let runtime = self.runtime.clone();
        let messages = self.messages.clone();
        
        py.allow_threads(|| {
            runtime.block_on(async {
                let messages_guard = messages.lock().await;
                let limit = limit.unwrap_or(messages_guard.len());
                
                let recent_messages: PyResult<Vec<PyObject>> = messages_guard
                    .iter()
                    .rev()
                    .take(limit)
                    .map(|msg| {
                        Python::with_gil(|py| -> PyResult<PyObject> {
                            let dict = pyo3::types::PyDict::new(py);
                            dict.set_item("topic", &msg.topic)?;
                            dict.set_item("payload", &msg.payload)?;
                            dict.set_item("timestamp", msg.timestamp.to_rfc3339())?;
                            dict.set_item("qos", msg.qos)?;
                            Ok(dict.to_object(py))
                        })
                    })
                    .collect();
                
                recent_messages
            })
        })
    }

    /// Verifica si el cliente está conectado al broker MQTT.
    fn is_connected(&self, py: Python) -> PyResult<bool> {
        let runtime = self.runtime.clone();
        let is_connected = self.is_connected.clone();
        
        py.allow_threads(|| {
            runtime.block_on(async {
                Ok(*is_connected.read().await)
            })
        })
    }

    /// Desconecta el cliente del broker MQTT y detiene todas las operaciones.
    fn disconnect(&mut self, py: Python) -> PyResult<()> {
        let runtime = self.runtime.clone();
        let is_connected = self.is_connected.clone();
        let listener_handle = self.listener_handle.clone();
        let connection_arc = self.connection.clone();
        
        py.allow_threads(|| {
            runtime.block_on(async {
                // Detener el listener
                let mut handle_guard = listener_handle.lock().await;
                if let Some(handle) = handle_guard.take() {
                    handle.abort();
                    info!("Message listener stopped");
                }
                
                // Limpiar la conexión
                let mut connection_guard = connection_arc.lock().await;
                if connection_guard.is_some() {
                    *connection_guard = None;
                    info!("MQTT connection cleared");
                }
                
                *is_connected.write().await = false;
                Ok(())
            })
        })
    }
}