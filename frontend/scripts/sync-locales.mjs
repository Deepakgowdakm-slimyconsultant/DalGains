// Copies src/i18n/locales/*.json (the single source of truth, owned by
// the backend's src/i18n/loader.py) into frontend/public/locales/<lng>/
// translation.json so react-i18next's http backend can fetch them at
// runtime. Runs before dev/build -- frontend/public/locales is generated,
// not hand-maintained, and is gitignored.
import { readdirSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const sourceDir = fileURLToPath(new URL("../../src/i18n/locales", import.meta.url));
const targetRoot = fileURLToPath(new URL("../public/locales", import.meta.url));

for (const file of readdirSync(sourceDir)) {
  if (!file.endsWith(".json")) continue;
  const locale = file.replace(/\.json$/, "");
  const contents = readFileSync(`${sourceDir}/${file}`, "utf-8");
  const targetDir = `${targetRoot}/${locale}`;
  mkdirSync(targetDir, { recursive: true });
  writeFileSync(`${targetDir}/translation.json`, contents);
  console.log(`synced ${locale} -> public/locales/${locale}/translation.json`);
}
