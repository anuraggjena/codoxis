import Fastify from "fastify";
import cors from "@fastify/cors";

const server = Fastify({
  logger: true,
});

// allow requests from frontend
await server.register(cors, {
  origin: "http://localhost:3000",
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
