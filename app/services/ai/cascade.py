import logging
from typing import Optional, Tuple
from app.services.ai.interface import get_llm_backend
from app.models.schemas import InvoiceMetadata, TierUsed

logger = logging.getLogger(__name__)

class CascadeService:
    """
    Orchestrates the fallback logic:
    1. Try Tier 1 (Cheap Text Model)
    2. Check Confidence/Success
    3. Fallback to Tier 2 (Expensive Vision Model) if needed
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        self.backend = get_llm_backend()
        self.confidence_threshold = confidence_threshold

    async def process(
        self, 
        text: str, 
        image_bytes: Optional[bytes] = None
    ) -> Tuple[InvoiceMetadata, TierUsed]:
        """
        Main entry point for invoice extraction.
        Returns the data and which tier was ultimately used.
        """
        
        # --- Tier 1: Text-Only Extraction ---
        logger.info("Attempting Tier 1 (Text-Only) extraction...")
        try:
            result = await self.backend.extract_invoice_data(text=text)
            
            if result.confidence >= self.confidence_threshold:
                logger.info(f"Tier 1 successful with confidence {result.confidence}")
                return result, TierUsed.TIER_1
            
            logger.warning(
                f"Tier 1 confidence low ({result.confidence} < {self.confidence_threshold}). "
                "Escalating to Tier 2..."
            )
        except Exception as e:
            logger.error(f"Tier 1 extraction failed: {str(e)}. Escalating...")

        # --- Tier 2: Vision-Based Fallback ---
        # We only attempt this if image_bytes are provided (e.g., page renders)
        if not image_bytes:
            logger.error("Tier 2 escalation requested but no image data available.")
            # We return the low-confidence Tier 1 result if we can't do Tier 2
            if 'result' in locals():
                return result, TierUsed.TIER_1
            raise ValueError("Extraction failed and no image available for fallback.")

        logger.info("Initiating Tier 2 (Vision) extraction...")
        try:
            vision_result = await self.backend.extract_invoice_data(image_bytes=image_bytes)
            logger.info("Tier 2 extraction completed.")
            return vision_result, TierUsed.TIER_2
            
        except Exception as e:
            logger.error(f"Tier 2 extraction failed: {str(e)}")
            # Final fallback: return the original Tier 1 result if it existed
            if 'result' in locals():
                return result, TierUsed.TIER_1
            raise e