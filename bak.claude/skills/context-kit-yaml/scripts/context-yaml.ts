#!/usr/bin/env bun
/**
 * CLI entry point for context-kit YAML generation.
 *
 * Usage:
 *   bun run .claude/skills/context-kit-yaml/scripts/context-yaml.ts [options]
 *
 * Options:
 *   --dir <path>        Target directory (default: cwd)
 *   --output <path>     Output file (default: _context-kit.yml in target dir)
 *   --json              Output JSON to stdout instead of YAML file
 *   --tools <list>      Comma-separated tool subset: structure,dependencies,...
 *   --koji              Also ingest results into Koji (requires running service)
 *   --verbose           Show progress for each tool
 *   --help              Show this help message
 *
 * Exit codes:
 *   0 = success
 *   1 = runtime error
 *   2 = bad arguments
 *   3 = all tools failed
 */

import { resolve, join } from "node:path";
import { writeFile } from "node:fs/promises";
import { orchestrate } from "../../../../tkr-kit/core/context/orchestrator.js";
import { synthesize } from "../../../../tkr-kit/core/context/synthesizer.js";
import { ALL_TOOLS, type ContextToolName } from "../../../../tkr-kit/core/context/types.js";

interface CliOptions {
  dir: string;
  output: string | null;
  json: boolean;
  tools: ContextToolName[];
  koji: boolean;
  verbose: boolean;
}

function printHelp(): void {
  const lines = [
    "Usage: bun run .claude/skills/context-kit-yaml/scripts/context-yaml.ts [options]",
    "",
    "Options:",
    "  --dir <path>     Target directory (default: cwd)",
    "  --output <path>  Output file (default: _context-kit.yml in target dir)",
    "  --json           Output JSON to stdout instead of YAML file",
    "  --tools <list>   Comma-separated subset: structure,dependencies,testing,...",
    "  --koji           Also ingest results into Koji",
    "  --verbose        Show progress for each tool",
    "  --help           Show this help message",
    "",
    `Available tools: ${ALL_TOOLS.join(", ")}`,
  ];
  console.log(lines.join("\n"));
}

function parseArgs(argv: string[]): CliOptions | null {
  const opts: CliOptions = {
    dir: process.cwd(),
    output: null,
    json: false,
    tools: [...ALL_TOOLS],
    koji: false,
    verbose: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];

    switch (arg) {
      case "--help":
      case "-h":
        printHelp();
        process.exit(0);
        break;

      case "--dir": {
        i++;
        const dirArg = argv[i];
        if (!dirArg) {
          console.error("Error: --dir requires a path argument");
          return null;
        }
        opts.dir = resolve(dirArg);
        break;
      }

      case "--output": {
        i++;
        const outArg = argv[i];
        if (!outArg) {
          console.error("Error: --output requires a path argument");
          return null;
        }
        opts.output = resolve(outArg);
        break;
      }

      case "--json":
        opts.json = true;
        break;

      case "--tools": {
        i++;
        const toolsArg = argv[i];
        if (!toolsArg) {
          console.error("Error: --tools requires a comma-separated list");
          return null;
        }
        const names = toolsArg.split(",").map((s) => s.trim());
        const invalid = names.filter(
          (n) => !ALL_TOOLS.includes(n as ContextToolName),
        );
        if (invalid.length > 0) {
          console.error(
            `Error: unknown tools: ${invalid.join(", ")}\nAvailable: ${ALL_TOOLS.join(", ")}`,
          );
          return null;
        }
        opts.tools = names as ContextToolName[];
        break;
      }

      case "--koji":
        opts.koji = true;
        break;

      case "--verbose":
        opts.verbose = true;
        break;

      default:
        console.error(`Error: unknown option: ${arg}`);
        return null;
    }
  }

  return opts;
}

async function main(): Promise<void> {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts) {
    process.exit(2);
  }

  if (opts.verbose) {
    console.error(`Analyzing ${opts.dir} with tools: ${opts.tools.join(", ")}`);
  }

  // Run orchestrator
  const orchResult = await orchestrate({
    cwd: opts.dir,
    tools: opts.tools,
    includeTree: true,
    treeDepth: 4,
  });

  if (!orchResult.success) {
    console.error("Error: all tools failed");
    for (const err of orchResult.errors) {
      console.error(`  ${err.tool}: ${err.error}`);
    }
    process.exit(3);
  }

  if (opts.verbose && orchResult.errors.length > 0) {
    console.error(`Warnings (${orchResult.errors.length} tools failed):`);
    for (const err of orchResult.errors) {
      console.error(`  ${err.tool}: ${err.error}`);
    }
  }

  // Synthesize
  const synthResult = await synthesize(orchResult.results, {
    cwd: opts.dir,
  });

  if (opts.verbose) {
    console.error(
      `Generated ${synthResult.sectionsIncluded.length} sections in ${orchResult.duration}ms`,
    );
  }

  // Output
  if (opts.json) {
    console.log(JSON.stringify(synthResult.json, null, 2));
  } else {
    const outputPath =
      opts.output ?? join(opts.dir, "_context-kit.yml");
    await writeFile(outputPath, synthResult.yaml, "utf-8");
    console.error(`Wrote ${outputPath}`);
  }

  // Optional Koji ingestion
  if (opts.koji) {
    if (opts.verbose) {
      console.error("Ingesting into Koji...");
    }
    const { ingestToKoji } = await import("../../../../tkr-kit/core/context/koji-bridge.js");
    const kojiResult = await ingestToKoji(orchResult.results);
    if (opts.verbose) {
      console.error(
        `Koji: ${kojiResult.ingested} ingested, ${kojiResult.errors} errors`,
      );
    }
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
