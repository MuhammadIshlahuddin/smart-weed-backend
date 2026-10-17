from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String, Numeric
from sqlalchemy.orm import relationship
from app.db.session import Base

class DataGulma(Base):
    __tablename__ = "data_gulma"

    id_gulma = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_user = Column(Integer, ForeignKey("users.id_user"), nullable=True)
    batch_id = Column(String(50), index=True, nullable=True)
    filename = Column(String(255), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    persentase_gulma = Column(Float, nullable=False)
    tanggal_observasi = Column(Date, nullable=False)

    user = relationship("User", back_populates="data_gulma")
    hasil_cluster = relationship("HasilCluster", back_populates="data_gulma", cascade="all, delete-orphan", uselist=False)
