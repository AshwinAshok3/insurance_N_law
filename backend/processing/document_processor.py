import os
import re
import hashlib
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice

# We'll import the initialized Pinecone index and embedder from pipeline.py
from backend.ai.pipeline import get_pinecone_index, embedder

def process_document(pdf_path: str, category_name: str) -> bool:
    """
    Processes a PDF document:
    1. Extracts text using Docling
    2. Chunks the text
    3. Embeds chunks using SentenceTransformers
    4. Upserts to Pinecone
    """
    print(f"Starting processing for {pdf_path} into namespace {category_name}...")
    
    # 1. Pipeline configuration
    pipeline_opts = PdfPipelineOptions()
    pipeline_opts.do_ocr = True 
    pipeline_opts.do_table_structure = True 
    # Use CPU by default for backend, you can switch AcceleratorDevice to CUDA if running on GPU server
    pipeline_opts.accelerator_options = AcceleratorOptions(num_threads=2, device=AcceleratorDevice.CPU)
    
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)}
    )
    
    try:
        # 1. Rasterize and OCR
        result = converter.convert(pdf_path)
        markdown_text = result.document.export_to_markdown()
    except Exception as e:
        print(f"Error during Docling conversion: {e}")
        return False
        
    # 2. Chunking
    all_chunks = []
    MAX_CHAR_LIMIT = 8000 
    OVERLAP = 400 
    
    semantic_chunks = re.split(r'(?=\n#{2,3}\s)', markdown_text)
    
    for c in semantic_chunks:
        clean_chunk = c.strip()
        if len(clean_chunk) > 50:
            start = 0
            while start < len(clean_chunk):
                end = min(start + MAX_CHAR_LIMIT, len(clean_chunk))
                sub_chunk = clean_chunk[start:end]
                all_chunks.append({"text": sub_chunk, "source": os.path.basename(pdf_path)})
                start += MAX_CHAR_LIMIT - OVERLAP
                
    if not all_chunks:
        print("No valid chunks extracted.")
        return False
        
    # 3. Vectorizing & 4. Upserting
    index = get_pinecone_index()
    batch_size = 64
    
    try:
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            texts = [item['text'] for item in batch]
            
            ids = [hashlib.sha256(t.encode('utf-8')).hexdigest() for t in texts]
            embeddings = embedder.encode(texts).tolist()
            
            records = list(zip(ids, embeddings, batch))
            index.upsert(vectors=records, namespace=category_name)
            
        print(f"Successfully upserted {len(all_chunks)} vectors.")
        return True
    except Exception as e:
        print(f"Error during upsert: {e}")
        return False
    finally:
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Cleaned up temp file {pdf_path}")
            except Exception as e:
                print(f"Could not remove temp file {pdf_path}: {e}")
