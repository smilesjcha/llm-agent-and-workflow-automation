import { cp, mkdir, rm } from "node:fs/promises";

await rm("dist", { recursive: true, force: true });
await mkdir("dist/public/course-demos", { recursive: true });
await Promise.all([
  cp("index.html", "dist/index.html"),
  cp("app.js", "dist/app.js"),
  cp("style.css", "dist/style.css"),
  cp("course.html", "dist/course.html"),
  cp("course.js", "dist/course.js"),
  cp("course.css", "dist/course.css"),
  cp("public/demo-data.json", "dist/public/demo-data.json"),
  ...[2, 3, 4, 5].map((day) =>
    cp(`../output/course-demos/day${day}/demo_result.json`, `dist/public/course-demos/day${day}.json`),
  ),
]);

console.log("Built dist/ with Day 1 review UI and Day 2-5 course result demos.");
