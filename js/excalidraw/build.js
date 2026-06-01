// Build the Excalidraw anywidget bundle.
//
// Usage:
//   node js/excalidraw/build.js <git-url-or-local-path> [branch]
//   node js/excalidraw/build.js https://github.com/rambip/excalidraw fix/shadow-dom-support
//   node js/excalidraw/build.js /local/path/to/excalidraw-fork
//
// The repo is cloned into a temp dir if a URL is given.

const path = require("path");
const fs = require("fs");
const os = require("os");
const { execSync } = require("child_process");
const { pathToFileURL } = require("url");

const arg = process.argv[2];
const branch = process.argv[3];

let FORK;
if (!arg) {
  throw new Error("Usage: node build.js <git-url-or-path> [branch]");
} else if (arg.startsWith("http") || arg.startsWith("git@")) {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "excalidraw-fork-"));
  const branchFlag = branch ? `--branch ${branch} --single-branch` : "";
  console.log(`Cloning ${arg} ${branch ?? ""} into ${tmpDir} ...`);
  execSync(`git clone --depth 1 ${branchFlag} ${arg} ${tmpDir}`, { stdio: "inherit" });
  execSync(`yarn install --no-immutable`, { cwd: tmpDir, stdio: "inherit" });
  FORK = tmpDir;
} else {
  FORK = path.resolve(arg);
}
const NODE_MODULES = path.join(FORK, "node_modules");
const PACKAGES = path.join(FORK, "packages");
const OUT_DIR = path.resolve(__dirname, "../../wigglystuff/static");

console.log(`Using fork: ${FORK}`);

const { build } = require(path.join(NODE_MODULES, "esbuild"));
const { sassPlugin } = require(path.join(NODE_MODULES, "esbuild-sass-plugin"));
const { parseEnvVariables } = require(path.join(FORK, "packages/excalidraw/env.cjs"));

const resolveRelativePath = (importPath, sourceFile) => {
  const sourceDir = path.dirname(sourceFile);
  for (const ext of [".scss", ".css", ""]) {
    const fullPath = path.resolve(sourceDir, importPath + ext);
    if (fs.existsSync(fullPath)) return fullPath;
    const partial = path.join(path.dirname(fullPath), `_${path.basename(fullPath)}`);
    if (fs.existsSync(partial)) return partial;
  }
  return null;
};

const precompile = (source, sourcePath) =>
  source.replace(/(@use|@forward)\s+["'](\.[^"']+)["']/g, (match, directive, importPath) => {
    const resolved = resolveRelativePath(importPath, sourcePath);
    return resolved ? `${directive} "${pathToFileURL(resolved).href}"` : match;
  });

const ENV_VARS = {
  ...parseEnvVariables(path.join(FORK, ".env.production")),
  PROD: true,
};

const fontPlugin = {
  name: "font-loader",
  setup(build) {
    build.onLoad({ filter: /\/Xiaolai\/index\.[jt]sx?$/ }, () => ({
      contents: `
        console.warn("[excalidraw] Chinese (Xiaolai) font not bundled — CJK text will use system fallback.");
        export const XiaolaiFontFaces = [];
      `,
      loader: "js",
    }));
    build.onLoad({ filter: /\.woff2$/ }, (args) => ({
      contents: fs.readFileSync(args.path),
      loader: "dataurl",
    }));
  },
};

(async () => {
  await build({
    entryPoints: [path.join(__dirname, "widget.tsx")],
    outfile: path.join(OUT_DIR, "excalidraw.js"),
    bundle: true,
    splitting: false,
    format: "esm",
    minify: true,
    plugins: [
      sassPlugin({ precompile, loadPaths: [path.join(FORK, "packages/excalidraw")] }),
      fontPlugin,
    ],
    target: "es2020",
    define: {
      "import.meta.env": JSON.stringify(ENV_VARS),
      "process.env.NODE_ENV": '"production"',
    },
    nodePaths: [NODE_MODULES],
    alias: {
      "./excalidraw-fork/packages/excalidraw/index.tsx":  path.join(PACKAGES, "excalidraw/index.tsx"),
      "./excalidraw-fork/packages/excalidraw/types.ts":   path.join(PACKAGES, "excalidraw/types.ts"),
      "./excalidraw-fork/packages/common/src/types.ts":   path.join(PACKAGES, "common/src/types.ts"),
      "@excalidraw/utils":               path.join(PACKAGES, "utils/src"),
      "@excalidraw/common":              path.join(PACKAGES, "common/src"),
      "@excalidraw/element":             path.join(PACKAGES, "element/src"),
      "@excalidraw/math":                path.join(PACKAGES, "math/src"),
      "@excalidraw/fractional-indexing": path.join(PACKAGES, "fractional-indexing/src"),
    },
  });
  console.log("✅ wigglystuff/static/excalidraw.{js,css}");
})();
