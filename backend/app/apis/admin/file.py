from fastapi import APIRouter, HTTPException, Path, UploadFile, File as FastAPIFile
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.file import File
from app.models.product import Product
from app.utils.file_upload import upload_file_to_storage, delete_file_from_storage

router = APIRouter(
    prefix="/admin/files",
    tags=["Admin - Files"],
)


@router.post("/{product_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_product_file(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    file: UploadFile = FastAPIFile(...),
):
    """
    Upload file to configured storage provider.
    POST /admin/files/{product_id}/upload
    """

    try:
        # Check product exists
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Upload file using utility
        file_url = await upload_file_to_storage(file, product_id)

        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file."
            )

        # Save to database
        new_file = File(
            product_id=product_id, file_name=file.filename, file_url=file_url
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        logger.info(
            f"✅ File Uploaded | "
            f"Product ID={product_id} | "
            f"File={file.filename} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File uploaded successfully.",
            "file": {
                "id": new_file.id,
                "product_id": new_file.product_id,
                "file_name": new_file.file_name,
                "file_url": new_file.file_url,
                "created_at": new_file.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ File Upload Failed | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file.",
        )


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_files(
    db: db_dependency, admin: admin_dependency, product_id: int = Path(gt=0)
):
    """
    Get all files for a product.
    GET /admin/files/{product_id}
    """

    try:
        # Check product exists
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get all files
        files = db.query(File).filter(File.product_id == product_id).all()

        logger.info(
            f"📁 Product Files Retrieved | "
            f"Product ID={product_id} | "
            f"Count={len(files)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Files retrieved successfully.",
            "product_id": product_id,
            "product_name": product.name,
            "total": len(files),
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
        logger.error(
            f"❌ Error retrieving files | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files.",
        )


@router.get("/single/{file_id}", status_code=status.HTTP_200_OK)
async def get_file_by_id(
    db: db_dependency, admin: admin_dependency, file_id: int = Path(gt=0)
):
    """
    Get single file details.
    GET /admin/files/single/{file_id}
    """

    try:
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        logger.info(f"📁 File Retrieved | ID={file.id} | Admin={admin.phone_number}")

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
        logger.error(
            f"❌ Error retrieving file | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file.",
        )


@router.put("/{file_id}", status_code=status.HTTP_200_OK)
async def update_file(
    db: db_dependency,
    admin: admin_dependency,
    file_id: int = Path(gt=0),
    file: UploadFile = FastAPIFile(...),
):
    """
    Update file (delete old, upload new).
    PUT /admin/files/{file_id}
    """

    try:
        # Get existing file
        existing_file = db.query(File).filter(File.id == file_id).first()

        if not existing_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        product_id = existing_file.product_id
        old_file_url = existing_file.file_url

        # Upload new file
        file_url = await upload_file_to_storage(file, product_id)

        if not file_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to upload new file.",
            )

        # Delete old file from storage
        await delete_file_from_storage(old_file_url)

        # Update database
        existing_file.file_name = file.filename
        existing_file.file_url = file_url

        db.commit()
        db.refresh(existing_file)

        logger.info(
            f"✅ File Updated | "
            f"File ID={file_id} | "
            f"Product ID={product_id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File updated successfully.",
            "file": {
                "id": existing_file.id,
                "product_id": existing_file.product_id,
                "file_name": existing_file.file_name,
                "file_url": existing_file.file_url,
                "created_at": existing_file.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ File Update Failed | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file.",
        )


@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(
    db: db_dependency, admin: admin_dependency, file_id: int = Path(gt=0)
):
    """
    Delete file from storage.
    DELETE /admin/files/{file_id}
    """

    try:
        file = db.query(File).filter(File.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        # Delete from storage
        success = await delete_file_from_storage(file.file_url)

        if not success:
            logger.warning(f"⚠️ File delete from storage failed | URL={file.file_url}")

        file_name = file.file_name
        product_id = file.product_id

        # Delete from database
        db.delete(file)
        db.commit()

        logger.info(
            f"✅ File Deleted | "
            f"Product ID={product_id} | "
            f"File={file_name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File deleted successfully.",
            "deleted_file_id": file_id,
            "deleted_file_name": file_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ File Delete Failed | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file.",
        )
