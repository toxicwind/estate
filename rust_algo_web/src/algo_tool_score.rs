use serde::{Serialize, Deserialize};
use std::cmp::Ordering;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Weights {
    pub nix_overhead: f32, // 10 = zero nix dependency, 0 = pure nix coding
    pub tui_gui_polish: f32,
    pub performance: f32,
    pub setup_speed: f32,
    pub orchestration: f32,
    pub portability: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolScore {
    pub name: String,
    pub description: String,
    pub website: String,
    pub scores: CriteriaScores,
    pub weighted_score: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriteriaScores {
    pub nix_overhead: f32,
    pub tui_gui_polish: f32,
    pub performance: f32,
    pub setup_speed: f32,
    pub orchestration: f32,
    pub portability: f32,
}

pub fn get_tools() -> Vec<ToolScore> {
    vec![
        ToolScore {
            name: "Devbox (Jetify)".to_string(),
            description: "JSON-driven environment config powered by Nix, offering zero-nix-knowledge environments and simple service orchestration.".to_string(),
            website: "https://www.jetify.com/devbox".to_string(),
            scores: CriteriaScores {
                nix_overhead: 8.0,
                tui_gui_polish: 7.0,
                performance: 8.5,
                setup_speed: 8.0,
                orchestration: 7.0,
                portability: 8.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Flox".to_string(),
            description: "High-performance Nix-based environment profiles with CLI package installs and native service runtimes.".to_string(),
            website: "https://flox.dev".to_string(),
            scores: CriteriaScores {
                nix_overhead: 9.0,
                tui_gui_polish: 6.0,
                performance: 8.5,
                setup_speed: 8.5,
                orchestration: 6.5,
                portability: 8.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Mise-en-place".to_string(),
            description: "Universal developer tool manager, env-var manager, and parallel task executor written in Rust (zero Nix requirement).".to_string(),
            website: "https://mise.jdx.dev".to_string(),
            scores: CriteriaScores {
                nix_overhead: 10.0,
                tui_gui_polish: 7.0,
                performance: 9.5,
                setup_speed: 9.0,
                orchestration: 8.0,
                portability: 10.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Devcontainers & DevPod".to_string(),
            description: "Containerized environments using devcontainer.json, offering standard development packages with Docker compose services.".to_string(),
            website: "https://devpod.sh".to_string(),
            scores: CriteriaScores {
                nix_overhead: 10.0,
                tui_gui_polish: 9.0,
                performance: 4.5,
                setup_speed: 6.0,
                orchestration: 6.0,
                portability: 9.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "numtide/devshell".to_string(),
            description: "Declarative development environments built directly inside the Nix Flake module ecosystem, with menu-driven commands.".to_string(),
            website: "https://github.com/numtide/devshell".to_string(),
            scores: CriteriaScores {
                nix_overhead: 2.0,
                tui_gui_polish: 5.0,
                performance: 8.5,
                setup_speed: 5.0,
                orchestration: 5.5,
                portability: 7.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Daytona".to_string(),
            description: "Self-hosted, open-source developer workspace manager. Automates development tooling and processes across local or remote clouds.".to_string(),
            website: "https://www.daytona.io".to_string(),
            scores: CriteriaScores {
                nix_overhead: 10.0,
                tui_gui_polish: 8.0,
                performance: 6.0,
                setup_speed: 7.0,
                orchestration: 7.0,
                portability: 9.5,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Nix Flakes + direnv + Overmind".to_string(),
            description: "Advanced custom combination. Nix Flakes manage packages, direnv loads them auto-magically, and Overmind runs Procfile tasks in Tmux.".to_string(),
            website: "https://github.com/DarthSim/overmind".to_string(),
            scores: CriteriaScores {
                nix_overhead: 3.0,
                tui_gui_polish: 8.0,
                performance: 8.0,
                setup_speed: 5.0,
                orchestration: 9.5,
                portability: 7.0,
            },
            weighted_score: 0.0,
        },
        ToolScore {
            name: "Tilt".to_string(),
            description: "Interactive local development orchestrator that rebuilds, redeploys, and serves a beautiful web dashboard monitoring log outputs.".to_string(),
            website: "https://tilt.dev".to_string(),
            scores: CriteriaScores {
                nix_overhead: 10.0,
                tui_gui_polish: 10.0,
                performance: 5.5,
                setup_speed: 6.5,
                orchestration: 10.0,
                portability: 9.0,
            },
            weighted_score: 0.0,
        },
    ]
}

pub fn rank_tools(weights: Weights) -> Vec<ToolScore> {
    let mut tools = get_tools();
    
    // Normalize weights to sum to 1.0 (or just run standard weighted sum)
    let sum = weights.nix_overhead + weights.tui_gui_polish + weights.performance + 
              weights.setup_speed + weights.orchestration + weights.portability;
              
    let w = if sum > 0.0 {
        Weights {
            nix_overhead: weights.nix_overhead / sum,
            tui_gui_polish: weights.tui_gui_polish / sum,
            performance: weights.performance / sum,
            setup_speed: weights.setup_speed / sum,
            orchestration: weights.orchestration / sum,
            portability: weights.portability / sum,
        }
    } else {
        Weights {
            nix_overhead: 1.0 / 6.0,
            tui_gui_polish: 1.0 / 6.0,
            performance: 1.0 / 6.0,
            setup_speed: 1.0 / 6.0,
            orchestration: 1.0 / 6.0,
            portability: 1.0 / 6.0,
        }
    };

    for tool in &mut tools {
        let score = (tool.scores.nix_overhead * w.nix_overhead) +
                    (tool.scores.tui_gui_polish * w.tui_gui_polish) +
                    (tool.scores.performance * w.performance) +
                    (tool.scores.setup_speed * w.setup_speed) +
                    (tool.scores.orchestration * w.orchestration) +
                    (tool.scores.portability * w.portability);
                    
        // Scale to 0-100% for readability
        tool.weighted_score = (score * 10.0).round();
    }

    // Sort descending by weighted score
    tools.sort_by(|a, b| b.weighted_score.partial_cmp(&a.weighted_score).unwrap_or(Ordering::Equal));
    
    tools
}
