
```bash
source ~/miniconda3/bin/activate
conda create --prefix ./env python=3.10

source ~/miniconda3/bin/activate
conda activate ./env

python print.py > error.txt

pip install -r requirements.txt

pip install httpx==0.27.2

# works now
python -m examples.agents.hello localhost 5001

# Runs but doesn't work
PYTHONPATH=. python examples/agent_store/app.py localhost 5001

python -m examples.agents.rag_with_memory_bank localhost 5001

cd examples/E2E-RAG-App/
pip install -r requirements.txt
pip install gradio chromadb

python app.py
```
