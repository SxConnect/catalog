from app.tasks.worker import celery_app
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.storage_service import storage_service
from app.services.catalog_enrichment import CatalogEnrichmentService
from app.services.normalizer import normalize_product_name, normalize_brand, normalize_ean
from app.services.nutrition_parser import nutrition_parser
from app.database import SessionLocal
from app.models import Catalog, Product, Settings
from app.logger import logger, log_catalog_event, log_error
from app.monitoring.metrics import (
    monitor_pdf_extraction, 
    record_product_processed, 
    record_product_duplicate,
    record_catalog_upload,
    record_pdf_size,
    update_queue_size
)
from pathlib import Path
import time
import asyncio
from app.monitoring.metrics import (
    monitor_pdf_extraction, 
    record_product_processed, 
    record_product_duplicate,
    record_catalog_upload,
    record_pdf_size,
    update_queue_size
)
from pathlib import Path
import time

@celery_app.task
@monitor_pdf_extraction
def process_pdf_task(catalog_id: int, pdf_path: str):
    db = SessionLocal()
    start_time = time.time()
    
    try:
        log_catalog_event(catalog_id, f"Starting PDF processing: {pdf_path}")
        
        # Registrar tamanho do arquivo PDF
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            file_size = pdf_file.stat().st_size
            record_pdf_size(file_size)
            log_catalog_event(catalog_id, f"PDF file size: {file_size} bytes")
        
        catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
        if not catalog:
            log_catalog_event(catalog_id, "Catalog not found", "error")
            record_catalog_upload("failed")
            return
        
        catalog.status = "processing"
        db.commit()
        log_catalog_event(catalog_id, "Status changed to processing")
        
        pdf_service = PDFService(pdf_path)
        ai_service = AIService()
        catalog_enrichment = CatalogEnrichmentService()
        
        # Verificar se scraping está habilitado
        scraping_enabled_setting = db.query(Settings).filter(Settings.key == "scraping_enabled").first()
        scraping_enabled = scraping_enabled_setting and scraping_enabled_setting.get_typed_value() if scraping_enabled_setting else False
        
        log_catalog_event(catalog_id, f"Scraping enabled: {scraping_enabled}")
        
        total_pages = pdf_service.get_total_pages()
        catalog.total_pages = total_pages
        db.commit()
        log_catalog_event(catalog_id, f"PDF has {total_pages} pages")
        
        # Lista para acumular produtos do catálogo
        catalog_products = []
        
        for page_num in range(total_pages):
            log_catalog_event(catalog_id, f"Processing page {page_num + 1}/{total_pages}")
            
            images = pdf_service.extract_images_bytes(page_num)
            text = pdf_service.extract_text(page_num)
            
            logger.debug(f"Extracted {len(images)} images and {len(text)} chars from page {page_num}")
            
            # Salvar imagens usando storage service
            image_urls = []
            for img_data in images:
                url = storage_service.save_image(
                    img_data['bytes'],
                    catalog_id,
                    f"page{page_num}_{img_data['index']}.png"
                )
                image_urls.append(url)
            
            if text:
                product_data = ai_service.structure_product_data(text)
                
                if product_data:
                    logger.info(f"AI extracted product: {product_data.get('name')} - {product_data.get('brand')}")
                    
                    # Normalizar dados antes de processar
                    raw_name = product_data.get("name")
                    raw_brand = product_data.get("brand")
                    raw_ean = product_data.get("possible_ean")
                    raw_ingredients = product_data.get("ingredients_text")
                    raw_nutrition = product_data.get("nutritional_text")
                    
                    name = normalize_product_name(raw_name) if raw_name else None
                    brand = normalize_brand(raw_brand) if raw_brand else None
                    ean = normalize_ean(raw_ean) if raw_ean else None
                    
                    # Processar ingredientes e informações nutricionais
                    ingredients = []
                    nutritional_info = {}
                    
                    if raw_ingredients:
                        try:
                            ingredients = nutrition_parser.parse_ingredients(raw_ingredients)
                            logger.info(f"Parsed {len(ingredients)} ingredients for {name}")
                        except Exception as e:
                            logger.warning(f"Failed to parse ingredients for {name}: {e}")
                    
                    if raw_nutrition:
                        try:
                            # Para texto de PDF, usar parsing de texto simples
                            nutritional_info = nutrition_parser._extract_from_text(
                                __import__('bs4').BeautifulSoup(raw_nutrition, 'html.parser')
                            )
                            if nutritional_info:
                                nutritional_info = nutrition_parser._normalize_nutritional_units(nutritional_info)
                                logger.info(f"Parsed {len(nutritional_info)} nutritional values for {name}")
                        except Exception as e:
                            logger.warning(f"Failed to parse nutrition for {name}: {e}")
                    
                    logger.info(f"Normalized product: {name} - {brand} - EAN: {ean}")
                    
                    # Preparar dados do produto para o novo sistema
                    catalog_product = {
                        'name': name,
                        'brand': brand,
                        'ean': ean,
                        'price': product_data.get('price'),
                        'description': product_data.get('description'),
                        'images': image_urls,
                        'attributes': product_data.get('attributes', {}),
                        'ingredients': ingredients if ingredients else None,
                        'nutritional_info': nutritional_info if nutritional_info else None,
                        'source_catalog': catalog.filename,
                        'confidence_score': 0.8
                    }
                    
                    # Adicionar à lista para processamento em lote
                    catalog_products.append(catalog_product)
            
            catalog.processed_pages = page_num + 1
            db.commit()
        
        # Processar todos os produtos do catálogo usando o novo sistema
        if catalog_products:
            log_catalog_event(catalog_id, f"Processing {len(catalog_products)} products with new enrichment system")
            
            # Usar o novo serviço de enriquecimento de catálogo
            enrichment_results = asyncio.run(catalog_enrichment.process_catalog_batch(catalog_products, catalog_id))
            
            # Atualizar estatísticas do catálogo
            catalog.products_found = enrichment_results['total_products']
            
            log_catalog_event(
                catalog_id, 
                f"Enrichment completed: {enrichment_results['new_products']} new, "
                f"{enrichment_results['existing_products']} existing, "
                f"{enrichment_results['errors']} errors"
            )
        
        pdf_service.close()
        catalog.status = "completed"
        db.commit()
        
        duration = time.time() - start_time
        log_catalog_event(
            catalog_id,
            f"Processing completed in {duration:.2f}s - {catalog.products_found} products found"
        )
        
    except Exception as e:
        # Verificar se catalog foi definido antes de tentar acessá-lo
        try:
            if 'catalog' in locals() and catalog:
                catalog.status = "failed"
                db.commit()
        except Exception as commit_error:
            logger.error(f"Error updating catalog status to failed: {commit_error}")
        
        log_error(e, {"catalog_id": catalog_id, "pdf_path": pdf_path})
        log_catalog_event(catalog_id, f"Processing failed: {str(e)}", "error")
        raise e
    finally:
        db.close()
