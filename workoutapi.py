workoutapi.py
# workoutapi.py
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, selectinload
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional, List
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
import os

# Database configuration
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workoutapi.db")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class CentroTreinamento(Base):
    __tablename__ = "centros_treinamento"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    endereco = Column(String(200))
    proprietario = Column(String(100))
    
    atletas = relationship("Atleta", back_populates="centro_treinamento")

class Categoria(Base):
    __tablename__ = "categorias"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    
    atletas = relationship("Atleta", back_populates="categoria")

class Atleta(Base):
    __tablename__ = "atletas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    idade = Column(Integer, nullable=False)
    peso = Column(Integer, nullable=False)
    altura = Column(Integer, nullable=False)
    sexo = Column(String(1), nullable=False)
    centro_treinamento_id = Column(Integer, ForeignKey("centros_treinamento.id"))
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    
    centro_treinamento = relationship("CentroTreinamento", back_populates="atletas")
    categoria = relationship("Categoria", back_populates="atletas")

# Pydantic Schemas
class CentroTreinamentoBase(BaseModel):
    nome: str
    endereco: Optional[str] = None
    proprietario: Optional[str] = None

class CentroTreinamentoCreate(CentroTreinamentoBase):
    pass

class CentroTreinamentoResponse(CentroTreinamentoBase):
    id: int
    
    class Config:
        orm_mode = True

class CategoriaBase(BaseModel):
    nome: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int
    
    class Config:
        orm_mode = True

class AtletaBase(BaseModel):
    nome: str
    cpf: str
    idade: int
    peso: int
    altura: int
    sexo: str
    centro_treinamento_id: int
    categoria_id: int

class AtletaCreate(AtletaBase):
    pass

class AtletaResponse(AtletaBase):
    id: int
    centro_treinamento: Optional[CentroTreinamentoResponse] = None
    categoria: Optional[CategoriaResponse] = None
    
    class Config:
        orm_mode = True

class AtletaUpdate(BaseModel):
    nome: Optional[str] = None
    idade: Optional[int] = None
    peso: Optional[int] = None
    altura: Optional[int] = None
    sexo: Optional[str] = None
    centro_treinamento_id: Optional[int] = None
    categoria_id: Optional[int] = None

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="WorkoutAPI",
    description="API de competição de crossfit",
    version="1.0.0"
)

# Routers
router = APIRouter()

# Custom exception handler for IntegrityError
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    error_str = str(exc).lower()
    if "cpf" in error_str:
        # Extract CPF from error message if possible
        cpf_start = error_str.find("cpf")
        cpf_value = "unknown"
        if cpf_start != -1:
            # Try to find the CPF value in the error message
            import re
            cpf_match = re.search(r'[\d]{11}', error_str[cpf_start:])
            if cpf_match:
                cpf_value = cpf_match.group(0)
        
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe um atleta cadastrado com o cpf: {cpf_value}"
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Erro de integridade dos dados"
    )

# CentroTreinamento endpoints
@router.get("/centros_treinamento/", response_model=List[CentroTreinamentoResponse])
async def get_centros_treinamento(db: Session = Depends(get_db)):
    return db.query(CentroTreinamento).all()

@router.post("/centros_treinamento/", response_model=CentroTreinamentoResponse, status_code=201)
async def create_centro_treinamento(centro: CentroTreinamentoCreate, db: Session = Depends(get_db)):
    db_centro = CentroTreinamento(**centro.dict())
    db.add(db_centro)
    db.commit()
    db.refresh(db_centro)
    return db_centro

# Categoria endpoints
@router.get("/categorias/", response_model=List[CategoriaResponse])
async def get_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).all()

@router.post("/categorias/", response_model=CategoriaResponse, status_code=201)
async def create_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    db_categoria = Categoria(**categoria.dict())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria

# Atleta endpoints with query parameters and pagination
@router.get("/atletas/", response_model=Page[AtletaResponse])
async def get_atletas(
    db: Session = Depends(get_db),
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    params: Params = Depends()
):
    query = db.query(Atleta).options(
        selectinload(Atleta.centro_treinamento),
        selectinload(Atleta.categoria)
    )
    
    if nome:
        query = query.filter(Atleta.nome.ilike(f"%{nome}%"))
    
    if cpf:
        query = query.filter(Atleta.cpf == cpf)
    
    return paginate(query, params)

@router.get("/atletas/{atleta_id}", response_model=AtletaResponse)
async def get_atleta(atleta_id: int, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).options(
        selectinload(Atleta.centro_treinamento),
        selectinload(Atleta.categoria)
    ).filter(Atleta.id == atleta_id).first()
    
    if not atleta:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    
    return atleta

@router.post("/atletas/", response_model=AtletaResponse, status_code=201)
async def create_atleta(atleta: AtletaCreate, db: Session = Depends(get_db)):
    try:
        db_atleta = Atleta(**atleta.dict())
        db.add(db_atleta)
        db.commit()
        db.refresh(db_atleta)
        
        # Load relationships for response
        db_atleta = db.query(Atleta).options(
            selectinload(Atleta.centro_treinamento),
            selectinload(Atleta.categoria)
        ).filter(Atleta.id == db_atleta.id).first()
        
        return db_atleta
    except IntegrityError as e:
        db.rollback()
        error_str = str(e).lower()
        if "cpf" in error_str:
            # Try to extract CPF value
            cpf_value = atleta.cpf
            raise HTTPException(
                status_code=303,
                detail=f"Já existe um atleta cadastrado com o cpf: {cpf_value}"
            )
        raise HTTPException(
            status_code=400,
            detail="Erro de integridade dos dados"
        )

@router.put("/atletas/{atleta_id}", response_model=AtletaResponse)
async def update_atleta(atleta_id: int, atleta_data: AtletaUpdate, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    
    if not atleta:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    
    try:
        update_data = atleta_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(atleta, field, value)
        
        db.commit()
        db.refresh(atleta)
        
        # Load relationships for response
        atleta = db.query(Atleta).options(
            selectinload(Atleta.centro_treinamento),
            selectinload(Atleta.categoria)
        ).filter(Atleta.id == atleta_id).first()
        
        return atleta
    except IntegrityError as e:
        db.rollback()
        error_str = str(e).lower()
        if "cpf" in error_str:
            # Try to extract CPF value
            cpf_value = atleta.cpf
            raise HTTPException(
                status_code=303,
                detail=f"Já existe um atleta cadastrado com o cpf: {cpf_value}"
            )
        raise HTTPException(
            status_code=400,
            detail="Erro de integridade dos dados"
        )

@router.delete("/atletas/{atleta_id}", status_code=204)
async def delete_atleta(atleta_id: int, db: Session = Depends(get_db)):
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    
    if not atleta:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")
    
    db.delete(atleta)
    db.commit()
    
    return None

# Include routers
app.include_router(router, prefix="/api/v1", tags=["API v1"])

# Add pagination
add_pagination(app)

@app.get("/")
async def root():
    return {"message": "WorkoutAPI - API de competição de crossfit"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)