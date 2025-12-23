import { relations } from "drizzle-orm/relations";
import { projects, files } from "./schema";

export const filesRelations = relations(files, ({one}) => ({
	project: one(projects, {
		fields: [files.projectId],
		references: [projects.id]
	}),
}));

export const projectsRelations = relations(projects, ({many}) => ({
	files: many(files),
}));