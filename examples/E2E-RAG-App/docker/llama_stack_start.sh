
sleep 45

echo "-----starting to llama-stack docker now---------"

pip install gradio
pip install docling

python /root/E2E-RAG-App/01_ingest_files.py --input_dir /root/rag_data/

echo "starting the llama-stack server"

python -m llama_stack.distribution.server.server --yaml-config /root/my-run.yaml --disable-ipv6&

sleep 30
echo "---------running the RAG app--------------"

python /root/E2E-RAG-App/gradio_interface.py
