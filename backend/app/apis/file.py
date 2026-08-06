from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.file import File
from app.models.product import Product

router = APIRouter(
    prefix="/files",
    tags=["Files"],
)


@router.get("/product/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_files(db: db_dependency, product_id: int = Path(gt=0)):
    """
    Get all files for a product (user can view).
    GET /files/product/{product_id}
    """

    try:
        # Check product exists and is active
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.is_active == True)
            .first()
        )

        if not product:
            logger.warning(f"⚠️ Product Not Found | ID={product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get all files for product
        files = db.query(File).filter(File.product_id == product_id).all()

        logger.info(
            f"📁 Product Files Retrieved | "
            f"Product ID={product_id} | "
            f"Count={len(files)}"
        )

        return {
            "message": "Files retrieved successfully.",
            "product_id": product_id,
            "product_name": product.name,
            "files": [
                {
                    "id": f.id,
                    "file_name": f.file_name,
                    "file_url": f.file_url,
                    "created_at": f.created_at.isoformat(),
                }
                for f in files
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving files | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files.",
        )


@router.get("/{file_id}", status_code=status.HTTP_200_OK)
async def get_file_by_id(db: db_dependency, file_id: int = Path(gt=0)):
    """
    Get single file details.
    GET /files/{file_id}
    """

    try:
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            logger.warning(f"⚠️ File Not Found | ID={file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        # Check if product is active
        product = (
            db.query(Product)
            .filter(Product.id == file.product_id, Product.is_active == True)
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        logger.info(f"📁 File Retrieved | ID={file.id}")

        return {
            "message": "File retrieved successfully.",
            "file": {
                "id": file.id,
                "product_id": file.product_id,
                "file_name": file.file_name,
                "file_url": file.file_url,
                "created_at": file.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving file | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file.",
        )
