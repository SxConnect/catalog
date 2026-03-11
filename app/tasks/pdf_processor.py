from app.tasks.worker import celery_app
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.storage_service import storage_service
from app.services.deduplication_service import DeduplicationService
from app.services.web_enrichment import WebEnrichmentService
from app.services.normalizer import normalize_product_name, normalize_brand, normalize_ean
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
        dedup_service = DeduplicationService(db)
        enrichment_service = WebEnrichmentService()
        
        # Verificar se scraping está habilitado
        scraping_enabled_setting = db.query(Settings).filter(Settings.key == "scraping_enabled").first()
        scraping_enabled = scraping_enabled_setting and scraping_enabled_setting.get_typed_value() if scraping_enabled_setting else False
        
        log_catalog_event(catalog_id, f"Scraping enabled: {scraping_enabled}")
        
        total_pages = pdf_service.get_total_pages()
        catalog.total_pages = total_pages
        db.commit()
        log_catalog_event(catalog_id, f"PDF has {total_pages} pages")
        
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
                    
                    name = normalize_product_name(raw_name) if raw_name else None
                    brand = normalize_brand(raw_brand) if raw_brand else None
                    ean = normalize_ean(raw_ean) if raw_ean else None
                    
                    logger.info(f"Normalized product: {name} - {brand} - EAN: {ean}")
                    
                    # Verificar duplicatas (prioriza EAN normalizado)
                    duplicate = dedup_service.is_duplicate(name, brand, ean)
                    
                    if duplicate:
                        # ATUALIZAR produto existente
                        logger.info(f"Duplicate found: {duplicate.id} - {duplicate.name}")
                        updated = False
                        
                        # Atualizar EAN se estava vazio (usando EAN normalizado)
                        if not duplicate.ean and ean:
                            duplicate.ean = ean
                            updated = True
                        
                        # Adicionar novas imagens (sem duplicar)
                        if image_urls:
                            existing_images = set(duplicate.images or [])
                            new_images = set(image_urls)
                            duplicate.images = list(existing_images | new_images)
                            updated = True
                        
                        # Atualizar descrição se estava vazia
                        if not duplicate.description and product_data.get("description"):
                            duplicate.description = product_data.get("description")
                            updated = True
                        
                        # Mesclar atributos
                        new_attrs = product_data.get("attributes", {})
                        if new_attrs:
                            duplicate.attributes = {
                                **(duplicate.attributes or {}),
                                **new_attrs
                            }
                            updated = True
                        
                        # Aumentar confidence se atualizou
                        if updated:
                            duplicate.confidence_score = min(
                                1.0, 
                                (duplicate.confidence_score or 0.8) + 0.05
                            )
                        
                        catalog.products_found = (catalog.products_found or 0)
                        db.commit()
                        log_catalog_event(catalog_id, f"Updated duplicate product: {duplicate.id}")
                    else:
                        # CRIAR novo produto
                        logger.info(f"Creating new product: {name} - {brand}")
                        product = Product(
                            ean=ean,
                            name=name,
                            brand=brand,
                            category=product_data.get("category"),
                            description=product_data.get("description"),
                            images=image_urls,
                            attributes=product_data.get("attributes", {}),
                            source_catalog=catalog.filename,
                            confidence_score=0.8
                        )
                        db.add(product)
                        catalog.products_found = (catalog.products_found or 0) + 1
                        log_catalog_event(catalog_id, f"Created new product: {name}")
                        
                        # Enriquecer produto se habilitado
                        if scraping_enabled:
                            try:
                                log_catalog_event(catalog_id, f"Enriching product: {name}")
                                enriched_data = enrichment_service.search_product_sync(name, brand, ean)
                                
                                if enriched_data:
                                    # Adicionar imagens enriquecidas
                                    if enriched_data.get('additional_images'):
                                        product.images = list(set((product.images or []) + enriched_data['additional_images']))
                                    
                                    # Atualizar descrição se vazia
                                    if not product.description and enriched_data.get('full_description'):
                                        product.description = enriched_data['full_description']
                                    
                                    # Adicionar preço aos atributos
                                    if enriched_data.get('price_avg'):
                                        product.attributes = product.attributes or {}
                                        product.attributes['price_avg'] = enriched_data['price_avg']
                                    
                                    # Adicionar peso aos atributos
                                    if enriched_data.get('weight'):
                                        product.attributes = product.attributes or {}
                                        product.attributes['weight'] = enriched_data['weight']
                                    
                                    log_catalog_event(catalog_id, f"Product enriched successfully: {name}")
                            except Exception as e:
                                log_error(e, {"catalog_id": catalog_id, "product_name": name})
                                logger.warning(f"Enrichment failed for {name}: {e}")
            
            catalog.processed_pages = page_num + 1
            db.commit()
        
        pdf_service.close()
        enrichment_service.close_sync()
        catalog.status = "completed"
        db.commit()
        
        duration = time.time() - start_time
        log_catalog_event(
            catalog_id,
            f"Processing completed in {duration:.2f}s - {catalog.products_found} products found"
        )
        
    except Exception as e:
        catalog.status = "failed"
        db.commit()
        log_error(e, {"catalog_id": catalog_id, "pdf_path": pdf_path})
        log_catalog_event(catalog_id, f"Processing failed: {str(e)}", "error")
        raise e
    finally:
        db.close()
