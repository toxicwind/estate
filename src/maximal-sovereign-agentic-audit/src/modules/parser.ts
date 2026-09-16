import { readFileSync } from "fs";
import { PROJECTS_ENV, PROJECTS_DIR, SOVEREIGN_DIR } from "./constants.js";

export function parseProjectsEnvSync(): string[] {
  try {
    const content = readFileSync(PROJECTS_ENV, "utf8");
    const paths: string[] = [];
    for (const line of content.split("\n").filter((l) => l.trim() !== "" && !l.startsWith("#"))) {
      const [, value] = line.split("=", 2);
      if (value) {
        const path = value.split(":")[0];
        if (path) paths.push(path);
      }
    }
    return paths;
  } catch (error) {
    console.warn(`Failed to parse ${PROJECTS_ENV}: ${error.message}`);
    return [PROJECTS_DIR, SOVEREIGN_DIR];
  }
}
