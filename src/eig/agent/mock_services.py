"""State-backed mock ERP and CRM services for autonomous enterprise operations."""

import datetime
import uuid
from typing import Dict, Any, Optional
from eig.core.logging import logger


class MockEnterpriseServices:
    """In-memory stateful store simulating external SAP/Salesforce/ServiceNow APIs."""

    def __init__(self):
        # Initial synthetic enterprise ERP state
        self._inventory: Dict[str, Dict[str, Any]] = {
            "SKU-SERVER-RACK-01": {
                "sku": "SKU-SERVER-RACK-01",
                "name": "Datacenter 42U Server Rack",
                "quantity": 14,
                "location": "WH-US-EAST-1",
                "unit_price_usd": 1250.00
            },
            "SKU-GPU-H100-80G": {
                "sku": "SKU-GPU-H100-80G",
                "name": "NVIDIA H100 SXM5 80GB",
                "quantity": 4,
                "location": "WH-US-WEST-2",
                "unit_price_usd": 32000.00
            },
            "SKU-OPTIC-SWITCH-400G": {
                "sku": "SKU-OPTIC-SWITCH-400G",
                "name": "32-Port 400GbE Managed Switch",
                "quantity": 8,
                "location": "WH-EU-CENTRAL-1",
                "unit_price_usd": 8500.00
            }
        }

        # Initial CRM Customers
        self._customers: Dict[str, Dict[str, Any]] = {
            "CUST-ACME-CORP": {
                "customer_id": "CUST-ACME-CORP",
                "name": "Acme Global Aerospace",
                "tier": "PLATINUM",
                "contract_end": "2027-12-31",
                "primary_contact": "alex.vance@acmeglobal.com"
            },
            "CUST-CYBERDYNE": {
                "customer_id": "CUST-CYBERDYNE",
                "name": "Cyberdyne Autonomous Systems",
                "tier": "GOLD",
                "contract_end": "2026-08-15",
                "primary_contact": "m.connor@cyberdyne.org"
            }
        }

        # Initial CRM Leads
        self._leads: Dict[str, Dict[str, Any]] = {
            "LEAD-4891": {
                "lead_id": "LEAD-4891",
                "company": "Nova Quantum Financial",
                "status": "QUALIFIED",
                "deal_value_usd": 250000.00,
                "owner": "sarah.jenkins@enterprise.com",
                "updated_at": "2026-10-20T10:00:00Z"
            },
            "LEAD-9012": {
                "lead_id": "LEAD-9012",
                "company": "Apex BioTech Logistics",
                "status": "CONTACTED",
                "deal_value_usd": 90000.00,
                "owner": "michael.chang@enterprise.com",
                "updated_at": "2026-10-22T14:30:00Z"
            }
        }

        # Support Tickets
        self._tickets: Dict[str, Dict[str, Any]] = {
            "TICK-1001": {
                "ticket_id": "TICK-1001",
                "customer_id": "CUST-ACME-CORP",
                "priority": "HIGH",
                "status": "IN_PROGRESS",
                "description": "Network latency spike on US-EAST cluster",
                "created_at": "2026-10-24T08:00:00Z"
            }
        }

        # Operation Tracking Log (Idempotency and Verification)
        self._operations: Dict[str, Dict[str, Any]] = {}

    def lookup_inventory(self, sku: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Query inventory stock by SKU."""
        item = self._inventory.get(sku.upper())
        if not item:
            return {"found": False, "message": f"SKU {sku} not found in enterprise inventory"}

        if location_id and item.get("location") != location_id:
            return {
                "found": True,
                "sku": sku,
                "quantity_at_location": 0,
                "total_quantity": item["quantity"],
                "location": location_id,
                "notes": f"Item located at {item.get('location')}, not {location_id}"
            }

        return {"found": True, **item}

    def lookup_customer(self, customer_id: str) -> Dict[str, Any]:
        """Query customer details by ID."""
        customer = self._customers.get(customer_id.upper())
        if not customer:
            return {"found": False, "message": f"Customer ID {customer_id} not found in CRM"}
        return {"found": True, **customer}

    def update_lead_status(
        self,
        lead_id: str,
        new_status: str,
        reason: str,
        operation_id: str
    ) -> Dict[str, Any]:
        """Write operation: update lead status with audit record."""
        # Check idempotency
        if operation_id in self._operations:
            logger.info(f"Replaying cached result for idempotent operation {operation_id}")
            return self._operations[operation_id]

        lead = self._leads.get(lead_id.upper())
        if not lead:
            res = {"success": False, "message": f"Lead {lead_id} not found"}
            self._operations[operation_id] = res
            return res

        old_status = lead["status"]
        lead["status"] = new_status
        lead["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        lead["last_update_reason"] = reason

        result = {
            "success": True,
            "operation_id": operation_id,
            "lead_id": lead_id,
            "previous_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "timestamp": lead["updated_at"]
        }
        self._operations[operation_id] = result
        return result

    def create_support_ticket(
        self,
        customer_id: str,
        priority: str,
        description: str,
        operation_id: str
    ) -> Dict[str, Any]:
        """Write operation: file enterprise support ticket."""
        if operation_id in self._operations:
            logger.info(f"Replaying cached ticket for idempotent operation {operation_id}")
            return self._operations[operation_id]

        ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
        ticket_record = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "priority": priority,
            "status": "OPEN",
            "description": description,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self._tickets[ticket_id] = ticket_record

        result = {
            "success": True,
            "operation_id": operation_id,
            "ticket": ticket_record
        }
        self._operations[operation_id] = result
        return result

    def lookup_ticket_status(self, ticket_id: str) -> Dict[str, Any]:
        """Query status of a support ticket."""
        ticket = self._tickets.get(ticket_id.upper())
        if not ticket:
            return {"found": False, "message": f"Ticket {ticket_id} not found"}
        return {"found": True, **ticket}

    def verify_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Verify outcome of a previous operation."""
        if operation_id in self._operations:
            return {
                "operation_id": operation_id,
                "verified": True,
                "status": "EXECUTED",
                "details": self._operations[operation_id]
            }
        return {
            "operation_id": operation_id,
            "verified": False,
            "status": "UNKNOWN_OR_EXPIRED",
            "message": "Operation ID not found in transaction log"
        }


# Global singleton mock services store
mock_enterprise_services = MockEnterpriseServices()
