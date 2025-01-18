
```bash
export LLAMA_STACK_PORT=5000
export FIREWORKS_API_KEY=your_key_here
docker run -it \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ~/.llama:/root/.llama \
  llamastack/distribution-fireworks \
  --port $LLAMA_STACK_PORT \
  --env FIREWORKS_API_KEY=$FIREWORKS_API_KEY

source ~/miniconda3/bin/activate
conda create --prefix ./env python=3.10 -y
conda activate ./env
pip install -r ./requirements.txt

# Dev dependencies
pip install datasets

version=v1 && \
mkdir -p evals/$version && \
eval_dir=$(realpath evals/$version) && \
python eval10.py --eval_dir $eval_dir

python eval10.py

(rm worker_0.log || true) && python eval10.py
```
