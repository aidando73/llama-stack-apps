```bash
source ~/miniconda3/bin/activate
conda create --prefix ./env python=3.10

source ~/miniconda3/bin/activate
conda activate ./env

python -m examples.agents.hello localhost 5000
```