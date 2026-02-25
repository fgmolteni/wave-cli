//! # Módulo MQTT
//!
//! Este módulo implementa toda la funcionalidad relacionada con MQTT:
//! - Cliente asíncrono con reconexión automática
//! - Gestión de mensajes y suscripciones
//! - Estructuras de datos para mensajes MQTT

pub mod client;
pub mod message;
pub mod connection;

pub use client::MqttClient;
pub use message::MqttMessage;
pub use connection::MqttConnection;