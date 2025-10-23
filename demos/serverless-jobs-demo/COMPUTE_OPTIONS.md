# Classic vs Serverless Compute Options

This demo now provides both **classic compute** and **serverless compute** options for all pipelines.

## Directory Structure

```
demos/serverless-jobs-demo/
└── scripts/                    # Python scripts (shared by both compute types)
    ├── bronze/
    │   ├── bronze_ingest.py
    │   └── bronze_archive.py
    ├── silver/                 # 4 silver fact table loaders + control
    │   ├── silver_control.py
    │   ├── load_fact_claims.py
    │   ├── load_fact_patient_encounters.py
    │   ├── load_fact_medications.py
    │   └── load_fact_procedures.py
    └── gold/                   # 1 gold aggregation table
        └── load_fact_member_monthly_snapshot.py
```

## What's Different?

**Code**: All Python scripts are in the `scripts/` directory - **shared by both compute types**.

**Execution**: 
- **Classic jobs** run on traditional Databricks clusters you configure
- **Serverless jobs** run on serverless compute with automatic scaling

**Configuration**: Only the job definitions in `databricks.yml` differ:
- Classic jobs use `job_clusters` with explicit cluster specifications
- Serverless jobs use `environment_key` with environment definitions (no cluster config needed)

**Key Point**: The Python code is identical - only the compute configuration changes!

## Jobs Created (Batch)

| Job Name | Compute | Description |
|----------|---------|-------------|
| `daily_bronze_ingestion_incr_classic` | Classic | Bronze ingest + archive (2 tasks) |
| `daily_bronze_ingestion_incr_serverless` | Serverless | Bronze ingest + archive (2 tasks) |
| `daily_silver_load_incr_classic` | Classic | Silver/gold loads (5 tasks) |
| `daily_silver_load_incr_serverless` | Serverless | Silver/gold loads (5 tasks) |

## Classic Compute

**Advantages:**
- Full control over cluster configuration
- Can use spot instances for cost savings
- Specific Spark configurations available
- Familiar cluster management
- Predictable resource allocation
- Better for long-running jobs

**Use When:**
- You need specific driver/worker configurations
- Cost optimization via spot instances is important
- You require custom Spark settings
- Debugging requires cluster-level access
- Jobs run continuously for long periods

**Configuration Example (databricks.yml):**
```yaml
job_clusters:
  - job_cluster_key: classic_single_node
    new_cluster:
      spark_version: "14.3.x-scala2.12"
      node_type_id: "Standard_DS3_v2"
      spark_conf:
        spark.databricks.cluster.profile: "singleNode"
      num_workers: 0
```

## Serverless Compute

**Advantages:**
- Instant startup (no cluster provisioning)
- Automatic scaling based on workload
- Simplified configuration (no sizing needed)
- Pay only for actual compute used
- Faster development iteration
- Managed by Databricks platform

**Use When:**
- Fast startup is important
- Workload varies significantly
- You want simplified operations
- Development speed is priority
- Ad-hoc or scheduled batch jobs
- You prefer hands-off infrastructure

**Configuration Example (databricks.yml):**
```yaml
jobs:
  my_serverless_job:
    name: my_serverless_job
    tasks:
      - task_key: my_task
        spark_python_task:
          python_file: scripts/my_script.py
        environment_key: Serverless
    queue:
      enabled: true
    environments:
      - environment_key: Serverless
        spec:
          client: "1"
          dependencies: []
    performance_target: PERFORMANCE_OPTIMIZED
```

## Cost Comparison

| Aspect | Classic Compute | Serverless Compute |
|--------|----------------|-------------------|
| **Startup** | 5-10 minutes | Instant (seconds) |
| **Idle Time** | Charged if running | No idle charges |
| **Scaling** | Manual configuration | Automatic |
| **DBU Rate** | Standard | Slightly higher |
| **Best For** | Long-running | Short/variable jobs |
| **Spot Instances** | Supported | Not available |

**General Rule:**
- Serverless is cheaper for short, infrequent jobs
- Classic can be cheaper for long-running, continuous jobs (especially with spot instances)

## Performance Comparison

| Metric | Classic Compute | Serverless Compute |
|--------|----------------|-------------------|
| **Cold Start** | 5-10 minutes | <30 seconds |
| **Warm Start** | 0 seconds (if running) | <30 seconds |
| **Processing Speed** | Configurable | Auto-optimized |
| **Consistency** | High (dedicated) | High (managed) |
| **Monitoring** | Standard | Enhanced lineage |

## Choosing Between Them

### Start with Serverless if:
- ✅ You're new to Databricks
- ✅ You want simplest setup
- ✅ Jobs run on schedule (not continuously)
- ✅ Development/testing phase
- ✅ Uncertain about workload size

### Switch to Classic if:
- ✅ Jobs run 24/7
- ✅ Need specific Spark tuning
- ✅ Cost optimization via spot instances important
- ✅ Existing cluster management patterns
- ✅ Network/security restrictions

### Run Both When:
- ✅ Testing performance differences
- ✅ Migration period
- ✅ Different jobs have different needs

**Important:** Don't run both classic AND serverless versions of the same job simultaneously - they'll create duplicate data!

## Migration Path

### From Classic to Serverless

1. Notebooks are already compatible (no code changes needed!)
2. Deploy serverless jobs: 
   ```bash
   databricks bundle deploy
   ```
3. Test serverless job:
   ```bash
   databricks bundle run daily_bronze_ingestion_incr_serverless
   ```
4. Compare results and performance
5. Pause classic job if satisfied:
   - Update `pause_status: "PAUSED"` for classic jobs

### From Serverless to Classic

1. Notebooks are already compatible (no code changes needed!)
2. Jobs already deployed
3. Test classic job:
   ```bash
   databricks bundle run daily_bronze_ingestion_incr
   ```
4. Compare performance
5. Pause serverless job if satisfied

## Recommendation

**For this healthcare demo:**
- **Start with Serverless** for simplicity and faster iteration
- **Move to Classic** only if you need specific optimizations

**For production:**
- **Serverless** for scheduled ETL jobs
- **Classic** for streaming/continuous jobs or cost-sensitive workloads
- **Mix both** based on job characteristics

## FAQs

**Q: Can I use both simultaneously?**  
A: Technically yes, but **not recommended** as they'll create duplicate tables. Choose one.

**Q: Are the Python scripts different between classic and serverless?**  
A: No! Both use the same scripts from the `scripts/` directory. Only the job configuration differs.

**Q: Can I switch between them easily?**  
A: Yes! Just run the other job. They both use the same Python code.

**Q: Which costs more?**  
A: Depends on job duration. Serverless has higher DBU rate but no idle charges. Classic has lower DBU rate but charges during idle/startup.

**Q: Is serverless as fast?**  
A: Yes, once started. But startup is much faster (instant vs 5-10 min).

---

**Bottom Line:** Try serverless first. It's simpler and usually the right choice for ETL jobs. Switch to classic only if you have specific needs.

