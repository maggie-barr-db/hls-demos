## HLS Demos

A collection of healthcare and life sciences (HLS) demos. Each demo lives in its own folder under `demos/` with its own README and installation steps.

### Pre-requisites

- **Databricks workspace**: You have access to a Databricks workspace (URL) with permissions to create clusters/jobs and manage resources required by the demos.
- **Databricks CLI**: Installed and authenticated against your workspace.
  - Install (macOS):
    ```bash
    brew install databricks/tap/databricks
    ```
  - Verify:
    ```bash
    databricks --version
    ```
  - Authenticate (recommended):
    ```bash
    databricks auth login --host https://<your-workspace-url>
    ```
  - Alternatively (classic CLI auth):
    ```bash
    databricks configure --token
    ```

### Repository structure

```
.
├── README.md          # This file
└── demos/             # Each demo in its own folder (see below)
    └── <demo-name>/
        ├── README.md  # Demo-specific overview & install steps
        └── ...        # Notebooks, scripts, configs, etc.
```

### Available demos

| Demo | Description | Install / Docs |
|------|-------------|----------------|
| serverless-jobs-demo | Bronze and silver data pipeline jobs using classic and serverless compute with UC volumes | demos/serverless-jobs-demo/README.md |

As new demos are added under `demos/<demo-name>`, they should include a `README.md` with environment setup, deployment, and teardown instructions. This top-level list will link to them.

### Synthetic data generation

These demos may rely on synthetic healthcare datasets generated directly on Databricks using the Synthea-based workflow in `synthea-on-dbx`.

- Repository: [matthew-gigl-db/synthea-on-dbx](https://github.com/matthew-gigl-db/synthea-on-dbx)
- Use it to generate realistic synthetic HLS data into a Unity Catalog catalog/schema of your choice (written to UC volumes). At a high level:
  1. Clone that repo into a Git-enabled, UC workspace.
  2. Open the `synthea-on-databricks` notebook and attach to a cluster (e.g., DBR 14.3 LTS or Serverless).
  3. Set widgets such as `catalog_name` (your chosen UC catalog) and `schema_name` (default `synthea`), plus optional `create_landing_zone` and `inject_bad_data`.
  4. Run the notebook to post and execute the workflow; CSV outputs are written to UC volumes and can be consumed by the demos here.

### Quick start

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-org>/hls-demos.git
   cd hls-demos
   ```
2. Ensure pre-requisites are met (Databricks workspace access and CLI configured).
3. Explore available demos:
   ```bash
   ls demos
   ```
4. Pick a demo and follow its `README.md` for installation:
   ```bash
   cd demos/<demo-name>
   # follow the demo's README.md
   ```

### Adding a new demo

When contributing a demo under `demos/<demo-name>`:

- Include a `README.md` that covers:
  - Overview and architecture (what the demo shows)
  - Pre-requisites (workspace requirements, required permissions, runtime version)
  - Installation steps (commands/notebooks to run, expected runtime, configs)
  - How to validate the deployment worked
  - Teardown/cleanup instructions
- Keep any scripts idempotent where possible and prefer non-interactive flags for automation.

### Troubleshooting

- Verify your CLI is authenticated to the correct workspace/profile:
  ```bash
  databricks auth profiles
  databricks auth whoami
  ```
- If cluster/job creation fails, confirm your workspace permissions and that your account/UC settings allow the required resources.

### Useful links

- Databricks CLI docs: [Install and use the Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html)
- Databricks authentication: [CLI authentication](https://docs.databricks.com/en/dev-tools/cli/authentication.html)


