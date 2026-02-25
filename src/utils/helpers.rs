//! # Funciones auxiliares
//!
//! Utilidades comunes para todo el proyecto.

/// Genera un ID único para clientes MQTT
pub fn generate_client_id() -> String {
    format!(
        "wave-cli-{}",
        uuid::Uuid::new_v4().to_string()[..8].to_string()
    )
}

/// Valida que una URL de broker sea válida
pub fn validate_broker_url(url: &str) -> bool {
    !url.is_empty()
        && (url.starts_with("mqtt://") || url.starts_with("tcp://") || !url.contains("://"))
}

/// Valida que un puerto sea válido (u16 válido es 1-65535)
pub fn validate_port(port: u16) -> bool {
    port > 0
}

/// Normaliza una URL/host de broker MQTT a hostname sin esquema ni path.
pub fn normalize_broker_host(url: &str) -> String {
    let trimmed = url.trim();
    if trimmed.is_empty() {
        return String::new();
    }

    let without_scheme = if let Some((_, rest)) = trimmed.split_once("://") {
        rest
    } else {
        trimmed
    };

    let host_port = without_scheme.split('/').next().unwrap_or("");

    if host_port.starts_with('[') {
        if let Some(end) = host_port.find(']') {
            return host_port[1..end].to_string();
        }
        return String::new();
    }

    if let Some((host, _port)) = host_port.rsplit_once(':') {
        if host_port.matches(':').count() == 1 {
            return host.to_string();
        }
    }

    host_port.to_string()
}
