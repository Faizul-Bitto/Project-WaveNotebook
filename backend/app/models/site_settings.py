from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)

    logo_url = Column(String(500), nullable=True, server_default=None)
    favicon_url = Column(String(500), nullable=True, server_default=None)
    site_name = Column(String(255), nullable=True, server_default="WaveNotebook")
    page_title = Column(String(255), nullable=True, server_default=None)

    # Footer & Contact
    site_description = Column(Text, nullable=True, server_default=None)
    contact_phone = Column(String(50), nullable=True, server_default=None)
    contact_email = Column(String(255), nullable=True, server_default=None)
    contact_address = Column(String(500), nullable=True, server_default=None)
    hotline_number = Column(String(50), nullable=True, server_default=None)

    # Social Links
    facebook_url = Column(String(500), nullable=True, server_default=None)
    youtube_url = Column(String(500), nullable=True, server_default=None)
    instagram_url = Column(String(500), nullable=True, server_default=None)
    twitter_url = Column(String(500), nullable=True, server_default=None)
    whatsapp_number = Column(String(50), nullable=True, server_default=None)
    messenger_url = Column(String(500), nullable=True, server_default=None)

    # Order Contact Numbers (Product Detail Page)
    order_whatsapp_number = Column(String(50), nullable=True, server_default=None)
    order_call_number = Column(String(50), nullable=True, server_default=None)

    # Policy Pages
    privacy_policy = Column(Text, nullable=True, server_default=None)
    terms_conditions = Column(Text, nullable=True, server_default=None)
    refund_policy = Column(Text, nullable=True, server_default=None)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
