use serde::{Serialize, Deserialize};
use reqwest::Client;
use crate::algo::Weights;

const LLM_PROXY_URL: &str = "http://127.0.0.1:25008/v1/chat/completions";

#[derive(Serialize, Deserialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct ChatCompletionRequest {
    model: String,
    messages: Vec<ChatMessage>,
    temperature: f32,
    max_tokens: usize,
}

#[derive(Deserialize)]
struct ChatChoice {
    message: ChatMessage,
}

#[derive(Deserialize)]
struct ChatCompletionResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct AdvisorRequest {
    pub prompt: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AdvisorResponse {
    pub weights: Weights,
    #[serde(default)]
    pub explanation: String,
}

pub async fn consult_advisor(req: AdvisorRequest) -> Result<AdvisorResponse, String> {
    let client = Client::new();

    let system_instructions = 
        "You are an expert DevOps Advisor. The user is trying to find the perfect developer environment \
         and process manager manager tool. Your job is to parse their description of their project, preferences, \
         and constraints, and suggest weights for 6 scoring criteria:\n\
         - nix_overhead: 1.0 means 'I hate Nix / want zero Nix dependency', 0.0 means 'I am happy with deep Nix Flakes coding'\n\
         - tui_gui_polish: 1.0 means 'I want a rich web dashboard, terminal multiplexer, or TUI', 0.0 means 'Plain CLI output is fine'\n\
         - performance: 1.0 means 'Extremely lightweight, native speed, low RAM/resource use', 0.0 means 'Happy with Docker VMs/heavy containers'\n\
         - setup_speed: 1.0 means 'I want zero configuration/instant init', 0.0 means 'Happy to write long config files/Dockerfiles'\n\
         - orchestration: 1.0 means 'I need a robust process manager that watches files and restarts servers', 0.0 means 'Only need a basic shell run command'\n\
         - portability: 1.0 means 'Must work seamlessly across macOS, Linux, Windows without prerequisites', 0.0 means 'Platform-specific is fine'\n\n\
         You MUST reply in valid JSON format only, matching this structure:\n\
         {\n\
           \"weights\": {\n\
             \"nix_overhead\": 0.8,\n\
             \"tui_gui_polish\": 0.5,\n\
             \"performance\": 0.9,\n\
             \"setup_speed\": 0.7,\n\
             \"orchestration\": 0.8,\n\
             \"portability\": 0.6\n\
           },\n\
           \"explanation\": \"Based on your request, I recommend...\"\n\
         }\n\n\
         Do not include any markup other than JSON in your response. Ensure all weight values are between 0.0 and 1.0.";

    let prompt = format!(
        "User description of project requirements:\n\n\
         \"{}\"\n\n\
         Suggest weights and explain your choices.",
        req.prompt
    );

    let body = ChatCompletionRequest {
        model: "qwen3.6-27b".to_string(),
        messages: vec![
            ChatMessage {
                role: "system".to_string(),
                content: system_instructions.to_string(),
            },
            ChatMessage {
                role: "user".to_string(),
                content: prompt,
            },
        ],
        temperature: 0.3,
        max_tokens: 1024,
    };

    match client.post(LLM_PROXY_URL).json(&body).send().await {
        Ok(resp) => {
            if resp.status().is_success() {
                match resp.json::<ChatCompletionResponse>().await {
                    Ok(res) => {
                        if let Some(choice) = res.choices.first() {
                            parse_llm_json(&choice.message.content)
                        } else {
                            Err("No choices returned from LLM".to_string())
                        }
                    }
                    Err(e) => Err(format!("Failed to parse LLM response: {}", e)),
                }
            } else {
                Err(format!("LLM proxy HTTP error: {}", resp.status()))
            }
        }
        Err(e) => Err(format!("Failed to connect to LLM proxy: {}", e)),
    }
}

fn parse_llm_json(content: &str) -> Result<AdvisorResponse, String> {
    // Extract the first complete JSON object from the content
    if let Some(json_obj) = extract_json_object(content) {
        let cleaned_json = clean_json_commas(&json_obj);
        match serde_json::from_str::<AdvisorResponse>(&cleaned_json) {
            Ok(parsed) => Ok(parsed),
            Err(e) => Err(format!(
                "Failed to parse JSON structure from LLM content: {} (Extracted: {})",
                e, cleaned_json
            )),
        }
    } else {
        Err(format!(
            "Could not find a valid JSON object in the LLM response (Raw: {})",
            content
        ))
    }
}

fn clean_json_commas(input: &str) -> String {
    let mut result = String::with_capacity(input.len());
    let mut chars = input.chars().peekable();
    let mut in_string = false;
    let mut escape = false;

    while let Some(c) = chars.next() {
        if escape {
            result.push(c);
            escape = false;
            continue;
        }
        if c == '\\' && in_string {
            result.push(c);
            escape = true;
            continue;
        }
        if c == '"' {
            in_string = !in_string;
        }
        
        if c == ',' && !in_string {
            // Check if the next non-whitespace characters are '}' or ']'
            let mut temp = chars.clone();
            let mut is_trailing = false;
            while let Some(&next_c) = temp.peek() {
                if next_c.is_whitespace() {
                    temp.next();
                } else if next_c == '}' || next_c == ']' {
                    is_trailing = true;
                    break;
                } else {
                    break;
                }
            }
            if is_trailing {
                // Skip the comma
                continue;
            }
        }
        result.push(c);
    }
    result
}

fn extract_json_object(input: &str) -> Option<String> {
    let clean_input = input.split("<end_of_turn>").next().unwrap_or(input);
    let clean_input = clean_input.split("<start_of_turn>").next().unwrap_or(clean_input);

    let start_idx = clean_input.find('{')?;
    let mut depth = 0;
    let mut in_string = false;
    let mut escape = false;
    let mut last_valid_idx = start_idx;

    for (i, c) in clean_input[start_idx..].char_indices() {
        let current_idx = start_idx + i;
        if escape {
            escape = false;
            continue;
        }
        match c {
            '\\' => {
                if in_string {
                    escape = true;
                }
            }
            '"' => {
                in_string = !in_string;
            }
            '{' => {
                if !in_string {
                    depth += 1;
                }
            }
            '}' => {
                if !in_string {
                    depth -= 1;
                    if depth == 0 {
                        return Some(clean_input[start_idx..=current_idx].to_string());
                    }
                }
            }
            _ => {}
        }
        if !in_string {
            last_valid_idx = current_idx;
        }
    }

    // Recovery if depth > 0
    if depth > 0 {
        let mut sub = clean_input[start_idx..=last_valid_idx].trim().to_string();
        if sub.ends_with(',') {
            sub.pop();
        }
        let sub = sub.trim();
        let mut closed = sub.to_string();
        for _ in 0..depth {
            closed.push('}');
        }
        return Some(closed);
    }
    None
}
