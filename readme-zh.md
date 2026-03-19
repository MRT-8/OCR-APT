# OCR-APT（中文翻译）

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17254415.svg)](https://doi.org/10.5281/zenodo.17254415)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17254415.svg)](https://doi.org/10.5281/zenodo.17254415)

**OCR-APT** 是一款APT（高级持续性威胁）检测系统，旨在识别异常节点和子图，按异常程度对告警进行优先排序，并重构攻击过程故事，以支持全面溯源调查。

本系统利用 **基于图神经网络（GNN）的子图异常检测** 揭示可疑活动，并借助 **LLM（大语言模型）驱动报告模块** 自动生成类人的攻击叙述。

此代码库对应论文 **OCR-APT: Reconstructing APT Stories through Subgraph Anomaly Detection and LLMs**（收录于ACM CCS 2025）。

---
## 仓库导览

OCR-APT 的输入为CSV格式的审计日志。
系统由多个 Python 和 Bash 脚本协同工作：

- **`/src`** – 主要 Python 脚本：
  - **`sparql_queries.py`** – 定义用于从 GraphDB 构建子图的 SPARQL 查询。
  - **`llm_prompt.py`** – 包含供LLM攻击调查模块使用的提示词。
  - **`transform_to_RDF.py`** – 将原始审计日志转换为RDF格式，以便导入 GraphDB。
  - **`encode_to_PyG.py`** – 将溯源图编码为PyTorch Geometric（PyG）数据结构，用于模型训练与推理。
  - **`train_gnn_models.py`** – 在良性数据上训练一类GNN模型（见 `ocrgcn.py`），并应用于节点异常检测。
  - **`detect_anomalous_subgraphs.py`** – 利用训练好的模型，构建子图并检测异常子图。
  - **`ocrapt_llm_investigator.py`** – 利用大语言模型，对检测出的异常子图生成简明、人类可读的攻击调查报告。
- **`/bash_src`** – 管理整条管道的 Bash 脚本：
  - **`ocrapt-full-system-pipeline.sh`** – 运行OCR-APT所有流程，从数据预处理到报告生成。
  - **`ocrapt-detection.sh`** – 仅运行检测阶段（基于GNN的异常检测与报告生成）。
- **`/recovered_reports`** – 存放实验过程中生成的报告。
- **`/logs`** – 默认系统日志存放目录。
- **`/dataset`** – 包含用于训练/测试的审计日志、真实标签、实验检查点、已训练GNN模型及检测结果（如异常节点、子图和生成报告）。数据集已在 [此链接](https://doi.org/10.5281/zenodo.17254415) 发布。

---
## 系统架构

![系统架构](OCR-APT-system.png)

---

## OCR-APT 安装与配置

1. **创建 Conda 环境**  
   安装 Conda 后，在 `bash_src` 目录下运行如下命令，根据 `requirements.txt` 创建并激活环境：
   ```bash
   conda create -n env-ocrapt python=3.9
   conda activate env-ocrapt
   bash create_env.sh
   ```

2. **设置 GraphDB 及 RDF-Star 支持**  
   - 按[此链接](https://graphdb.ontotext.com/documentation/11.0/graphdb-desktop-installation.html)下载并安装 GraphDB Desktop。
   - 从我们的数据集[页面](https://doi.org/10.5281/zenodo.17254415)下载 `GraphDB_repositories.tar.xz`。该压缩包包含GraphDB的repositories文件夹备份。
     - 快速配置方式：解压后，将其中 `GraphDB_repositories/repositories/` 下的整个 `repositories` 目录替换至 `<PATH_TO_GraphDB_INSTANCE>/.graphdb/data/`。
     - 若想保留现有仓库，可仅拷贝其中三个提供的库到相同位置。
     - 此操作即可运行我们的评测数据集。若需新增库，请参考 `Configure_GraphDB.md`。
   - 启动 GraphDB Desktop，并访问 Workbench（默认端口为 7200，地址为 `http://localhost:7200/`）。
     - 预期在 **Setup → Repositories** 下能看到如下三个仓库：
       - `darpa-tc3`
       - `darpa-optc-1day`
       - `simulated-nodlink`

3. **配置系统参数**  
   在 OCR-APT 根目录下新建 `config.json` 文件，内容如下（请用你的OpenAI密钥替换占位符）：
   ```json
   {
     "repository_url_tc3": "http://localhost:7200//repositories/darpa-tc3",
     "repository_url_optc": "http://localhost:7200/repositories/darpa-optc-1day",
     "repository_url_nodlink": "http://localhost:7200/repositories/simulated-nodlink",
     "openai_api_key": "<API_KEY>"
   }
   ```

4. **准备数据集和模型**  
   从数据集[页面](https://doi.org/10.5281/zenodo.17254415)下载 `dataset.tar.xz`，其中包含数据快照、真实标签和已训练模型。解压后将 `dataset` 文件夹移动至项目根目录。


5. **运行检测管道**  
   - 在 `bash_src` 目录下，使用已训练模型运行检测：
     ```bash
     bash ocrapt-detection.sh
     ```
   - 正常运行后，会在 `/logs/<HOST>/Full_Script_Test` 下生成3个日志文件：
     - `DetectAnomalousNodes_*.txt`：利用 OCRGCN 已训练模型得到的节点异常检测结果。
     - `DetectAnomalousSubgraphs_*.txt`：异常子图检测结果，以及OCR-APT的检测性能指标。
     - `llm_investigator_output_*.txt`：LLM模块自动生成的人类可读攻击调查报告。
   - 示例运行日志（以**cadets**主机为例）见 `/logs/cadets/Full_Script_Test`，可用于运行验证。
   - 如需运行全流程（含预处理、再训练、检测）：
     ```bash
     bash ocrapt-full-system-pipeline.sh
     ```
   > **注意：** 各种预处理文件已在[此处](https://doi.org/10.5281/zenodo.17254415)单独提供，如只做检测可跳过预处理。

---

## 本地部署大语言模型的实验结果

### 实验摘要
我们评估了 OCR-APT 在**本地部署大模型**下的表现，并将生成报告与 ChatGPT 作对比：

- 部署环境：4核CPU、8GB显存GPU、22GB内存，运行 **LLAMA3（8B参数）**  
- 优化方式：测试多种本地嵌入模型，并分析其效果。

**主要发现：** LLAMA3 结合最优嵌入模型后生成的报告，与 ChatGPT 质量相当。

详细实验结果请见 [实验表格](Experiments_with_locally_deployed_LLMs.xlsx)。

---

## 引用
### Bibtex
```
@inproceedings{10.1145/3719027.3765219,
  author = {Aly, Ahmed and Mansour, Essam and Youssef, Amr},
  title = {{OCR-APT}: Reconstructing {APT} Stories from Audit Logs using Subgraph Anomaly Detection and {LLMs}},
  year = {2025},
  isbn = {9798400715259},
  publisher = {Association for Computing Machinery},
  address = {New York, NY, USA},
  url = {https://doi.org/10.1145/3719027.3765219},
  doi = {10.1145/3719027.3765219},
  booktitle = {Proceedings of the 2025 ACM SIGSAC Conference on Computer and Communications Security},
  pages = {261–275},
  series = {CCS '25}
}
```

---

*（本文件为 OCR-APT 官方 README.md 中文翻译，仅供参考，具体技术细节请以英文原版为准）*
