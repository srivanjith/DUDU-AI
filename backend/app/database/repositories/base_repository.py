from typing import Any, Dict, List, Optional
from bson import ObjectId
from backend.app.database.mongodb import get_db, db_manager


class BaseRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def collection(self):
        return get_db()[self.collection_name]

    def _convert_id(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        d = dict(doc)
        if "_id" in d:
            d["id"] = str(d["_id"])
            del d["_id"]
        return d

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        doc = dict(data)
        if "id" in doc and "_id" not in doc:
            doc["_id"] = ObjectId(doc["id"]) if ObjectId.is_valid(doc["id"]) else doc["id"]
            del doc["id"]
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        if db_manager.is_mock:
            db_manager.persist_fallback_data()
        return self._convert_id(doc)

    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        query = {"_id": ObjectId(doc_id)} if ObjectId.is_valid(doc_id) else {"_id": doc_id}
        doc = self.collection.find_one(query)
        return self._convert_id(doc)

    def find_all(self, filter_query: Optional[Dict[str, Any]] = None, limit: int = 100, skip: int = 0, sort: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        q = filter_query or {}
        cursor = self.collection.find(q).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return [self._convert_id(d) for d in cursor]

    def update(self, doc_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        query = {"_id": ObjectId(doc_id)} if ObjectId.is_valid(doc_id) else {"_id": doc_id}
        self.collection.update_one(query, {"$set": updates})
        if db_manager.is_mock:
            db_manager.persist_fallback_data()
        return self.find_by_id(doc_id)

    def delete(self, doc_id: str) -> bool:
        query = {"_id": ObjectId(doc_id)} if ObjectId.is_valid(doc_id) else {"_id": doc_id}
        result = self.collection.delete_one(query)
        if db_manager.is_mock:
            db_manager.persist_fallback_data()
        return result.deleted_count > 0

    def count(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        return self.collection.count_documents(filter_query or {})

