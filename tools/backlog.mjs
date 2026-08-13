#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const BACKLOG_PATH = join(ROOT, "backlog.json");

const REQUIRED_FIELDS = [
  "id",
  "status",
  "priority",
  "category",
  "title",
  "summary",
  "where",
  "deps",
  "doc",
];
const ID_PATTERN = /^LB-\d{3}$/;

function load() {
  return JSON.parse(readFileSync(BACKLOG_PATH, "utf-8"));
}

function save(data) {
  writeFileSync(BACKLOG_PATH, JSON.stringify(data, null, 2) + "\n", "utf-8");
}

function findTask(data, id) {
  const task = data.tasks.find((t) => t.id === id);
  if (!task) throw new Error(`task not found: ${id}`);
  return task;
}

function cmdList() {
  const data = load();
  for (const t of data.tasks) {
    console.log(`${t.id}\t${t.status}\t${t.title}`);
  }
}

function cmdSet(args) {
  const [id, status] = args;
  if (!id || !status) {
    throw new Error("usage: backlog.mjs set <id> <status>");
  }
  const data = load();
  const task = findTask(data, id);
  if (!data.enums.status.includes(status)) {
    throw new Error(`invalid status: "${status}" (allowed: ${data.enums.status.join(", ")})`);
  }
  task.status = status;
  if (status === "done" && !task.done_at) {
    task.done_at = new Date().toISOString().slice(0, 19);
  }
  save(data);
  console.log(`${id}.status = ${status}`);
}

function validateTask(data, task, index) {
  const problems = [];
  const label = task.id ?? `tasks[${index}]`;

  for (const field of REQUIRED_FIELDS) {
    if (task[field] === undefined || task[field] === null || task[field] === "") {
      problems.push(`${label}: 필수 필드 누락 (${field})`);
    }
  }
  if (typeof task.id === "string" && !ID_PATTERN.test(task.id)) {
    problems.push(`${label}: id 형식이 LB-숫자3자리가 아님 ("${task.id}")`);
  }
  if (task.status !== undefined && !data.enums.status.includes(task.status)) {
    problems.push(`${label}: enums에 없는 status ("${task.status}")`);
  }
  if (task.priority !== undefined && !data.enums.priority.includes(task.priority)) {
    problems.push(`${label}: enums에 없는 priority ("${task.priority}")`);
  }
  if (task.category !== undefined && !data.enums.category.includes(task.category)) {
    problems.push(`${label}: enums에 없는 category ("${task.category}")`);
  }
  return problems;
}

function cmdValidate() {
  const data = load();
  const problems = data.tasks.flatMap((task, index) => validateTask(data, task, index));
  if (problems.length === 0) {
    console.log("VALID");
    return;
  }
  for (const p of problems) console.log(p);
  process.exitCode = 1;
}

const [, , cmd, ...args] = process.argv;

try {
  if (cmd === "list") cmdList();
  else if (cmd === "set") cmdSet(args);
  else if (cmd === "validate") cmdValidate();
  else {
    console.error("usage: backlog.mjs <list | set <id> <status> | validate>");
    process.exit(1);
  }
} catch (err) {
  console.error(err.message);
  process.exit(1);
}
