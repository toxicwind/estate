document.addEventListener("DOMContentLoaded", () => {
    const modelList = document.getElementById("model-list");
    const runsList = document.getElementById("runs-list");
    const btnRun = document.getElementById("btn-run");
    const progressBox = document.getElementById("progress-box");
    const progressBar = document.getElementById("progress-bar");
    const progressStatus = document.getElementById("progress-status");
    const consoleLog = document.getElementById("console-log");

    const diagPrompt = document.getElementById("diag-prompt");
    const diagGen = document.getElementById("diag-gen");
    const diagVram = document.getElementById("diag-vram");

    let selectedModelId = "";

    // Load models
    async function loadModels() {
        try {
            const res = await fetch("/api/models");
            const models = await res.json();

            if (models.length === 0) {
                modelList.innerHTML = `<li class="loading">No models defined in llama-swap config.yaml</li>`;
                return;
            }

            modelList.innerHTML = "";
            models.forEach(model => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <span class="model-name">${model.modelId}</span>
                    <span class="model-size">context: ${model.metadata.context || "default"} | fork: ${model.metadata.fork || "default"}</span>
                `;
                li.addEventListener("click", () => selectModel(model, li));
                modelList.appendChild(li);
            });
            logMessage("Ready. Select a model configuration to run benchmarks.");
        } catch (err) {
            logMessage(`Error loading configurations: ${err.message}`, "error");
        }
    }

    // Load runs history
    async function loadRuns() {
        try {
            const res = await fetch("/api/runs");
            const runs = await res.json();

            runsList.innerHTML = "";
            runs.forEach(run => {
                const li = document.createElement("li");
                const timeStr = new Date(run.timestamp).toLocaleTimeString();
                li.innerHTML = `
                    <div class="run-header">
                        <span>${run.modelId}</span>
                        <span class="model-size">${timeStr}</span>
                    </div>
                    <div class="run-metrics">
                        <span>Prompt: ${run.promptTps} t/s</span>
                        <span>Gen: ${run.genTps} t/s</span>
                        <span>VRAM: ${(run.vramUsedMb / 1024).toFixed(1)} GB</span>
                    </div>
                `;
                runsList.appendChild(li);
            });
        } catch (err) {
            console.error("Error loading run history:", err);
        }
    }

    function selectModel(model, element) {
        document.querySelectorAll("#model-list li").forEach(li => li.classList.remove("active"));
        element.classList.add("active");

        selectedModelId = model.modelId;
        btnRun.disabled = false;

        logMessage(`Selected [${selectedModelId}]. Prepared cmd: "${model.cmd.substring(0, 100)}..."`);
    }

    // Run benchmark
    btnRun.addEventListener("click", async () => {
        if (!selectedModelId) return;

        btnRun.disabled = true;
        progressBox.classList.remove("hidden");
        progressBar.style.width = "10%";
        progressStatus.textContent = "Spinning up profiling context...";

        logMessage(`Deploying profiler run for ${selectedModelId}...`);

        try {
            await delay(400);
            progressBar.style.width = "40%";
            progressStatus.textContent = "Executing graduated context probes...";

            await delay(400);
            progressBar.style.width = "75%";
            progressStatus.textContent = "Measuring active VRAM Footprint...";

            const res = await fetch("/api/benchmark", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ modelId: selectedModelId })
            });

            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || "Benchmark run failed");
            }

            const run = await res.json();

            progressBar.style.width = "100%";
            progressStatus.textContent = "Done!";

            // Update stats
            diagPrompt.textContent = `${run.promptTps} t/s`;
            diagGen.textContent = `${run.genTps} t/s`;
            diagVram.textContent = `${(run.vramUsedMb / 1024).toFixed(1)} GB`;

            logMessage(`✅ Successfully completed run. Prompt PP: ${run.promptTps} t/s. Gen TG: ${run.genTps} t/s.`);
            if (run.details) {
                consoleLog.textContent += `\n\n--- CLI Output Preview ---\n${run.details}\n--------------------------`;
            }

            await delay(600);
            progressBox.classList.add("hidden");
            btnRun.disabled = false;

            loadRuns();
        } catch (err) {
            progressBar.style.width = "100%";
            progressBar.style.backgroundColor = "#ef4444";
            progressStatus.textContent = "Error!";
            logMessage(`❌ Benchmark failed: ${err.message}`, "error");

            await delay(2000);
            progressBox.classList.add("hidden");
            progressBar.style.backgroundColor = "var(--secondary-color)";
            btnRun.disabled = false;
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
    loadRuns();
});
