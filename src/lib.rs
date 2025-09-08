// lib.rs - Punto de entrada de nuestra librería Rust para Python

// Importamos PyO3 - la librería que conecta Rust con Python
use pyo3::prelude::*;

/// Una función simple de Rust que se expondrá a Python
/// El atributo #[pyfunction] le dice a PyO3 que esta función
/// estará disponible desde Python
#[pyfunction]
fn saludar(nombre: &str) -> PyResult<String> {
    // En Rust, las funciones devuelven la última expresión
    // PyResult es como Result<T, Error> pero específico para PyO3
    Ok(format!("¡Hola {} desde Rust! 🦀", nombre))
}

/// Esta función define qué estará disponible cuando importemos
/// el módulo desde Python
/// 
/// En Python será: from wave_cli.wave_core import saludar
#[pymodule]
fn wave_core(_py: Python, modulo: &PyModule) -> PyResult<()> {
    // Agregamos nuestra función al módulo
    modulo.add_function(wrap_pyfunction!(saludar, modulo)?)?;
    
    // Agregamos información del módulo
    modulo.add("__version__", "0.1.0")?;
    modulo.add("__author__", "Wave CLI Team")?;
    
    Ok(())
}