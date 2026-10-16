from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ZonaGulma(Base):
    __tablename__ = "zona_gulma"

    id_zona = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_cluster = Column(Integer, ForeignKey("hasil_cluster.id_cluster"), nullable=True)
    batch_id = Column(String(50), index=True, nullable=True)
    nama_zona = Column(String(20), nullable=False)  # Rendah, Sedang, Tinggi
    cluster_num = Column(Integer, nullable=True)     # 1, 2, 3
    coverage = Column(Float, nullable=False)         # e.g. 20.44 (%)
    rekomendasi = Column(Text, nullable=False)

    hasil_cluster = relationship("HasilCluster", back_populates="zona_gulma")
