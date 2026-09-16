use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tokio::process::Command;

// ── Fork metadata (mirrors tools/fleet/forks.json) ────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForkMeta {
    pub name: String,
    pub bench_bin: PathBuf,
    pub ld_library_path: String,
}

pub fn soverign_forks() -> Vec<ForkMeta> {
    vec![
        ForkMeta {
            name: "beellama".into(),
            bench_bin: "/home/toxic/projects/beellama.cpp/build/bin/llama-bench".into(),
            ld_library_path: "/home/toxic/projects/beellama.cpp/build/bin".into(),
        },
        ForkMeta {
            name: "turboquant".into(),
            bench_bin: "/home/toxic/projects/llama-cpp-turboquant/build/bin/llama-bench".into(),
            ld_library_path: "/home/toxic/projects/llama-cpp-turboquant/build/bin".into(),
        },
        ForkMeta {
            name: "ik_llama".into(),
            bench_bin: "/home/toxic/projects/ik_llama.cpp-main/build/bin/llama-bench".into(),
            ld_library_path: "/home/toxic/projects/ik_llama.cpp-main/build/bin".into(),
        },
        ForkMeta {
            name: "ik_turboquant".into(),
            bench_bin: "/home/toxic/projects/ik_turboquant/build/bin/llama-bench".into(),
            ld_library_path: "/home/toxic/projects/ik_llama.cpp-main/build_turboquant/bin".into(),
        },
    ]
}

// ── Model discovery ──────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiscoveredModel {
    pub path: PathBuf,
    pub filename: String,
    pub size_bytes: u64,
    pub size_gb: String,
    pub fork: String,
    pub quant: String,
    pub params_b: Option<f64>,
}

pub fn scan_models(models_dir: &Path) -> Vec<DiscoveredModel> {
    let mut models = Vec::new();
    let dir = match std::fs::read_dir(models_dir) {
        Ok(d) => d,
        Err(_) => return models,
    };

    for entry in dir.flatten() {
        let path = entry.path();
        let Some(name) = path
            .file_name()
            .and_then(|n| n.to_str())
            .map(|s| s.to_string())
        else {
            continue;
        };
        if !name.ends_with(".gguf") {
            continue;
        }
        let size_bytes = std::fs::metadata(&path).map(|m| m.len()).unwrap_or(0);
        let size_gb = format!("{:.2}", size_bytes as f64 / 1_073_741_824.0);
        let fork = classify_fork(&name);
        let quant = classify_quant(&name);
        let params_b = extract_params_b(&name);

        models.push(DiscoveredModel {
            path,
            filename: name.clone(),
            size_bytes,
            size_gb,
            fork: classify_fork(&name),
            quant: classify_quant(&name),
            params_b: extract_params_b(&name),
        });
    }
    models
}

fn classify_fork(filename: &str) -> String {
    let lower = filename.to_lowercase();
    if lower.contains("ik_turboquant") || lower.contains("turboquant") && lower.contains("ik") {
        "ik_turboquant".into()
    } else if lower.contains("ik_llama") || lower.contains("ik_") {
        "ik_llama".into()
    } else if lower.contains("turboquant") || lower.contains("turbo") {
        "turboquant".into()
    } else {
        "beellama".into()
    }
}

fn classify_quant(filename: &str) -> String {
    let lower = filename.to_lowercase();
    let quants = [
        "iq4_xs", "iq4xs", "q4_k_m", "q4km", "q4_k_xl", "q5_k_m", "q5km", "q5_k_xl", "q6_k",
        "q8_0", "bf16", "tcq", "turbo3",
    ];
    for q in &quants {
        if lower.contains(q) {
            return q.replace('_', "").to_uppercase();
        }
    }
    "UNKNOWN".into()
}

fn extract_params_b(filename: &str) -> Option<f64> {
    let re = regex::Regex::new(r"(\d+\.?\d*)[bB]").ok()?;
    let caps = re.captures(filename)?;
    caps.get(1)?.as_str().parse().ok()
}

// ── Benchmark execution ──────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchRun {
    pub model_filename: String,
    pub fork: String,
    pub prompt_tps: f64,
    pub gen_tps: f64,
    pub params: Option<String>,
    pub status: String,
    pub details: Option<String>,
    pub duration_ms: u64,
}

pub async fn bench_model(model: &DiscoveredModel, fork: &ForkMeta) -> Result<BenchRun, String> {
    let bench_bin = &fork.bench_bin;
    if !bench_bin.exists() {
        return Err(format!("llama-bench not found: {}", bench_bin.display()));
    }

    // Packa-small benchmark: 128 prompt, 32 gen, 1 rep, ngl 99
    let start = std::time::Instant::now();
    let result = tokio::time::timeout(
        Duration::from_secs(180),
        Command::new(bench_bin)
            .arg("-m")
            .arg(&model.path)
            .arg("-p")
            .arg("128")
            .arg("-n")
            .arg("32")
            .arg("-r")
            .arg("1")
            .arg("-ngl")
            .arg("99")
            .env("LD_LIBRARY_PATH", &fork.ld_library_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output(),
    )
    .await;

    let duration_ms = start.elapsed().as_millis() as u64;

    match result {
        Ok(Ok(output)) => {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let stderr = String::from_utf8_lossy(&output.stderr);
            let (prompt_tps, gen_tps, params) = parse_bench_output(&stdout, &stderr);

            if gen_tps > 0.0 {
                Ok(BenchRun {
                    model_filename: model.filename.clone(),
                    fork: fork.name.clone(),
                    prompt_tps,
                    gen_tps,
                    params,
                    status: "success".into(),
                    details: None,
                    duration_ms,
                })
            } else {
                Ok(BenchRun {
                    model_filename: model.filename.clone(),
                    fork: fork.name.clone(),
                    prompt_tps: 0.0,
                    gen_tps: 0.0,
                    params: None,
                    status: "failed".into(),
                    details: Some(format!(
                        "No valid TPS. stderr: {}",
                        stderr.lines().last().unwrap_or("")
                    )),
                    duration_ms,
                })
            }
        }
        Ok(Err(e)) => Err(format!("llama-bench execution error: {}", e)),
        Err(_) => Err(format!("llama-bench timed out after {}ms", duration_ms)),
    }
}

fn parse_bench_output(stdout: &str, _stderr: &str) -> (f64, f64, Option<String>) {
    // llama-bench output: "pp 512 | tg 128 | ..." or table format
    let mut prompt_tps = 0.0_f64;
    let mut gen_tps = 0.0_f64;
    let params: Option<String> = None;

    for line in stdout.lines() {
        let l = line.trim();
        if l.contains("model") && l.contains("size") && l.contains("params") {
            // Header row in table format, capture params
            continue;
        }
        // "| model" -> table entry
        if l.starts_with("|") && l.contains("|") {
            let parts: Vec<&str> = l.split('|').map(|s| s.trim()).collect();
            if parts.len() >= 4 {
                for (i, p) in parts.iter().enumerate() {
                    if *p == "pp" || *p == "pp512" {
                        if let Ok(v) = parts.get(i + 1).unwrap_or(&"").parse::<f64>() {
                            prompt_tps = prompt_tps.max(v);
                        }
                    }
                    if *p == "tg" || *p == "tg128" {
                        if let Ok(v) = parts.get(i + 1).unwrap_or(&"").parse::<f64>() {
                            gen_tps = gen_tps.max(v);
                        }
                    }
                }
            }
        }
        // "pp 512: 123.45 t/s" format
        if let Some(v) = extract_stat(l, "pp") {
            prompt_tps = prompt_tps.max(v);
        }
        if let Some(v) = extract_stat(l, "tg") {
            gen_tps = gen_tps.max(v);
        }
    }

    if prompt_tps == 0.0 && gen_tps == 0.0 {
        // Try numeric extraction
        for line in stdout.lines() {
            if let Some(colon_pos) = line.find(':') {
                let right = line[colon_pos + 1..].trim();
                if let Ok(v) = right.split_whitespace().next().unwrap_or("").parse::<f64>() {
                    if gen_tps == 0.0 {
                        gen_tps = v;
                    }
                }
            }
        }
    }

    (prompt_tps, gen_tps, params)
}

fn extract_stat(line: &str, tag: &str) -> Option<f64> {
    let prefix = format!("{} ", tag);
    if let Some(pos) = line.find(&prefix) {
        let rest = &line[pos + prefix.len()..];
        // Look for number before "t/s" or at end
        for part in rest.split_whitespace() {
            if let Ok(v) = part
                .trim_end_matches(',')
                .trim_end_matches("t/s")
                .parse::<f64>()
            {
                return Some(v);
            }
        }
    }
    // "pp 512 | 123.45" format in table
    if line.contains(tag) {
        let parts: Vec<&str> = line.split('|').collect();
        for (i, part) in parts.iter().enumerate() {
            if part.contains(tag) && i + 1 < parts.len() {
                if let Ok(v) = parts[i + 1].trim().parse::<f64>() {
                    return Some(v);
                }
            }
        }
    }
    None
}

// ── Persistence ──────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BenchResults {
    pub runs: Vec<BenchRun>,
    pub updated_at: String,
}

pub fn results_path() -> PathBuf {
    PathBuf::from("/home/toxic/sovereign/tools/fleet/results/rust-bench.json")
}

pub fn load_results() -> BenchResults {
    let path = results_path();
    std::fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or(BenchResults {
            runs: Vec::new(),
            updated_at: String::new(),
        })
}

pub fn save_results(mut results: BenchResults) {
    results.updated_at = chrono_like_now();
    let path = results_path();
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let _ = std::fs::write(
        path,
        serde_json::to_string_pretty(&results).unwrap_or_default(),
    );
}

fn chrono_like_now() -> String {
    // Simple timestamp without chrono dependency
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| format!("{}", d.as_secs()))
        .unwrap_or_else(|_| "unknown".into())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_classify_fork_beellama() {
        assert_eq!(classify_fork("beellama/qwen-flash-96k"), "beellama");
    }

    #[test]
    fn test_classify_fork_turboquant() {
        assert_eq!(classify_fork("turboquant/heretic-27b-256k"), "turboquant");
    }

    #[test]
    fn test_classify_fork_ik_llama() {
        assert_eq!(classify_fork("ik_llama/heretic-ud-64k"), "ik_llama");
    }

    #[test]
    fn test_classify_fork_ik_turboquant() {
        assert_eq!(
            classify_fork("ik_turboquant/heretic-27b-256k"),
            "ik_turboquant"
        );
    }

    #[test]
    fn test_classify_quant_iq4xs() {
        assert_eq!(classify_quant("some-model-IQ4_XS.gguf"), "IQ4XS");
    }

    #[test]
    fn test_classify_quant_q4km() {
        assert_eq!(classify_quant("model-Q4_K_M.gguf"), "Q4KM");
    }

    #[test]
    fn test_classify_quant_tcq() {
        assert_eq!(classify_quant("model-tcq.gguf"), "TCQ");
    }

    #[test]
    fn test_extract_params_b() {
        assert_eq!(extract_params_b("qwen-flash-9b-iq4xs.gguf"), Some(9.0));
        assert_eq!(extract_params_b("heretic-27b-256k.gguf"), Some(27.0));
        assert_eq!(extract_params_b("gemma-4-12b.gguf"), Some(12.0));
        assert_eq!(extract_params_b("no-params.gguf"), None);
    }

    #[test]
    fn test_sovereign_forks() {
        let forks = soverign_forks();
        assert_eq!(forks.len(), 4);
        assert_eq!(forks[0].name, "beellama");
        assert_eq!(forks[3].name, "ik_turboquant");
    }

    #[test]
    fn test_parse_bench_output_numeric() {
        let stdout = "pp 512 | 123.45\ntg 128 | 45.67\n";
        let (pp, tg, _) = parse_bench_output(stdout, "");
        assert!(pp > 0.0 || tg > 0.0); // At least one should be parsed
    }

    #[test]
    fn test_load_results_empty() {
        let results = load_results();
        assert!(results.runs.is_empty());
    }
}
