**Complete Plan**

**Already done:**
- Searched for `acp-install.mjs` in `/home/toxic/sovereign` using `find`; no matches found.

**Remaining execution-order steps:**

1. **Broaden file search for similar names/extensions**  
   - Command: `find /home/toxic/sovereign -type f -name "acp-install.*" 2>/dev/null`  
   - Expected output: List of files like `acp-install.js`, `acp-install.ts`, etc., if any exist.  
   - Verification: If found, note paths and examine content; if not, proceed to step 2.

2. **Search for textual references to "acp-install"**  
   - Command: `grep -r "acp-install" /home/toxic/sovereign --include="*.js" --include="*.mjs" --include="*.ts" --include="*.json" --include="*.md" 2>/dev/null | head -30`  
   - Expected output: Lines showing where "acp-install" appears (e.g., in scripts, configs, docs).  
   - Verification: Analyze context to infer purpose (installation script, package name, etc.); if no references, consider alternative naming (e.g., "install-acp").

3. **Inspect project manifest and lock files**  
   - Command: `ls -la /home/toxic/sovereign/{package.json,package-lock.json,yarn.lock,pnpm-lock.yaml} 2>/dev/null`  
   - Expected output: Existence of manifest files.  
   - Verification: If `package.json` exists, read it to identify ACP-related dependencies or scripts (e.g., `"scripts": { "install-acp": "..." }`).

4. **Review installation/documentation files**  
   - Command: `find /home/toxic/sovereign -maxdepth 3 -type f \( -name "README*" -o -name "INSTALL*" -o -name "docs/*" -o -name "*.md" \) 2>/dev/null | head -10`  
   - Expected output: List of documentation files.  
   - Verification: Skim relevant files (e.g., `README.md`) for instructions on installing ACP or running `acp-install.mjs`.

5. **Locate or generate the install script**  
   - Based on prior findings:  
     - If references point to a missing script, check if it should be fetched from a URL or generated via a template (e.g., in `scripts/` directory).  
     - If no references exist, search for ACP installation instructions in docs to deduce manual steps.  
   - Verification: Confirm the script’s presence and correctness (e.g., valid JS/MJS syntax, executable flag if needed).

6. **Validate and execute the installation**  
   - Command: If script found, run `node /path/to/acp-install.mjs --help` or similar to verify usability.  
   - Expected output: Usage information or successful execution without errors.  
   - Verification: Check for post-installation artifacts (e.g., installed packages, generated config, or service status) as described in the script or docs.

**Risks and edge cases:**
- The file might be named differently (e.g., `install-acp.mjs`, `acp-installer.mjs`).  
- The script might reside in a non-obvious location (e.g., `tools/`, `scripts/`, `bin/`).  
- Installation might require specific environment variables, permissions, or dependencies (e.g., Node.js version).  
- If the script is missing, we may need to reconstruct it from documentation or external sources, risking inaccuracies.  
- Verification must avoid false positives; rely on explicit success indicators from the script/docs rather than assumptions.

**Next steps after plan:**  
Use `todo` tool to capture concrete, verifiable actions (5–9 items) for execution.

---

**Todo List (5–9 meaningful steps)**  
Initialized with concrete targets and verification criteria:  

1. **Search for acp-install.* files**  
   - Command: `find /home/toxic/sovereign -type f -name "acp-install.*" 2>/dev/null`  
   - Verify: Output lists candidate files; if none, proceed to step 2.  

2. **Search for textual references to "acp-install"**  
   - Command: `grep -r "acp-install" /home/toxic/sovereign --include="*.js" --include="*.mjs" --include="*.ts" --include="*.json" --include="*.md" 2>/dev/null | head -30`  
   - Verify: Output shows context (e.g., file paths and surrounding lines); if empty, consider alternative search terms.  

3. **Examine package.json for ACP-related scripts**  
   - Command: `cat /home/toxic/sovereign/package.json 2>/dev/null`  
   - Verify: If file exists, inspect `"scripts"` and `"dependencies"` for ACP; note any relevant entries.  

4. **Check for installation documentation**  
   - Command: `grep -i "acp\|install" /home/toxic/sovereign/README.md 2>/dev/null | head -10`  
   - Verify: Output contains actionable steps or references to acp-install.mjs.  

5. **Determine and verify the install script location**  
   - Based on steps 1–4: Either confirm path to existing script or decide to create/fetch it.  
   - Verify: Script exists at expected path and is readable; if creating, ensure content matches documented purpose.  

6. **Validate script syntax and executability**  
   - Command: `node -c /path/to/acp-install.mjs 2>&1 && echo "Syntax OK"`  
   - Verify: Output includes "Syntax OK" (or equivalent) and no errors; set executable flag if needed (`chmod +x`).  

7. **Execute installation and check for success**  
   - Command: `/path/to/acp-install.mjs [expected args] 2>&1 | tail -20`  
   - Verify: Output indicates successful installation (e.g., "Installed ACP", no fatal errors); check for expected side effects (e.g., new directory, package).  

8. **Confirm installation via artifact verification**  
   - Command: `test -f /expected/artifact && echo "Artifact found"` (based on script/docs)  
   - Verify: Artifact exists; if not, re-examine installation output for clues.  

*(Adjust number of items as needed; each step is concrete, verifiable, and tied to code execution or validation.)*  

Proceed to execute these steps after this reply.





