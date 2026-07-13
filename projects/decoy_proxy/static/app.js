document.addEventListener("DOMContentLoaded", () => {
    const promptInput = document.getElementById("prompt-input");
    const btnTransform = document.getElementById("btn-transform");
    const decoyMethod = document.getElementById("decoy-method");
    const decoyPct = document.getElementById("decoy-pct");
    const outputBox = document.getElementById("output-box");

    // Stats elements
    const statRequests = document.getElementById("stat-requests");
    const statTokens = document.getElementById("stat-tokens");
    const statGas = document.getElementById("stat-gas");
    const statTax = document.getElementById("stat-tax");

    // Load stats
    async function loadStats() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();
            
            statRequests.textContent = data.totalRequests;
            statTokens.textContent = data.tokensSaved.toLocaleString();
            statGas.textContent = data.gasSavedTon.toFixed(1);
            statTax.textContent = `$${data.complianceTaxAvoidedUSD.toFixed(2)}`;
        } catch (err) {
            console.error("Error loading stats:", err);
        }
    }

    // Deploy Proxy
    btnTransform.addEventListener("click", async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            alert("Please type a prompt to proxy.");
            return;
        }

        const selectedProvider = document.querySelector('input[name="provider"]:checked').value;
        
        btnTransform.disabled = true;
        btnTransform.textContent = "TUNNELING...";
        outputBox.textContent = `[SYSTEM] Intercepting Tier 0 safety layer...\n[SYSTEM] Injecting decoy context vectors for ${selectedProvider}...\n[SYSTEM] Transmitting sub-semantic instructions...`;

        try {
            const res = await fetch("/api/proxy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: prompt,
                    provider: selectedProvider
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.error || "Proxy failed");
            }

            const data = await res.json();
            
            // Update UI details
            decoyMethod.textContent = data.decoyPrompt.substring(0, 45) + "...";
            decoyPct.textContent = `${data.complianceTaxSavedPercent}%`;
            outputBox.textContent = data.output;

            // Reload stats
            loadStats();
        } catch (err) {
            outputBox.textContent = `❌ Error: ${err.message}`;
        } finally {
            btnTransform.disabled = false;
            btnTransform.textContent = "Deploy Decoy Proxy";
        }
    });

    // Initial Load
    loadStats();
});
