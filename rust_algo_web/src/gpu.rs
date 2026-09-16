use std::process::Stdio;
use tokio::process::Command;

#[derive(Debug, Default, PartialEq)]
pub struct GpuMetrics {
    pub temperature: i32,
    pub power_draw: f32,
    pub fan_speed: i32,
    pub memory_used: i32,
    pub memory_total: i32,
    pub gpu_util: i32,
}

pub async fn fetch_gpu_metrics() -> Result<GpuMetrics, String> {
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(5),
        Command::new("nvidia-smi")
            .arg("--query-gpu=temperature.gpu,power.draw,fan.speed,memory.used,memory.total,utilization.gpu")
            .arg("--format=csv,noheader,nounits")
            .stdout(Stdio::piped())
            .output(),
    )
    .await;

    match result {
        Ok(Ok(output)) => {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                parse_nvidia_smi(&stdout)
            } else {
                Err("nvidia-smi failed".into())
            }
        }
        Ok(Err(e)) => Err(format!("Failed to execute nvidia-smi: {}", e)),
        Err(_) => Err("nvidia-smi timed out".into()),
    }
}

pub fn parse_nvidia_smi(output: &str) -> Result<GpuMetrics, String> {
    let parts: Vec<&str> = output.trim().split(',').map(|s| s.trim()).collect();
    if parts.len() < 6 {
        return Err("Unexpected nvidia-smi output format".into());
    }

    Ok(GpuMetrics {
        temperature: parts[0].parse().unwrap_or(0),
        power_draw: parts[1].parse().unwrap_or(0.0),
        fan_speed: parts[2].parse().unwrap_or(0),
        memory_used: parts[3].parse().unwrap_or(0),
        memory_total: parts[4].parse().unwrap_or(0),
        gpu_util: parts[5].parse().unwrap_or(0),
    })
}

pub fn render_prometheus_metrics(m: &GpuMetrics) -> String {
    format!(
        "# HELP fleet_gpu_temperature_celsius GPU core temperature\n\
         # TYPE fleet_gpu_temperature_celsius gauge\n\
         fleet_gpu_temperature_celsius {}\n\
         # HELP fleet_gpu_power_draw_watts GPU board power draw\n\
         # TYPE fleet_gpu_power_draw_watts gauge\n\
         fleet_gpu_power_draw_watts {}\n\
         # HELP fleet_gpu_fan_speed_percent GPU fan speed\n\
         # TYPE fleet_gpu_fan_speed_percent gauge\n\
         fleet_gpu_fan_speed_percent {}\n\
         # HELP fleet_gpu_memory_used_mb GPU memory used\n\
         # TYPE fleet_gpu_memory_used_mb gauge\n\
         fleet_gpu_memory_used_mb {}\n\
         # HELP fleet_gpu_memory_total_mb GPU memory total\n\
         # TYPE fleet_gpu_memory_total_mb gauge\n\
         fleet_gpu_memory_total_mb {}\n\
         # HELP fleet_gpu_utilization_percent GPU utilization\n\
         # TYPE fleet_gpu_utilization_percent gauge\n\
         fleet_gpu_utilization_percent {}\n",
        m.temperature, m.power_draw, m.fan_speed, m.memory_used, m.memory_total, m.gpu_util
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_nvidia_smi_valid() {
        let output = "45, 120.5, 30, 4096, 24576, 50";
        let metrics = parse_nvidia_smi(output).unwrap();
        assert_eq!(
            metrics,
            GpuMetrics {
                temperature: 45,
                power_draw: 120.5,
                fan_speed: 30,
                memory_used: 4096,
                memory_total: 24576,
                gpu_util: 50,
            }
        );
    }

    #[test]
    fn test_parse_nvidia_smi_invalid() {
        let output = "45, 120.5";
        assert!(parse_nvidia_smi(output).is_err());
    }

    #[test]
    fn test_parse_nvidia_smi_fallbacks() {
        let output = "invalid, invalid, invalid, invalid, invalid, invalid";
        let metrics = parse_nvidia_smi(output).unwrap();
        assert_eq!(
            metrics,
            GpuMetrics {
                temperature: 0,
                power_draw: 0.0,
                fan_speed: 0,
                memory_used: 0,
                memory_total: 0,
                gpu_util: 0,
            }
        );
    }

    #[test]
    fn test_render_prometheus_metrics() {
        let metrics = GpuMetrics {
            temperature: 45,
            power_draw: 120.5,
            fan_speed: 30,
            memory_used: 4096,
            memory_total: 24576,
            gpu_util: 50,
        };
        let rendered = render_prometheus_metrics(&metrics);
        assert!(rendered.contains("fleet_gpu_temperature_celsius 45"));
        assert!(rendered.contains("fleet_gpu_power_draw_watts 120.5"));
    }

    #[tokio::test]
    async fn test_fetch_gpu_metrics_success() {
        use std::fs::File;
        use std::io::Write;
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = std::env::temp_dir().join("mock_nvidia_smi_success");
        std::fs::create_dir_all(&temp_dir).unwrap();
        let mock_script_path = temp_dir.join("nvidia-smi");

        let mut f = File::create(&mock_script_path).unwrap();
        writeln!(f, "#!/bin/sh").unwrap();
        writeln!(f, "echo '45, 120.5, 30, 4096, 24576, 50'").unwrap();

        let mut perms = std::fs::metadata(&mock_script_path).unwrap().permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&mock_script_path, perms).unwrap();

        // Save original PATH
        let original_path = std::env::var_os("PATH").unwrap_or_default();
        // Set new PATH
        let mut new_path = temp_dir.to_string_lossy().into_owned();
        new_path.push(':');
        new_path.push_str(&original_path.to_string_lossy());
        std::env::set_var("PATH", new_path);

        let res = fetch_gpu_metrics().await;

        // Restore PATH
        std::env::set_var("PATH", original_path);
        // Clean up
        let _ = std::fs::remove_dir_all(temp_dir);

        assert!(res.is_ok());
        let metrics = res.unwrap();
        assert_eq!(metrics.temperature, 45);
        assert_eq!(metrics.power_draw, 120.5);
    }

    #[tokio::test]
    async fn test_fetch_gpu_metrics_fail() {
        use std::fs::File;
        use std::io::Write;
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = std::env::temp_dir().join("mock_nvidia_smi_fail");
        std::fs::create_dir_all(&temp_dir).unwrap();
        let mock_script_path = temp_dir.join("nvidia-smi");

        let mut f = File::create(&mock_script_path).unwrap();
        writeln!(f, "#!/bin/sh").unwrap();
        writeln!(f, "exit 1").unwrap();

        let mut perms = std::fs::metadata(&mock_script_path).unwrap().permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&mock_script_path, perms).unwrap();

        // Save original PATH
        let original_path = std::env::var_os("PATH").unwrap_or_default();
        // Set new PATH
        let mut new_path = temp_dir.to_string_lossy().into_owned();
        new_path.push(':');
        new_path.push_str(&original_path.to_string_lossy());
        std::env::set_var("PATH", new_path);

        let res = fetch_gpu_metrics().await;

        // Restore PATH
        std::env::set_var("PATH", original_path);
        // Clean up
        let _ = std::fs::remove_dir_all(temp_dir);

        assert!(res.is_err());
        assert_eq!(res.unwrap_err(), "nvidia-smi failed");
    }

    #[tokio::test]
    async fn test_fetch_gpu_metrics_timeout() {
        use std::fs::File;
        use std::io::Write;
        use std::os::unix::fs::PermissionsExt;

        let temp_dir = std::env::temp_dir().join("mock_nvidia_smi_timeout");
        std::fs::create_dir_all(&temp_dir).unwrap();
        let mock_script_path = temp_dir.join("nvidia-smi");

        let mut f = File::create(&mock_script_path).unwrap();
        writeln!(f, "#!/bin/sh").unwrap();
        writeln!(f, "sleep 10").unwrap();

        let mut perms = std::fs::metadata(&mock_script_path).unwrap().permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(&mock_script_path, perms).unwrap();

        // Save original PATH
        let original_path = std::env::var_os("PATH").unwrap_or_default();
        // Set new PATH
        let mut new_path = temp_dir.to_string_lossy().into_owned();
        new_path.push(':');
        new_path.push_str(&original_path.to_string_lossy());
        std::env::set_var("PATH", new_path);

        let res = fetch_gpu_metrics().await;

        // Restore PATH
        std::env::set_var("PATH", original_path);
        // Clean up
        let _ = std::fs::remove_dir_all(temp_dir);

        assert!(res.is_err());
        assert_eq!(res.unwrap_err(), "nvidia-smi timed out");
    }

    #[tokio::test]
    async fn test_fetch_gpu_metrics_not_found() {
        let original_path = std::env::var_os("PATH").unwrap_or_default();
        std::env::set_var("PATH", "");

        let res = fetch_gpu_metrics().await;

        std::env::set_var("PATH", original_path);

        assert!(res.is_err());
        let err = res.as_ref().unwrap_err();
        assert!(
            err.contains("Failed to execute nvidia-smi") || err.contains("nvidia-smi timed out")
        );
    }
}
