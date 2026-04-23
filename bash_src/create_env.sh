uv pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install torch_geometric==2.6.1
uv pip install pyg_lib torch_scatter torch_sparse --find-links https://data.pyg.org/whl/torch-2.6.0+cpu.html
uv pip install -r ../requirements.txt
