db = db.getSiblingDB("think_products");

db.createCollection("products");

db.products.createIndex({ name: 1 });
db.products.createIndex({ status: 1 });
db.products.createIndex({ created_at: -1 });
