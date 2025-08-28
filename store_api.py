# store_api.py
from fastapi import FastAPI, APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from contextlib import asynccontextmanager
import pytest
import asyncio

# ===== MODELS/EXCEPTIONS =====
class ProductNotFoundException(Exception):
    """Exceção quando produto não é encontrado"""
    pass

class ProductCreationException(Exception):
    """Exceção quando há erro na criação do produto"""
    pass

class ProductUpdateException(Exception):
    """Exceção quando há erro na atualização do produto"""
    pass

# ===== SCHEMAS =====
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    updated_at: Optional[datetime] = None

class ProductInDB(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductResponse(ProductInDB):
    pass

# ===== DATABASE SETUP =====
MONGODB_URL = "mongodb://localhost:27017"
MONGODB_DB_NAME = "storeapi"

class MongoDB:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    mongodb.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    mongodb.database = mongodb.client[MONGODB_DB_NAME]

async def close_mongo_connection():
    mongodb.client.close()

def get_product_collection():
    return mongodb.database.products

# ===== REPOSITORY =====
class ProductRepository:
    def __init__(self, collection):
        self.collection = collection

    async def create(self, product: ProductCreate) -> ProductInDB:
        try:
            product_data = product.model_dump()
            product_data["created_at"] = datetime.utcnow()
            product_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.insert_one(product_data)
            
            created_product = await self.collection.find_one({"_id": result.inserted_id})
            return self._convert_to_product_in_db(created_product)
        except Exception as e:
            raise ProductCreationException(f"Error creating product: {str(e)}")

    async def get_by_id(self, product_id: str) -> ProductInDB:
        if not ObjectId.is_valid(product_id):
            raise ProductNotFoundException("Invalid product ID")
            
        product = await self.collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise ProductNotFoundException(f"Product with id {product_id} not found")
            
        return self._convert_to_product_in_db(product)

    async def get_all(self, skip: int = 0, limit: int = 10, filters: dict = None) -> List[ProductInDB]:
        query = filters or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        products = await cursor.to_list(length=limit)
        return [self._convert_to_product_in_db(product) for product in products]

    async def update(self, product_id: str, product: ProductUpdate) -> ProductInDB:
        if not ObjectId.is_valid(product_id):
            raise ProductNotFoundException("Invalid product ID")
            
        update_data = product.model_dump(exclude_unset=True)
        
        # Se não foi fornecido updated_at, atualiza com a data atual
        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.utcnow()
            
        result = await self.collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ProductNotFoundException(f"Product with id {product_id} not found")
            
        updated_product = await self.collection.find_one({"_id": ObjectId(product_id)})
        return self._convert_to_product_in_db(updated_product)

    async def delete(self, product_id: str) -> bool:
        if not ObjectId.is_valid(product_id):
            raise ProductNotFoundException("Invalid product ID")
            
        result = await self.collection.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0

    def _convert_to_product_in_db(self, product_data: dict) -> ProductInDB:
        """Converte dados do MongoDB para ProductInDB"""
        product_data["id"] = str(product_data["_id"])
        return ProductInDB(**product_data)

# ===== USECASES =====
class ProductUseCases:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def create_product(self, product: ProductCreate) -> ProductInDB:
        return await self.repository.create(product)

    async def get_product(self, product_id: str) -> ProductInDB:
        return await self.repository.get_by_id(product_id)

    async def list_products(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        min_price: float = None, 
        max_price: float = None
    ) -> List[ProductInDB]:
        filters = {}
        
        # Aplicar filtros de preço conforme o desafio
        if min_price is not None and max_price is not None:
            filters["price"] = {"$gt": min_price, "$lt": max_price}
        elif min_price is not None:
            filters["price"] = {"$gt": min_price}
        elif max_price is not None:
            filters["price"] = {"$lt": max_price}
            
        return await self.repository.get_all(skip, limit, filters)

    async def update_product(self, product_id: str, product: ProductUpdate) -> ProductInDB:
        return await self.repository.update(product_id, product)

    async def delete_product(self, product_id: str) -> bool:
        return await self.repository.delete(product_id)

# ===== CONTROLLER =====
router = APIRouter(prefix="/products", tags=["products"])

def get_product_controller(usecases: ProductUseCases):
    @router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
    async def create_product(product: ProductCreate):
        try:
            return await usecases.create_product(product)
        except ProductCreationException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @router.get("/{product_id}", response_model=ProductResponse)
    async def get_product(product_id: str):
        try:
            return await usecases.get_product(product_id)
        except ProductNotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

    @router.get("/", response_model=List[ProductResponse])
    async def list_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        min_price: float = Query(None, gt=0),
        max_price: float = Query(None, gt=0)
    ):
        return await usecases.list_products(skip, limit, min_price, max_price)

    @router.patch("/{product_id}", response_model=ProductResponse)
    async def update_product(product_id: str, product: ProductUpdate):
        try:
            return await usecases.update_product(product_id, product)
        except ProductNotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

    @router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_product(product_id: str):
        try:
            deleted = await usecases.delete_product(product_id)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {product_id} not found"
                )
        except ProductNotFoundException as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )

    return router

# ===== MAIN APPLICATION =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    
    # Configurar dependências
    product_collection = get_product_collection()
    product_repository = ProductRepository(product_collection)
    product_usecases = ProductUseCases(product_repository)
    
    # Configurar controlador com as dependências
    app.include_router(get_product_controller(product_usecases))
    
    yield
    
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Store API",
    description="API para loja desenvolvida com TDD",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Store API is running"}

# ===== TESTES =====
async def run_tests():
    """Função para executar testes básicos"""
    print("Executando testes...")
    
    # Teste de schemas
    def test_schemas():
        print("Testando schemas...")
        # Teste de criação válida
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "price": 100.0,
            "category": "Test"
        }
        product = ProductCreate(**product_data)
        assert product.name == "Test Product"
        print("✓ Schema de criação válido")
        
        # Teste de atualização parcial
        update_data = {"name": "Updated Name"}
        product_update = ProductUpdate(**update_data)
        assert product_update.name == "Updated Name"
        assert product_update.price is None
        print("✓ Schema de atualização válido")
    
    test_schemas()
    
    # Configurar banco de dados de teste
    test_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    test_db = test_client["test_store_api"]
    await test_db.drop_collection("products")
    test_collection = test_db.products
    
    # Teste de repositório
    async def test_repository():
        print("Testando repositório...")
        repository = ProductRepository(test_collection)
        
        # Teste de criação
        product_data = ProductCreate(
            name="Test Product",
            description="A test product",
            price=100.0,
            category="Test"
        )
        
        created_product = await repository.create(product_data)
        assert created_product.name == "Test Product"
        assert created_product.id is not None
        print("✓ Criação de produto funcionando")
        
        # Teste de busca
        retrieved_product = await repository.get_by_id(created_product.id)
        assert retrieved_product.name == "Test Product"
        assert retrieved_product.id == created_product.id
        print("✓ Busca de produto funcionando")
        
        # Teste de produto não encontrado
        try:
            await repository.get_by_id("nonexistentid")
            assert False, "Deveria ter lançado exceção"
        except ProductNotFoundException:
            print("✓ Tratamento de produto não encontrado funcionando")
    
    await test_repository()
    
    # Teste de usecases
    async def test_usecases():
        print("Testando usecases...")
        repository = ProductRepository(test_collection)
        usecases = ProductUseCases(repository)
        
        # Criar produtos com preços diferentes
        products = [
            ProductCreate(name="Product 1", price=100.0, category="Test"),
            ProductCreate(name="Product 2", price=6000.0, category="Test"),
            ProductCreate(name="Product 3", price=7500.0, category="Test"),
            ProductCreate(name="Product 4", price=9000.0, category="Test"),
        ]
        
        for product in products:
            await usecases.create_product(product)
        
        # Testar filtros de preço
        filtered_products = await usecases.list_products(
            min_price=5000, 
            max_price=8000
        )
        
        assert len(filtered_products) == 2
        assert all(5000 < p.price < 8000 for p in filtered_products)
        print("✓ Filtros de preço funcionando")
    
    await test_usecases()
    
    print("Todos os testes passaram! ✅")
    
    # Limpar banco de teste
    await test_client.drop_database("test_store_api")
    test_client.close()

# ===== EXECUÇÃO =====
if __name__ == "__main__":
    import uvicorn
    
    # Executar testes quando o arquivo é executado diretamente
    async def main():
        try:
            await run_tests()
        except Exception as e:
            print(f"Erro durante os testes: {e}")
            print("Certifique-se de que o MongoDB está rodando na porta 27017")
        
        # Iniciar servidor
        print("\nIniciando servidor na porta 8000...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    
    asyncio.run(main())