import sharp from "sharp";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");
const input = path.join(root, "public/brand/logo-aia-legnano.png");
const brandDir = path.join(root, "public/brand");
const publicDir = path.join(root, "public");

const NAVY = { r: 0, g: 69, b: 135, alpha: 1 };

/** Cerchio navy + logo, angoli trasparenti. */
async function circularPng(size) {
  const roundMask = Buffer.from(
    `<svg><rect x="0" y="0" width="${size}" height="${size}" rx="${size / 2}" ry="${size / 2}" fill="#fff"/></svg>`
  );

  return sharp(input)
    .resize(size, size, { fit: "contain", background: NAVY })
    .ensureAlpha()
    .composite([{ input: roundMask, blend: "dest-in" }])
    .png()
    .toBuffer();
}

async function writeCircular(name, size) {
  const buf = await circularPng(size);
  await sharp(buf).toFile(path.join(brandDir, name));
  console.log(`Wrote ${name} (${size}px)`);
  return buf;
}

await mkdir(brandDir, { recursive: true });

const buf16 = await writeCircular("favicon-16.png", 16);
const buf32 = await writeCircular("favicon-32.png", 32);
await writeCircular("favicon-48.png", 48);
await writeCircular("apple-touch-icon.png", 180);
await writeCircular("icon-192.png", 192);
await writeCircular("icon-512.png", 512);

try {
  const toIco = (await import("to-ico")).default;
  await writeFile(path.join(publicDir, "favicon.ico"), await toIco([buf16, buf32]));
  console.log("Wrote favicon.ico");
} catch (err) {
  console.warn("favicon.ico skipped:", err.message);
  await writeFile(path.join(publicDir, "favicon.ico"), buf32);
  console.log("Wrote favicon.ico (32px PNG fallback)");
}

const b64 = buf32.toString("base64");
await writeFile(
  path.join(brandDir, "favicon.svg"),
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><image href="data:image/png;base64,${b64}" width="32" height="32"/></svg>`
);
console.log("Wrote favicon.svg");
