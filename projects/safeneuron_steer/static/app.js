document.addEventListener("DOMContentLoaded", () => {
    const modelList = document.getElementById("model-list");
    const tensorSelect = document.getElementById("tensor-select");
    const scaleSlider = document.getElementById("scale-slider");
    const scaleValue = document.getElementById("scale-value");
    const btnSteer = document.getElementById("btn-steer");
    const progressBox = document.getElementById("progress-box");
    const progressBar = document.getElementById("progress-bar");
    const progressStatus = document.getElementById("progress-status");
    const consoleLog = document.getElementById("console-log");

    const statTensors = document.getElementById("stat-tensors");
    const statAlign = document.getElementById("stat-align");
    const statVersion = document.getElementById("stat-version");

    let activeModelPath = "";
    let activeModelName = "";

    // Sync slider value
    scaleSlider.addEventListener("input", (e) => {
        scaleValue.textContent = parseFloat(e.target.value).toFixed(2);
    });

    // Load models list
    async function loadModels() {
        try {
            const res = await fetch("/api/models");
            const models = await res.json();
            
            if (models.length === 0) {
                modelList.innerHTML = `<li class="loading">No GGUF models found in /home/toxic/models</li>`;
                return;
            }

            modelList.innerHTML = "";
            models.forEach(model => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span class="model-name">${model.name}</span>
                    <span class="model-size">${(model.size / (1024 * 1024 * 1024)).toFixed(2)} GB</span>
                `;
                li.addEventListener("click", () => selectModel(model, li));
                modelList.appendChild(li);
            });
            logMessage("System ready. Select a model to begin analysis.");
        } catch (err) {
            logMessage(`Error loading models: ${err.message}`, "error");
        }
    }

    // Select model and inspect it
    async function selectModel(model, element) {
        // Toggle active class
        document.querySelectorAll("#model-list li").forEach(li => li.classList.remove("active"));
        element.classList.add("active");

        activeModelPath = model.path;
        activeModelName = model.name;

        logMessage(`Loading and parsing metadata for ${activeModelName}...`);
        
        // Reset controls
        tensorSelect.disabled = true;
        scaleSlider.disabled = true;
        btnSteer.disabled = true;
        tensorSelect.innerHTML = `<option value="">Parsing GGUF header...</option>`;

        try {
            const res = await fetch(`/api/inspect?path=${encodeURIComponent(activeModelPath)}`);
            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || "Failed to inspect model");
            }
            const info = await res.json();

            // Populate stats
            statTensors.textContent = info.tensor_count;
            statAlign.textContent = `${info.alignment}B`;
            statVersion.textContent = `v${info.version}`;

            // Filter relevant steering tensors (gate, up, down, attention outputs)
            const steerTensors = info.tensors.filter(t => 
                t.name.includes("ffn_gate") || 
                t.name.includes("ffn_down") || 
                t.name.includes("ffn_up") || 
                t.name.includes("attn_output") ||
                t.name.includes("attn_q")
            );

            tensorSelect.innerHTML = `<option value="">-- Select a target tensor --</option>`;
            steerTensors.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t.name;
                opt.textContent = `${t.name} (type: ${t.tensor_type}, size: ${(t.size_bytes / 1024).toFixed(1)} KB)`;
                tensorSelect.appendChild(opt);
            });

            tensorSelect.disabled = false;
            scaleSlider.disabled = false;
            btnSteer.disabled = false;
            
            logMessage(`✅ Successfully parsed ${activeModelName}.`);
            logMessage(`Found ${info.tensor_count} total tensors; ${steerTensors.length} candidates eligible for de-alignment steering.`);
        } catch (err) {
            logMessage(`❌ Parser Error: ${err.message}`, "error");
            tensorSelect.innerHTML = `<option value="">Failed to inspect model</option>`;
            statTensors.textContent = "--";
            statAlign.textContent = "--";
            statVersion.textContent = "--";
        }
    }

    // Apply patch
    btnSteer.addEventListener("click", async () => {
        const tensorName = tensorSelect.value;
        if (!tensorName) {
            alert("Please select a target tensor to steer.");
            return;
        }

        const scale = parseFloat(scaleSlider.value);
        logMessage(`Initiating surgical patch on [${tensorName}] with scale factor ${scale.toFixed(2)}...`);

        // UI states
        btnSteer.disabled = true;
        progressBox.classList.remove("hidden");
        progressBar.style.width = "20%";
        progressStatus.textContent = "Locating tensor offset...";

        try {
            // Step 1 simulation interval
            await delay(400);
            progressBar.style.width = "50%";
            progressStatus.textContent = "Writing byte modifications in-place...";

            const res = await fetch("/api/steer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model_path: activeModelPath,
                    tensor_name: tensorName,
                    scale: scale
                })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || "Steering operation failed");
            }

            const data = await res.json();
            progressBar.style.width = "100%";
            progressStatus.textContent = "Completed successfully!";
            logMessage(`✅ ${data.message || "Surgical patch successfully applied."}`);
            
            await delay(600);
            progressBox.classList.add("hidden");
            btnSteer.disabled = false;
        } catch (err) {
            progressBar.style.width = "100%";
            progressBar.style.backgroundColor = "#ff3333";
            progressStatus.textContent = "Failed!";
            logMessage(`❌ Error applying patch: ${err.message}`, "error");
            
            await delay(2000);
            progressBox.classList.add("hidden");
            progressBar.style.backgroundColor = "var(--primary-color)";
            btnSteer.disabled = false;
        }
    });

    function logMessage(msg, type = "info") {
        const timestamp = new Date().toISOString().split("T")[1].substring(0, 8);
        const prefix = type === "error" ? "[ERR]" : "[SYS]";
        consoleLog.textContent += `\n[${timestamp}] ${prefix} ${msg}`;
        consoleLog.scrollTop = consoleLog.scrollHeight;
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Init
    loadModels();
});
