from app.tasks.worker import celery_app
from app.services.pdf_service import PDFService
from app.services.ai_service import AIService
from app.services.storage_service import storage_service
from app.services.deduplication_service import DeduplicationService
from app.database import SessionLocal
from app.models import Catalog, Product
from pathlib import Path

@celery_app.task
def process_pdf_task(catalog_id: int, pdf_path: str):
    db = SessionLocal()
    
    try:
        catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
        catalog.status = "processing"
        db.commit()
        
        pdf_service = PDFService(pdf_path)
        ai_service = AIService()
        dedup_service = DeduplicationService(db)
        
        total_pages = pdf_service.get_total_pages()
        catalog.total_pages = total_pages
        db.commit()
        
        for page_num in range(total_pages):
            images = pdf_service.extract_images_bytes(page_num)
            text = pdf_service.extract_text(page_num)
            
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
                    name = product_data.get("name")
                    brand = product_data.get("brand")
                    ean = product_data.get("possible_ean")
                    
                    # Verificar duplicatas (prioriza EAN)
                    duplicate = dedup_service.is_duplicate(name, brand, ean)
                    
                    if duplicate:
                        # ATUALIZAR produto existente
                        updated = False
                        
                        # Atualizar EAN se estava vazio
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
                    else:
                        # CRIAR novo produto
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
            
            catalog.processed_pages = page_num + 1
            db.commit()
        
        pdf_service.close()
        catalog.status = "completed"
        db.commit()
        
    except Exception as e:
        catalog.status = "failed"
        db.commit()
        raise e
    finally:
        db.close()
