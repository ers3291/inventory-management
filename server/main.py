from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
import math
import os
import threading
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
# Compress larger JSON responses (/api/orders is ~110 KB raw, ~13 KB gzipped)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Only the frontend may call the API from a browser. A wildcard origin combined with
# allow_credentials makes Starlette echo back *any* Origin, letting any website read the data
# and create purchase orders on a running instance. Override with a comma-separated
# ALLOWED_ORIGINS env var (e.g. for a second dev server on another port).
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # no cookies/auth yet; turn on only together with real authentication
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class Task(BaseModel):
    id: int
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    dueDate: str

# Input limits for user-entered fields (requests are otherwise unbounded)
MAX_SUPPLIER_NAME = 200
MAX_NOTES = 2000
MAX_TASK_TITLE = 200
MAX_PO_QUANTITY = 1_000_000
MAX_PO_UNIT_COST = 1_000_000.0
TASK_PRIORITIES = {"high", "medium", "low"}

# Tasks created through the API live in memory and reset on restart, like purchase orders.
# IDs start at 1000 because the client merges these with built-in mock tasks numbered 1-4
# and decides how to toggle/delete a task by its ID.
tasks: List[dict] = []
TASK_ID_START = 1000
# Monotonic counter (not max(existing)+1) so a deleted task's ID is never handed out again
_next_task_id = TASK_ID_START

# Handlers are sync, so FastAPI runs them in a thread pool: guard check-then-append sequences
# so concurrent requests can't create duplicate purchase orders or reuse an ID.
_write_lock = threading.Lock()

def _parse_iso_date(value: str, field: str) -> date:
    """Parse a YYYY-MM-DD date or raise 400 with a clear message"""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field} must be a date in YYYY-MM-DD format")

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Look up this item's purchase order (at most one per backlog item; see create_purchase_order)
        po = next((po for po in purchase_orders if po["backlog_item_id"] == item["id"]), None)
        item_dict["has_purchase_order"] = po is not None
        # The dashboard switches between "Create PO" and "View PO" on this field
        item_dict["purchase_order_id"] = po["id"] if po else None
        result.append(item_dict)
    return result

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (stored in memory only)"""
    # Validate the body first so an invalid request gets a 400, not a misleading 404/409
    supplier_name = request.supplier_name.strip()
    if not supplier_name:
        raise HTTPException(status_code=400, detail="Supplier name is required")
    if len(supplier_name) > MAX_SUPPLIER_NAME:
        raise HTTPException(status_code=400, detail=f"Supplier name must be at most {MAX_SUPPLIER_NAME} characters")
    if not 0 < request.quantity <= MAX_PO_QUANTITY:
        raise HTTPException(status_code=400, detail=f"Quantity must be between 1 and {MAX_PO_QUANTITY:,}")
    # Python's JSON parser accepts NaN/Infinity, and NaN < 0 is False, so check finiteness explicitly
    if not math.isfinite(request.unit_cost) or request.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Unit cost must be a non-negative number")
    if request.unit_cost > MAX_PO_UNIT_COST:
        raise HTTPException(status_code=400, detail=f"Unit cost must be at most {MAX_PO_UNIT_COST:,.0f}")
    delivery = _parse_iso_date(request.expected_delivery_date, "Expected delivery date")
    if delivery < date.today():
        raise HTTPException(status_code=400, detail="Expected delivery date cannot be in the past")
    notes = request.notes.strip() if request.notes else None
    if notes and len(notes) > MAX_NOTES:
        raise HTTPException(status_code=400, detail=f"Notes must be at most {MAX_NOTES} characters")

    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail="Backlog item not found")

    with _write_lock:
        # One PO per backlog item: the UI shows "View PO" once one exists, so a second is a conflict.
        # The check and the append happen under one lock so concurrent requests can't both pass it.
        if any(po["backlog_item_id"] == request.backlog_item_id for po in purchase_orders):
            raise HTTPException(status_code=409, detail="Purchase order already exists for this backlog item")
        po = {
            # Sequential IDs are safe: POs are never deleted and IDs are assigned under the lock
            "id": f"PO-{len(purchase_orders) + 1:04d}",
            "backlog_item_id": request.backlog_item_id,
            "supplier_name": supplier_name,
            "quantity": request.quantity,
            "unit_cost": request.unit_cost,
            "expected_delivery_date": delivery.isoformat(),
            "status": "Pending",
            "created_date": date.today().isoformat(),
            "notes": notes or None,
        }
        # Appending mutates the list shared with mock_data, so it resets when the server restarts
        purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks created through the API (built-in demo tasks live in the client)"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a task (stored in memory only)"""
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if len(title) > MAX_TASK_TITLE:
        raise HTTPException(status_code=400, detail=f"Title must be at most {MAX_TASK_TITLE} characters")
    priority = request.priority.lower()
    if priority not in TASK_PRIORITIES:
        raise HTTPException(status_code=400, detail="Priority must be high, medium or low")
    due = _parse_iso_date(request.dueDate, "Due date")

    global _next_task_id
    with _write_lock:
        task_id = _next_task_id
        _next_task_id += 1
        task = {"id": task_id, "title": title, "priority": priority, "dueDate": due.isoformat(), "status": "pending"}
        tasks.insert(0, task)  # newest first, matching how the client shows them
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    """Toggle a task between pending and completed"""
    with _write_lock:
        task = next((t for t in tasks if t["id"] == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task["status"] = "completed" if task["status"] == "pending" else "pending"
        return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    with _write_lock:
        index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
        if index is None:
            raise HTTPException(status_code=404, detail="Task not found")
        tasks.pop(index)
    return {"deleted": task_id}

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

def _filtered_report_orders(warehouse: Optional[str], category: Optional[str],
                            status: Optional[str], month: Optional[str]) -> list:
    """Orders matching the global filter bar; shared by the reports endpoints."""
    filtered = apply_filters(orders, warehouse, category, status)
    return filter_by_month(filtered, month)

def _quarter_for(order_date: str) -> Optional[tuple]:
    """Return (year, quarter_number) for an ISO order_date, or None if it can't be parsed.

    Derived from the date itself rather than a hardcoded 2025 lookup, so orders from
    any year land in the right quarter.
    """
    try:
        year = int(order_date[0:4])
        month_num = int(order_date[5:7])
    except (TypeError, ValueError):
        return None
    if not 1 <= month_num <= 12:
        return None
    return year, (month_num - 1) // 3 + 1

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports with optional filtering"""
    quarters = {}

    for order in _filtered_report_orders(warehouse, category, status, month):
        key = _quarter_for(order.get('order_date', ''))
        if key is None:
            continue

        if key not in quarters:
            year, q = key
            quarters[key] = {
                'quarter': f'Q{q}-{year}',
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0,
                'fulfillment_rate': 0
            }

        quarters[key]['total_orders'] += 1
        quarters[key]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[key]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    for data in quarters.values():
        data['total_revenue'] = round(data['total_revenue'], 2)
        data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
        data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)

    # Sort chronologically by (year, quarter); a plain string sort on "Qn-YYYY" would
    # interleave years (Q1-2026 before Q2-2025)
    return [quarters[key] for key in sorted(quarters)]

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends with optional filtering"""
    months = {}

    for order in _filtered_report_orders(warehouse, category, status, month):
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month_key = order_date[:7]  # Gets YYYY-MM

        if month_key not in months:
            months[month_key] = {
                'month': month_key,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month_key]['order_count'] += 1
        months[month_key]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month_key]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    for data in result:
        data['revenue'] = round(data['revenue'], 2)
    result.sort(key=lambda x: x['month'])
    return result

if __name__ == "__main__":
    import uvicorn
    # Loopback by default so the API isn't reachable from other machines on the network
    # (e.g. shared Wi-Fi); set HOST=0.0.0.0 to expose it deliberately.
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8001")))
