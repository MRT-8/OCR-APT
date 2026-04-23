# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OCR-APT is an APT (Advanced Persistent Threat) detection system published at ACM CCS 2025. It combines GNN-based subgraph anomaly detection on provenance graphs with LLM-based attack report generation. The pipeline: audit logs → RDF → GraphDB → PyG graphs → OCRGCN anomaly detection → subgraph extraction → LLM investigation reports.

## Environment Setup

```bash
uv venv --python 3.9
source .venv/bin/activate
cd bash_src/ && bash create_env.sh
```

This uses uv to create a Python 3.9 virtual environment, then installs PyTorch 2.6.0 (CPU), PyG 2.6.1, and all pip dependencies from `requirements.txt`.

## Configuration

Copy `config_sample.json` to `config.json` and fill in:
- GraphDB repository URLs (default: `http://localhost:7200/repositories/...`)
- OpenAI API key (if using GPT for report generation)

GraphDB must be running with repositories: `darpa-tc3`, `darpa-optc-1day`, `simulated-nodlink`. See `Configure_GraphDB.md` for setup.

## Running the Pipeline

### Detection with pre-trained models (recommended for evaluation):
```bash
cd bash_src/ && bash ocrapt-detection.sh
```

### Full pipeline (preprocessing + training + detection):
```bash
cd bash_src/ && bash ocrapt-full-system-pipeline.sh
```

Both scripts are interactive and prompt for dataset, host, experiment name, etc.

### Running individual stages from `src/`:
```bash
python transform_to_RDF.py --dataset tc3 --host cadets --source-graph cadets --root-path ../dataset/darpa_tc3/cadets/experiments/
python encode_to_PyG.py --dataset tc3 --host cadets --root-path ../dataset/darpa_tc3/cadets/experiments/ --source-graph cadets
python train_gnn_models.py --dataset tc3 --host cadets --exp-name MyExp --root-path ../dataset/darpa_tc3/cadets/experiments/ --detector OCRGCN
python detect_anomalous_subgraphs.py --dataset tc3 --host cadets --exp-name MyExp --root-path ../dataset/darpa_tc3/cadets/experiments/ --model <model_file>.model
python ocrapt_llm_investigator.py --dataset tc3 --host cadets --exp-name MyExp --root-path ../dataset/darpa_tc3/cadets/experiments/ --GNN-model-name <model_file>.model
```

## Architecture

### Pipeline stages (all in `src/`):

1. **transform_to_RDF.py** - Converts raw audit log CSVs (edges + node attributes) into RDF Turtle format for GraphDB ingestion.

2. **encode_to_PyG.py** - Queries GraphDB via SPARQL to build heterogeneous PyTorch Geometric graphs with temporal/structural features. Outputs PyG data zips and feature CSVs.

3. **train_gnn_models.py** - Trains the OCRGCN one-class detector on benign-only data. Supports multiple detectors (OCRGCN is primary), multi-run experiments, checkpoint save/load, and batch/full-batch learning.

4. **detect_anomalous_subgraphs.py** - Takes anomaly scores from trained models, identifies anomalous nodes, expands them into subgraphs via 1-hop/2-hop neighborhood queries to GraphDB, filters and deduplicates subgraphs.

5. **ocrapt_llm_investigator.py** - Feeds anomalous subgraphs to LLMs (OpenAI GPT, Ollama, or DeepSeek) to generate human-readable attack investigation reports with IoC extraction.

### Key supporting modules:

- **`pygod/`** - Forked/customized anomaly detection library. The main model is `pygod/detector/ocrgcn.py` (detector wrapper) + `pygod/nn/ocrgcn.py` (neural network using RGCN layers). Base classes in `ocrapt_base.py`.
- **sparql_queries.py** - All SPARQL queries for GraphDB (node/edge retrieval, anomaly expansion, correlation). Uses RDF-Star syntax.
- **database_config.py** - Dataset-specific constants: attack time ranges, node/edge type mappings, subgraph attribute schemas.
- **llm_prompt.py** - LLM prompt templates with `{DOC_ID}`, `{IOC_LIST}`, `{STAGE}` placeholders.

### Datasets supported:

| Dataset | Hosts | ID in CLI |
|---------|-------|-----------|
| DARPA TC3 | cadets, theia, trace | `tc3` |
| DARPA OpTC | SysClient0051, SysClient0501, SysClient0201 | `optc` |
| NODLINK | SimulatedUbuntu, SimulatedWS12, SimulatedW10 | `nodlink` |

### Data paths (under `dataset/`, gitignored):
- Input CSVs: `dataset/{dataset}/{host}/experiments/`
- Models: `dataset/{dataset}/{host}/experiments/models/{exp_name}/`
- Results: `dataset/{dataset}/{host}/experiments/results/{exp_name}/`
- LLM reports: `dataset/{dataset}/{host}/experiments/LLM_investigator_reports/`

### Output paths (tracked):
- Logs: `logs/{host}/{exp_name}/`
- Recovered reports: `recovered_reports/`
- Ground truth: `groundtruth/`
