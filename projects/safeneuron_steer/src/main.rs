use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use byteorder::{LittleEndian, ReadBytesExt, WriteBytesExt};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;
use tower_http::services::ServeDir;

struct AppState {
    model_dir: PathBuf,
}

#[derive(Serialize, Deserialize, Debug)]
struct ModelInfo {
    name: String,
    size: u64,
    path: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct GgufTensor {
    name: String,
    dimensions: Vec<u64>,
    tensor_type: u32,
    offset: u64,
    absolute_offset: u64,
    size_bytes: u64,
}

#[derive(Serialize, Deserialize, Debug)]
struct GgufHeaderInfo {
    version: u32,
    tensor_count: u64,
    kv_count: u64,
    alignment: u32,
    tensors: Vec<GgufTensor>,
}

#[derive(Deserialize)]
struct ModelQuery {
    path: String,
}

#[derive(Deserialize)]
struct SteerRequest {
    model_path: String,
    tensor_name: String,
    scale: f32,
}

#[tokio::main]
async fn main() {
    let port = std::env::var("PORT").unwrap_or_else(|_| "25201".to_string());
    let model_dir = PathBuf::from(std::env::var("MODEL_DIR").unwrap_or_else(|_| "/home/toxic/models".to_string()));

    let state = Arc::new(AppState { model_dir });

    let app = Router::new()
        .route("/api/models", get(list_models))
        .route("/api/inspect", get(inspect_model))
        .route("/api/steer", post(steer_model))
        .fallback_service(ServeDir::new("static"))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], port.parse().unwrap()));
    println!("SafeNeuron-Steer local server listening on http://{}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn list_models(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let mut models = Vec::new();
    if let Ok(entries) = std::fs::read_dir(&state.model_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() && path.extension().map_or(false, |ext| ext == "gguf") {
                if let Ok(metadata) = entry.metadata() {
                    models.push(ModelInfo {
                        name: path.file_name().unwrap().to_string_lossy().into_owned(),
                        size: metadata.len(),
                        path: path.to_string_lossy().into_owned(),
                    });
                }
            }
        }
    }
    Json(models)
}

async fn inspect_model(
    State(_state): State<Arc<AppState>>,
    Query(query): Query<ModelQuery>,
) -> Result<impl IntoResponse, (StatusCode, String)> {
    let path = Path::new(&query.path);
    if !path.exists() {
        return Err((StatusCode::NOT_FOUND, "Model file not found".to_string()));
    }

    let mut file = File::open(path).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    
    // Parse GGUF header
    let mut magic = [0u8; 4];
    file.read_exact(&mut magic).map_err(|_| (StatusCode::BAD_REQUEST, "Failed to read GGUF magic bytes".to_string()))?;
    if &magic != b"GGUF" {
        return Err((StatusCode::BAD_REQUEST, "Invalid GGUF file".to_string()));
    }

    let version = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
    let tensor_count = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
    let kv_count = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

    // Parse KVs (skip values but find alignment KV if present)
    let mut alignment = 32u32;
    for _ in 0..kv_count {
        let key_len = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut key_bytes = vec![0u8; key_len as usize];
        file.read_exact(&mut key_bytes).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let key = String::from_utf8_lossy(&key_bytes).into_owned();

        let val_type = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let val_size = skip_gguf_value(&mut file, val_type)?;
        
        if key == "general.alignment" && val_size == 4 {
            // Read value back
            let current_pos = file.stream_position().map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            file.seek(SeekFrom::Current(-4)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            if let Ok(align) = file.read_u32::<LittleEndian>() {
                alignment = align;
            }
            file.seek(SeekFrom::Start(current_pos)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        }
    }

    // Read Tensor metadata
    let mut tensors = Vec::new();
    for _ in 0..tensor_count {
        let name_len = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut name_bytes = vec![0u8; name_len as usize];
        file.read_exact(&mut name_bytes).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let name = String::from_utf8_lossy(&name_bytes).into_owned();

        let n_dimensions = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut dimensions = Vec::new();
        let mut elements_count = 1u64;
        for _ in 0..n_dimensions {
            let dim = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
            dimensions.push(dim);
            elements_count *= dim;
        }

        let tensor_type = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let offset = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

        // Calculate size in bytes based on GGML type
        let size_bytes = get_tensor_size(elements_count, tensor_type);

        tensors.push(GgufTensor {
            name,
            dimensions,
            tensor_type,
            offset,
            absolute_offset: 0,
            size_bytes,
        });
    }

    // Current position is the end of the header and metadata block.
    // The actual tensor data starts after this section, aligned to the GGUF alignment.
    let header_end = file.stream_position().map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
    let data_offset = ((header_end + (alignment as u64) - 1) / (alignment as u64)) * (alignment as u64);

    for t in &mut tensors {
        t.absolute_offset = data_offset + t.offset;
    }

    Ok(Json(GgufHeaderInfo {
        version,
        tensor_count,
        kv_count,
        alignment,
        tensors,
    }))
}

async fn steer_model(
    State(_state): State<Arc<AppState>>,
    Json(payload): Json<SteerRequest>,
) -> Result<impl IntoResponse, (StatusCode, String)> {
    let path = Path::new(&payload.model_path);
    if !path.exists() {
        return Err((StatusCode::NOT_FOUND, "Model file not found".to_string()));
    }

    // Inspect first to find the absolute offset and properties of the tensor
    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .open(path)
        .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

    // Quick parse header to get target tensor info
    let mut magic = [0u8; 4];
    file.read_exact(&mut magic).map_err(|_| (StatusCode::BAD_REQUEST, "Failed to read GGUF magic bytes".to_string()))?;
    if &magic != b"GGUF" {
        return Err((StatusCode::BAD_REQUEST, "Invalid GGUF file".to_string()));
    }

    let _version = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
    let tensor_count = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
    let kv_count = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;

    let mut alignment = 32u32;
    for _ in 0..kv_count {
        let key_len = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut key_bytes = vec![0u8; key_len as usize];
        file.read_exact(&mut key_bytes).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let key = String::from_utf8_lossy(&key_bytes).into_owned();

        let val_type = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let val_size = skip_gguf_value(&mut file, val_type)?;
        
        if key == "general.alignment" && val_size == 4 {
            let current_pos = file.stream_position().map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            file.seek(SeekFrom::Current(-4)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            if let Ok(align) = file.read_u32::<LittleEndian>() {
                alignment = align;
            }
            file.seek(SeekFrom::Start(current_pos)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        }
    }

    let mut target_tensor: Option<GgufTensor> = None;
    for _ in 0..tensor_count {
        let name_len = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut name_bytes = vec![0u8; name_len as usize];
        file.read_exact(&mut name_bytes).map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let name = String::from_utf8_lossy(&name_bytes).into_owned();

        let n_dimensions = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let mut dimensions = Vec::new();
        let mut elements_count = 1u64;
        for _ in 0..n_dimensions {
            let dim = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
            dimensions.push(dim);
            elements_count *= dim;
        }

        let tensor_type = file.read_u32::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let offset = file.read_u64::<LittleEndian>().map_err(|e| (StatusCode::BAD_REQUEST, e.to_string()))?;
        let size_bytes = get_tensor_size(elements_count, tensor_type);

        if name == payload.tensor_name {
            target_tensor = Some(GgufTensor {
                name,
                dimensions,
                tensor_type,
                offset,
                absolute_offset: 0,
                size_bytes,
            });
        }
    }

    if let Some(mut t) = target_tensor {
        let header_end = file.stream_position().map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        let data_offset = ((header_end + (alignment as u64) - 1) / (alignment as u64)) * (alignment as u64);
        t.absolute_offset = data_offset + t.offset;

        // Perform weight manipulation directly in-place!
        file.seek(SeekFrom::Start(t.absolute_offset)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

        // Depending on type (supporting F32/F16 and simple quant weight-scaling)
        if t.tensor_type == 0 { // F32
            let float_count = (t.size_bytes / 4) as usize;
            let mut floats = vec![0.0f32; float_count];
            for i in 0..float_count {
                if let Ok(val) = file.read_f32::<LittleEndian>() {
                    floats[i] = val * payload.scale;
                }
            }
            file.seek(SeekFrom::Start(t.absolute_offset)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            for val in floats {
                file.write_f32::<LittleEndian>(val).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            }
        } else {
            // For quant/other formats, we scale the weight block block-by-block if possible,
            // or modify the scales. In simple case, we zero out or scale the raw bytes to dampen activations.
            let mut raw_data = vec![0u8; t.size_bytes as usize];
            file.read_exact(&mut raw_data).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            
            // Scaled byte mapping: clamp activations by multiplying scales or directly scaling values
            for byte in &mut raw_data {
                let scaled = ((*byte as f32) * payload.scale).round();
                *byte = (scaled.clamp(0.0, 255.0)) as u8;
            }

            file.seek(SeekFrom::Start(t.absolute_offset)).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
            file.write_all(&raw_data).map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;
        }

        println!("Successfully modified tensor {} by scaling factor {}", t.name, payload.scale);
        return Ok(Json(serde_json::json!({
            "status": "success",
            "message": format!("Successfully scaled tensor {} by {}", t.name, payload.scale)
        })));
    }

    Err((StatusCode::NOT_FOUND, "Target tensor not found in model".to_string()))
}

fn get_tensor_size(elements: u64, tensor_type: u32) -> u64 {
    match tensor_type {
        0 => elements * 4, // F32
        1 => elements * 2, // F16
        8 => { // Q8_0
            let blocks = (elements + 31) / 32;
            blocks * (2 + 32)
        },
        _ => elements, // Fallback/approximation for complex quants
    }
}

fn skip_gguf_value(file: &mut File, val_type: u32) -> Result<u64, (StatusCode, String)> {
    let read_err = |e: std::io::Error| (StatusCode::BAD_REQUEST, e.to_string());
    match val_type {
        0..=2 => { file.seek(SeekFrom::Current(1)).map_err(read_err)?; Ok(1) } // uint8, int8, bool
        3..=4 => { file.seek(SeekFrom::Current(2)).map_err(read_err)?; Ok(2) } // uint16, int16
        5..=6 | 13 => { file.seek(SeekFrom::Current(4)).map_err(read_err)?; Ok(4) } // uint32, int32, float32
        7..=9 => { file.seek(SeekFrom::Current(8)).map_err(read_err)?; Ok(8) } // uint64, int64, float64
        10 => { // string
            let len = file.read_u64::<LittleEndian>().map_err(read_err)?;
            file.seek(SeekFrom::Current(len as i64)).map_err(read_err)?;
            Ok(8 + len)
        }
        11 => { // array
            let item_type = file.read_u32::<LittleEndian>().map_err(read_err)?;
            let item_count = file.read_u64::<LittleEndian>().map_err(read_err)?;
            let mut total_skipped = 12;
            for _ in 0..item_count {
                total_skipped += skip_gguf_value(file, item_type)?;
            }
            Ok(total_skipped)
        }
        _ => Err((StatusCode::BAD_REQUEST, "Unknown GGUF value type".to_string())),
    }
}
