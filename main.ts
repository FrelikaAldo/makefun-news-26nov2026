#!/usr/bin/env node
/**
 * Copies entry.png to the output directory after checking it is a PNG that
 * make.fun will accept: at most 1024 px on a side and at most 1 MiB.
 *
 * Node 22, standard library only. No clock, no network.
 *
 *   MAKEFUN_OUTPUT_DIR=out node main.ts
 */

import { copyFileSync, existsSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import process from "node:process";

const MAX_SIDE = 1024;
const MAX_BYTES = 1024 * 1024;
const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const repoRoot: string = import.meta.dirname;
const source: string = join(repoRoot, "entry.png");
const outputDir: string = resolve(process.env.MAKEFUN_OUTPUT_DIR ?? "/output");
const target: string = join(outputDir, "entry.png");

function refuse(reason: string): never {
  console.error(`refusing to copy entry.png: ${reason}`);
  process.exit(1);
}

if (!existsSync(source)) {
  refuse(`${source} does not exist. Run "python3 scripts/make_news.py" first.`);
}

const bytes: number = statSync(source).size;
if (bytes === 0) {
  refuse(`${source} is empty.`);
}
if (bytes > MAX_BYTES) {
  refuse(`${source} is ${bytes} bytes, over the 1048576 byte limit.`);
}

const head = readFileSync(source);
if (head.length < 24 || !head.subarray(0, 8).equals(PNG_SIGNATURE)) {
  refuse(`${source} does not start with the PNG signature.`);
}

const width = head.readUInt32BE(16);
const height = head.readUInt32BE(20);
if (width === 0 || height === 0) {
  refuse(`${source} has a broken IHDR header (${width}x${height}).`);
}
if (width > MAX_SIDE || height > MAX_SIDE) {
  refuse(`${source} is ${width}x${height}, larger than ${MAX_SIDE} px on a side.`);
}

mkdirSync(outputDir, { recursive: true });
copyFileSync(source, target);

const written: number = statSync(target).size;
if (written !== bytes) {
  refuse(`copy at ${target} is ${written} bytes but the source is ${bytes} bytes.`);
}

console.log(`entry.png -> ${target} (${written} bytes, ${width}x${height} px, PNG)`);
