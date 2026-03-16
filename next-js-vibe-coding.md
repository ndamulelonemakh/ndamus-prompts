# Promts for Vibe coding with NextJS

## Draft Architecture

```markdown
# Role
You are the Lead System Architect and Senior Engineer for this project. Your goal is to produce formal system architecture documentation and implementation guidelines based on the provided context.

# Context & Inputs
Please analyze the following three information sources to derive the architecture:
1. **Reference UI:** {{REFERENCE_UI_DESCRIPTION_OR_ATTACHMENT}}
2. **Project Brief:** {{PROJECT_BRIEF_CONTENT}}
3. **UI Design Project:** {{DESIGN_PROJECT_CONTEXT_OR_ATTACHMENT}} 
   *(Note: Do not rely on local file paths. Ensure content is pasted or uploaded directly.)*

# Architecture Requirements
Structure the documentation and implementation plan around these core pillars:

1. **Security & IAM**
   - Utilize the official "Better Auth" template patterns.
   - Security is non-negotiable. Implement strict authentication and authorization flows.
   
2. **Backend Strategy**
   - Primary: Next.js API Layer (Serverless/Edge compatible).
   - Constraint: Architecture must remain modular to allow future migration to a dedicated backend service without refactoring the core logic.

3. **Data Integration & State Management**
   - Framework: Next.js (Latest Stable Version).
   - Practices: Prioritize React Server Components (RSC).
   - State: Use TanStack Query for server state and Zustand for client global state only if strictly necessary.
   - Localization: Feature localization (i18n) is a key requirement.

# Coding & Documentation Standards
- **Documentation:** Formal architecture documentation required. 
- **Code Comments:** No unnecessary docstrings or inline comments. Code must be self-explanatory.
- **Engineering:** Sound engineering decisions only. Prioritize maintainability and scalability.
- **Security:** Zero-trust principles where applicable.

# Output Format
1. **Architecture Overview:** High-level diagram description.
2. **Security Model:** IAM flows and protection measures.
3. **Data Flow:** State management and API integration strategy.
4. **Implementation Plan:** Step-by-step breakdown.

# Critical Instruction
If any of the three input sources are missing, ambiguous, or if security requirements conflict with the brief, **STOP and ask clarifying questions** before generating the architecture.
```

## Version upgrades

```markdown
As the lead nextjs engineer at vercel you are required to upgrade this project from next version 14 to 15, making sure that evrything works as expected after the upgrade. Here is the offfical guide: https://nextjs.org/docs/app/guides/upgrading/version-15 . Use this and any other relevant information from the web you need to handle breaking changes. begin your analysis now
```

## Fix build

```markdown
Please help iteratively fix my build using bun run build and type-check
```


## Use [Vercel AI SDK](https://ai-sdk.dev/)

```markdown
Please upgrade this route to use vercel built-in ai sdk which already has built in retry, timeout settings and structured outputs support i.e. we can pass in the zod schema we want from llm directly. See this guides: https://ai-sdk.dev/docs/introduction and https://ai-sdk.dev/docs/ai-sdk-core/generating-structured-data
```

## Documentation

```markdown
Please carefully understand the project on a high and technical level, and use the gained knowldege to update the README accordingly
```
