import Fastify from "fastify";
import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import crypto from "crypto";
import fs from "fs";
import path from "path";
import { pipeline } from "stream/promises";
import "dotenv/config";

import { db } from "./db/client.js";
import { projects, files } from "./db/schema.js";

const server = Fastify({ logger: true });

/**
 * Enable CORS for frontend
 */
await server.register(cors, {
  origin: "http://localhost:3000",
});

/**
 * Enable multipart uploads
 */
await server.register(multipart, {
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB
  },
});

/**
 * Health check
 */
server.get("/health", async () => {
  return { status: "ok" };
});

/**
 * Get all projects
 */
server.get("/api/projects", async () => {
  const result = await db.select().from(projects);
  return { projects: result };
});

/**
 * Create a new project
 */
server.post("/api/projects", async (request, reply) => {
  const body = request.body as { name?: string };

  if (!body.name) {
    return reply.status(400).send({ error: "Project name is required" });
  }

  const [project] = await db
    .insert(projects)
    .values({
      id: crypto.randomUUID(), // UUID generated here
      name: body.name,
    })
    .returning();

  return project;
});

/**
 * Upload and extract ZIP for a project
 */
server.post("/api/projects/:projectId/upload", async (request, reply) => {
  const { projectId } = request.params as { projectId: string };
  const data = await request.file();

  if (!data) {
    return reply.status(400).send({ error: "No file uploaded" });
  }

  if (!data.filename.endsWith(".zip")) {
    return reply.status(400).send({ error: "Only ZIP files are allowed" });
  }

  const baseDir = path.join(process.cwd(), "uploads", projectId);
  await fs.promises.mkdir(baseDir, { recursive: true });

  const zipPath = path.join(baseDir, "source.zip");
  await pipeline(data.file, fs.createWriteStream(zipPath));

  // Extract ZIP
  const AdmZip = (await import("adm-zip")).default;
  const zip = new AdmZip(zipPath);
  const extractPath = path.join(baseDir, "extracted");
  zip.extractAllTo(extractPath, true);

  // Walk extracted files
  const filePaths: string[] = [];

  function walk(dir: string) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        walk(fullPath);
      } else {
        filePaths.push(
          fullPath.replace(extractPath, "").replace(/\\/g, "/")
        );
      }
    }
  }

  walk(extractPath);

  // Persist files in DB
  await db.insert(files).values(
    filePaths.map((filePath) => ({
      id: crypto.randomUUID(),
      projectId,
      path: filePath,
      extension: filePath.split(".").pop() || "",
    }))
  );

  return {
    message: "Codebase uploaded, extracted, and indexed",
    totalFiles: filePaths.length,
  };
});

/**
 * Start server
 */
const start = async () => {
  try {
    await server.listen({ port: 4000 });
    console.log("Backend running on http://localhost:4000");
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();
