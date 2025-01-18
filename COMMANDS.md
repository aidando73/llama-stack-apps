
```bash
export LLAMA_STACK_PORT=5000
export FIREWORKS_API_KEY=your_key_here
docker run -it \
  -p $LLAMA_STACK_PORT:$LLAMA_STACK_PORT \
  -v ~/.llama:/root/.llama \
  llamastack/distribution-fireworks \
  --port $LLAMA_STACK_PORT \
  --env FIREWORKS_API_KEY=$FIREWORKS_API_KEY

version=v40.6-confirm && \
eval_dir=$(realpath evals/$version) && \
mkdir -p $eval_dir && \
python eval10.py --eval_dir $eval_dir --num_workers 8
```