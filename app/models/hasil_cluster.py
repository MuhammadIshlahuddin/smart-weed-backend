from sqlalchemy import Column, Integer, Float, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.db.session import Base

class HasilCluster(Base):
    __tablename__ = "hasil_cluster"

    id_cluster = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_gulma = Column(Integer, ForeignKey("data_gulma.id_gulma"), nullable=False)
    batch_id = Column(String(50), index=True, nullable=True)
    cluster = Column(Integer, nullable=False)
    centroid_x = Column(Numeric(10, 7), nullable=False)
    centroid_y = Column(Numeric(10, 7), nullable=False)
    jarak = Column(Float, nullable=False)

    data_gulma = relationship("DataGulma", back_populates="hasil_cluster")
    zona_gulma = relationship("ZonaGulma", back_populates="hasil_cluster", uselist=False)
