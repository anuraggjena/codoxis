import Fastify from "fastify";
import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import { pipeline } from "stream/promises";
import fs from "fs";
import path from "path";
import AdmZip from "adm-zip";

const server = Fastify({
  logger: true,
});

// allow requests from frontend
await server.register(cors, {
  origin: "http://localhost:3000",
});

await server.register(multipart, {
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB
  }
});

server.get("/health", async () => {
  return {
    status: "ok",
    service: "codoxis-backend",
  };
});

type Project = {
  id: string;
  name: string;
  createdAt: string;
};

const projects: Project[] = [];

server.get("/api/projects", async () => {
  return {
    projects,
  };
});

server.post("/api/projects", async (request) => {
  const body = request.body as { name?: string };

  if (!body.name) {
    return {
      error: "Project name is required",
    };
  }

  const project: Project = {
    id: crypto.randomUUID(),
    name: body.name,
    createdAt: new Date().toISOString(),
  };

  projects.push(project);

  return project;
});

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
  const zip = new AdmZip(zipPath);
  const extractPath = path.join(baseDir, "extracted");
  zip.extractAllTo(extractPath, true);

  // Walk file structure
  const files: string[] = [];

  function walk(dir: string) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        walk(fullPath);
      } else {
        files.push(
          fullPath.replace(extractPath, "").replace(/\\/g, "/")
        );
      }
    }
  }

  walk(extractPath);

  return {
    message: "Codebase uploaded and extracted",
    totalFiles: files.length,
    sampleFiles: files.slice(0, 10)
  };
});

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
