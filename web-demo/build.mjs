import { cp, mkdir, rm } from "node:fs/promises";

await rm("dist", { recursive: true, force: true });
await mkdir("dist/public", { recursive: true });
await Promise.all([
  cp("index.html", "dist/index.html"),
  cp("app.js", "dist/app.js"),
  cp("style.css", "dist/style.css"),
  cp("public/demo-data.json", "dist/public/demo-data.json"),
]);

console.log("Built dist/ with the review UI and generated workflow data.");
